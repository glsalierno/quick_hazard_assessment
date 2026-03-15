#!/usr/bin/env python3
"""
QHA DSSTox Local - PubChem + DSSTox (local DB) + OPERA. No API key required.

Uses a downloaded DSSTox mapping file for CAS→DTXSID and preferred name lookup.
Download from EPA: https://www.epa.gov/comptox-tools/downloadable-computational-toxicology-data

Usage:
  python haz_assess_dsstox_local.py 67-64-1 --dsstox-db dsstox_mapping.csv
  python haz_assess_dsstox_local.py --list compounds.csv --dsstox-db dsstox_mapping.csv -o reports/
"""

from __future__ import annotations

import csv
import json
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
QHA_PRO = REPO_ROOT / "QHA_pro"
for p in (REPO_ROOT, QHA_PRO):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from hazard_query_structured import get_cid, fetch_structured_hazards
from ghs_phrases import expand_h_codes_with_phrases, expand_p_codes_with_phrases
from opera_client import merge_opera_into_hazard_data

from dsstox_local_client import DSSToxLocalDB

try:
    from provenance import detect_ghs_conflicts, with_provenance
    from ecotoxicity import extract_ecotoxicity
    from exposure_bands import compute_exposure_bands
    from sds_export import format_sds_report
    from vega_client import get_vega_predictions, vega_available
except ImportError:
    sys.path.insert(0, str(QHA_PRO))
    from provenance import detect_ghs_conflicts, with_provenance
    from ecotoxicity import extract_ecotoxicity
    from exposure_bands import compute_exposure_bands
    from sds_export import format_sds_report
    from vega_client import get_vega_predictions, vega_available

CAS_PATTERN = re.compile(r"\d+-\d+-\d+")


def _get_opera_exe(opera_exe_arg: str | None) -> tuple[Path | None, bool]:
    if opera_exe_arg:
        p = Path(opera_exe_arg)
        return (p, True) if p.exists() else (None, False)
    try:
        from OPERA_test.run_opera_cli import _find_opera_cli
        return (_find_opera_cli(), True)
    except ImportError:
        return (None, False)


def _parse_cas_string(s: str) -> list[str]:
    if not s or not s.strip():
        return []
    for sep in [",", "|", ";", "\t"]:
        if sep in s:
            return list(dict.fromkeys(
                m.group(0) for part in s.split(sep)
                for m in [CAS_PATTERN.search(part.strip())] if m
            ))
    m = CAS_PATTERN.search(s.strip())
    return [m.group(0)] if m else []


def _load_cas_from_csv(path: Path) -> list[str]:
    cas_seen: set[str] = set()
    cas_order: list[str] = []
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        rows = list(csv.reader(f))
    if not rows:
        return []
    header = rows[0]
    header_lower = [str(h).strip().lower() for h in header]
    cas_col_indices = [i for i, h in enumerate(header_lower) if "cas" in h or CAS_PATTERN.search(str(header[i] or ""))]
    if not cas_col_indices:
        cas_col_indices = list(range(len(header)))
    for row in rows:
        for i in cas_col_indices:
            if i < len(row):
                for c in _parse_cas_string((row[i] or "").strip()):
                    if c and c not in cas_seen:
                        cas_seen.add(c)
                        cas_order.append(c)
    if not cas_order:
        for row in rows:
            for cell in row:
                for c in _parse_cas_string((cell or "").strip()):
                    if c and c not in cas_seen:
                        cas_seen.add(c)
                        cas_order.append(c)
    return cas_order


def _summarize_dsstox_local(lookup: dict | None) -> dict:
    """Format local DSSTox lookup result."""
    if not lookup:
        return {"dsstox_dtxsid": None, "dsstox_error": None, "dsstox_preferred_name": None, "dsstox_source": "local"}
    return {
        "dsstox_dtxsid": lookup.get("dtxsid"),
        "dsstox_error": None,
        "dsstox_preferred_name": lookup.get("preferred_name"),
        "dsstox_source": "local",
    }


def process_one_cas(
    cas: str,
    dsstox_db: DSSToxLocalDB | None,
    opera_exe: str | None = None,
    java_home: str | None = None,
    run_opera: bool = True,
) -> dict:
    """Full assessment: PubChem + DSSTox (local) + OPERA."""
    cas = cas.strip()
    result = {
        "cas": cas,
        "name": cas,
        "status": "PubChem",
        "error": None,
        "pubchem": {},
        "dsstox": {},
        "opera": {},
        "conflicts": [],
        "ecotoxicity": {},
        "exposure_bands": {},
        "vega": None,
    }
    cid = get_cid(cas, "cas")
    if not cid:
        result["error"] = "No PubChem CID"
        return result
    haz = fetch_structured_hazards(cid)
    haz["identifier"] = cas
    time.sleep(0.25)

    ghs = haz.get("ghs") or {}
    result["ghs"] = {
        "h_codes": ghs.get("h_codes", []),
        "p_codes": ghs.get("p_codes", []),
        "h_codes_with_phrases": expand_h_codes_with_phrases(ghs.get("h_codes") or []),
        "p_codes_with_phrases": expand_p_codes_with_phrases(ghs.get("p_codes") or []),
    }
    tox = haz.get("toxicities") or []
    ld50_best = next((t for t in tox if "LD50" in (t.get("value") or "").upper() and "mg" in (t.get("value") or "").lower() and "kg" in (t.get("value") or "").lower()), tox[0] if any("LD50" in (t.get("value") or "").upper() for t in tox) else None)
    lc50_best = next((t for t in tox if "LC50" in (t.get("value") or "").upper()), None)
    hm = haz.get("hazard_metrics") or {}
    fp = hm.get("flash_point") or []
    vp = hm.get("other_designations") or []

    result["pubchem"] = {
        "cid": cid,
        "dtxsid": haz.get("dtxsid"),
        "ld50": with_provenance(ld50_best.get("value", "")[:150] if ld50_best else None, "pubchem", "experimental", "high"),
        "lc50": with_provenance(lc50_best.get("value", "")[:150] if lc50_best else None, "pubchem", "experimental", "medium"),
        "flash_point": fp[0] if fp else None,
        "vapor_pressure": next((x for x in vp if "mm" in str(x).lower() and "hg" in str(x).lower()), None),
    }
    result["physical_properties"] = {"flash_point": fp[0] if fp else None, "vapor_pressure": next((x for x in vp if "mm" in str(x).lower() and "hg" in str(x).lower()), None)}
    result["toxicology"] = {"oral_ld50": result["pubchem"]["ld50"], "inhalation_lc50": result["pubchem"]["lc50"]}
    result["ecotoxicity"] = extract_ecotoxicity(haz)
    opera_ld50 = None

    # DSSTox (local - no API)
    if dsstox_db:
        lookup = dsstox_db.lookup(cas)
        result["dsstox"] = _summarize_dsstox_local(lookup)
        if lookup:
            result["status"] = "PubChem + DSSTox (local)"
            if lookup.get("preferred_name"):
                result["name"] = lookup["preferred_name"]
            if haz.get("dtxsid") is None and lookup.get("dtxsid"):
                haz["dtxsid"] = lookup["dtxsid"]

    if run_opera:
        try:
            from opera_p2oasys_by_cas import process_one_cas_pubchem_only
            op = process_one_cas_pubchem_only(cas, opera_exe=opera_exe, java_home=java_home)
            if op.get("opera_available") and op.get("error") is None:
                result["status"] = result["status"] + " + OPERA"
                ep = op.get("p2oasys_endpoints") or {}
                opera_ld50 = ep.get("ld50_mg_kg")
                result["opera"] = {
                    "ld50_mg_kg": with_provenance(opera_ld50, "opera", "predicted", "medium"),
                    "ghs_h_codes": ep.get("ghs_h_codes") or [],
                    "ghs_h_with_phrases": expand_h_codes_with_phrases(ep.get("ghs_h_codes") or []),
                    "vp_mmhg": ep.get("vp_mmhg"),
                    "flash_point_c": ep.get("flash_point_c"),
                }
                merge_opera_into_hazard_data(haz, ep, prefer_experimental=False)
                result["conflicts"] = detect_ghs_conflicts(ghs.get("h_codes") or [], ep.get("ghs_h_codes") or [])
        except Exception as e:
            result["opera"] = {"error": str(e)[:100]}

    result["exposure_bands"] = compute_exposure_bands(haz, opera_ld50=opera_ld50)

    if vega_available():
        try:
            import pubchempy as pcp
            c = pcp.Compound.from_cid(cid)
            smiles = getattr(c, "isomeric_smiles", None) or getattr(c, "canonical_smiles", None)
            if smiles:
                result["vega"] = get_vega_predictions(smiles)
        except Exception:
            pass
    return result


def flatten_for_csv(assessment: dict) -> dict:
    row = {
        "CAS": assessment.get("cas"),
        "Name": assessment.get("name"),
        "Status": assessment.get("status"),
        "Error": assessment.get("error") or "",
        "PubChem_CID": assessment.get("pubchem", {}).get("cid"),
        "DSSTox_DTXSID": assessment.get("dsstox", {}).get("dsstox_dtxsid"),
        "DSSTox_preferred_name": assessment.get("dsstox", {}).get("dsstox_preferred_name"),
        "GHS_H_codes": "|".join(assessment.get("ghs", {}).get("h_codes", [])),
        "GHS_P_codes": "|".join(assessment.get("ghs", {}).get("p_codes", [])),
        "Conflict_count": len(assessment.get("conflicts", [])),
        "Ecotoxicity_LC50_mg_L": assessment.get("ecotoxicity", {}).get("aquatic_lc50_mg_l"),
        "Oral_exposure_band": assessment.get("exposure_bands", {}).get("oral", {}).get("band"),
    }
    pub = assessment.get("pubchem", {})
    row["LD50_value"] = pub.get("ld50", {}).get("value") if isinstance(pub.get("ld50"), dict) else pub.get("ld50")
    row["OPERA_LD50"] = assessment.get("opera", {}).get("ld50_mg_kg", {}).get("value") if isinstance(assessment.get("opera", {}).get("ld50_mg_kg"), dict) else assessment.get("opera", {}).get("ld50_mg_kg")
    return row


def main() -> int:
    import argparse
    p = argparse.ArgumentParser(description="QHA DSSTox Local - PubChem + DSSTox (local) + OPERA, no API key")
    p.add_argument("cas", nargs="*", default=[], help="CAS number(s)")
    p.add_argument("--input", "-i", default=None, help="Input JSON or CSV")
    p.add_argument("--output", "-o", default=None, help="Output path")
    p.add_argument("--output-format", choices=["json", "csv", "sds"], default=None)
    p.add_argument("--list", metavar="CSV", default=None, help="CSV with CAS column")
    p.add_argument("--dsstox-db", metavar="PATH", default=None, help="Path to DSSTox mapping file (CSV or Excel)")
    p.add_argument("--sds", action="store_true", help="Export SDS-like report")
    p.add_argument("--no-opera", action="store_true", help="Skip OPERA")
    p.add_argument("--opera-exe", default=None, help="OPERA executable path")
    p.add_argument("--java-home", default=None, help="Java home for OPERA")
    p.add_argument("-q", "--quiet", action="store_true")
    args = p.parse_args()

    dsstox_db: DSSToxLocalDB | None = None
    if args.dsstox_db:
        path = Path(args.dsstox_db)
        if path.exists():
            dsstox_db = DSSToxLocalDB()
            if dsstox_db.load(path):
                if not args.quiet:
                    print(f"Loaded DSSTox mapping from {path}", file=sys.stderr)
            else:
                print(f"Could not load DSSTox DB from {path}. Check file format (CSV/Excel with CAS, DTXSID columns).", file=sys.stderr)
                dsstox_db = None
        else:
            print(f"DSSTox DB file not found: {path}", file=sys.stderr)
    elif not args.quiet:
        print("No --dsstox-db specified. DSSTox lookup disabled (PubChem + OPERA only).", file=sys.stderr)

    cas_list: list[str] = []
    for c in args.cas:
        for cas in _parse_cas_string(str(c)):
            if cas not in cas_list:
                cas_list.append(cas)
    if args.list:
        path = Path(args.list)
        if path.exists():
            for c in _load_cas_from_csv(path):
                if c not in cas_list:
                    cas_list.append(c)
    if args.input:
        inp = Path(args.input)
        if inp.exists():
            if inp.suffix.lower() == ".json":
                try:
                    data = json.loads(inp.read_text(encoding="utf-8"))
                    for item in (data if isinstance(data, list) else [data]):
                        for cas in _parse_cas_string(str(item.get("cas") or item.get("CAS") or item)):
                            if cas not in cas_list:
                                cas_list.append(cas)
                except Exception:
                    pass
            elif inp.suffix.lower() == ".csv":
                for c in _load_cas_from_csv(inp):
                    if c not in cas_list:
                        cas_list.append(c)

    if not cas_list:
        p.print_help()
        return 1

    exe_path, _ = _get_opera_exe(args.opera_exe)
    results = []
    for i, cas in enumerate(cas_list):
        if not args.quiet and len(cas_list) > 1:
            print(f"[{i+1}/{len(cas_list)}] {cas}...", file=sys.stderr)
        r = process_one_cas(cas, dsstox_db=dsstox_db, opera_exe=str(exe_path) if exe_path else args.opera_exe, java_home=args.java_home, run_opera=not args.no_opera)
        results.append(r)
        if not args.quiet and len(cas_list) == 1:
            print(json.dumps(r, indent=2, default=str))

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        fmt = args.output_format or ("json" if out.suffix.lower() == ".json" else "csv" if out.suffix.lower() == ".csv" else "json")
        if args.sds or fmt == "sds":
            text = "\n\n".join(format_sds_report(r) for r in results)
            p = out if out.suffix.lower() in (".txt", ".md") else out.with_suffix(".txt")
            p.write_text(text, encoding="utf-8")
            if not args.quiet:
                print(f"Wrote: {p}", file=sys.stderr)
        if fmt == "json":
            p = out if out.suffix.lower() == ".json" else out.with_suffix(".json")
            p.write_text(json.dumps(results if len(results) != 1 else results[0], indent=2, default=str), encoding="utf-8")
            if not args.quiet:
                print(f"Wrote: {p}", file=sys.stderr)
        elif fmt == "csv":
            p = out if out.suffix.lower() == ".csv" else out.with_suffix(".csv")
            rows = [flatten_for_csv(r) for r in results]
            if rows:
                with open(p, "w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), extrasaction="ignore")
                    w.writeheader()
                    w.writerows(rows)
            if not args.quiet:
                print(f"Wrote: {p}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
