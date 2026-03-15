#!/usr/bin/env python3
"""
QHA Pro - Extended hazard assessment with:
- Ecotoxicity, route-specific exposure bands
- Provenance tags, confidence, conflict detection
- SDS-like export
- Batch API/CLI (JSON/CSV in/out)
- VEGA integration (optional)

Usage:
  python haz_assess_pro.py 67-64-1
  python haz_assess_pro.py --input compounds.json --output report.json
  python haz_assess_pro.py 67-64-1 --sds -o sds_report.txt
"""

from __future__ import annotations

import csv
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # repo root
QHA_PRO_ROOT = Path(__file__).resolve().parent          # QHA_pro
for p in (PROJECT_ROOT, QHA_PRO_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from hazard_query_structured import get_cid, fetch_structured_hazards
from ghs_phrases import expand_h_codes_with_phrases, expand_p_codes_with_phrases
from opera_client import merge_opera_into_hazard_data

try:
    from .provenance import detect_ghs_conflicts, with_provenance, format_provenance_tag
    from .ecotoxicity import extract_ecotoxicity
    from .exposure_bands import compute_exposure_bands
    from .sds_export import format_sds_report
    from .vega_client import get_vega_predictions, vega_available
except ImportError:
    from provenance import detect_ghs_conflicts, with_provenance, format_provenance_tag
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
        exe = _find_opera_cli()
        return (exe, exe is not None)
    except ImportError:
        return (None, False)


def _load_cas_from_csv(path: Path) -> list[str]:
    cas_seen: set[str] = set()
    cas_order: list[str] = []
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        rows = list(csv.reader(f))
    if not rows:
        return []
    header = rows[0]
    cas_col_names = {"cas", "cas number", "casrn", "cas_no", "casno", "registry id", "registryid"}
    header_lower = [str(h).strip().lower() for h in header]
    cas_col_indices = [
        i for i, h in enumerate(header_lower)
        if h in cas_col_names or "cas" in h or CAS_PATTERN.search(str(header[i] or ""))
    ]
    if not cas_col_indices:
        cas_col_indices = list(range(len(header)))

    def add_cas(c: str) -> None:
        if c and c not in cas_seen:
            cas_seen.add(c)
            cas_order.append(c)

    for row in rows:
        for i in cas_col_indices:
            if i < len(row):
                for c in _parse_cas_string((row[i] or "").strip()):
                    add_cas(c)
    if not cas_order:
        for row in rows:
            for cell in row:
                for c in _parse_cas_string((cell or "").strip()):
                    add_cas(c)
    return cas_order


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


def process_one_cas(
    cas: str,
    opera_exe: str | None = None,
    java_home: str | None = None,
    run_opera: bool = True,
) -> dict:
    """Full pro assessment with provenance, conflicts, ecotoxicity, exposure bands."""
    cas = cas.strip()
    result = {
        "cas": cas,
        "name": cas,
        "status": "PubChem only (OPERA not found)",
        "error": None,
        "pubchem": {},
        "opera": {},
        "provenance": {},
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
    ld50_vals = [t for t in tox if "LD50" in (t.get("value") or "").upper()]
    lc50_vals = [t for t in tox if "LC50" in (t.get("value") or "").upper()]
    # Prefer LD50 with mg/kg
    ld50_best = next((t for t in ld50_vals if "mg" in (t.get("value") or "").lower() and "kg" in (t.get("value") or "").lower()), ld50_vals[0] if ld50_vals else None)
    lc50_best = lc50_vals[0] if lc50_vals else None
    hm = haz.get("hazard_metrics") or {}
    fp = hm.get("flash_point") or []
    vp = hm.get("other_designations") or []

    result["pubchem"] = {
        "cid": cid,
        "dtxsid": haz.get("dtxsid"),
        "ld50": with_provenance(
            ld50_best.get("value", "")[:150] if ld50_best else None,
            "pubchem", "experimental", "high"
        ),
        "lc50": with_provenance(
            lc50_best.get("value", "")[:150] if lc50_best else None,
            "pubchem", "experimental", "medium"
        ),
        "flash_point": fp[0] if fp else None,
        "vapor_pressure": next((x for x in vp if "mm" in str(x).lower() and "hg" in str(x).lower()), None),
    }
    result["physical_properties"] = {
        "flash_point": fp[0] if fp else None,
        "vapor_pressure": next((x for x in vp if "mm" in str(x).lower() and "hg" in str(x).lower()), None),
    }
    result["toxicology"] = {
        "oral_ld50": result["pubchem"]["ld50"],
        "inhalation_lc50": result["pubchem"]["lc50"],
    }

    result["ecotoxicity"] = extract_ecotoxicity(haz)
    opera_ld50 = None

    if run_opera:
        try:
            from opera_p2oasys_by_cas import process_one_cas_pubchem_only
            op = process_one_cas_pubchem_only(cas, opera_exe=opera_exe, java_home=java_home)
            if op.get("opera_available") and op.get("error") is None:
                result["status"] = "PubChem + OPERA"
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
                conflicts = detect_ghs_conflicts(
                    ghs.get("h_codes") or [],
                    ep.get("ghs_h_codes") or [],
                )
                result["conflicts"] = conflicts
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
    """Flatten assessment for CSV export with provenance/conflict columns."""
    row = {
        "CAS": assessment.get("cas"),
        "Name": assessment.get("name"),
        "Status": assessment.get("status"),
        "Error": assessment.get("error") or "",
        "PubChem_CID": assessment.get("pubchem", {}).get("cid"),
        "GHS_H_codes": "|".join(assessment.get("ghs", {}).get("h_codes", [])),
        "GHS_P_codes": "|".join(assessment.get("ghs", {}).get("p_codes", [])),
        "Conflict_count": len(assessment.get("conflicts", [])),
        "Conflicts": "; ".join(c.get("message", "") for c in assessment.get("conflicts", [])),
        "Ecotoxicity_LC50_mg_L": assessment.get("ecotoxicity", {}).get("aquatic_lc50_mg_l"),
        "Oral_exposure_band": assessment.get("exposure_bands", {}).get("oral", {}).get("band"),
        "Dermal_exposure_band": assessment.get("exposure_bands", {}).get("dermal", {}).get("band"),
        "Inhalation_exposure_band": assessment.get("exposure_bands", {}).get("inhalation", {}).get("band"),
    }
    pub = assessment.get("pubchem", {})
    if isinstance(pub.get("ld50"), dict):
        row["LD50_value"] = pub["ld50"].get("value")
        row["LD50_provenance"] = pub["ld50"].get("source", "")
    else:
        row["LD50_value"] = pub.get("ld50")
    op = assessment.get("opera", {})
    row["OPERA_LD50"] = op.get("ld50_mg_kg", {}).get("value") if isinstance(op.get("ld50_mg_kg"), dict) else op.get("ld50_mg_kg")
    return row


def main() -> int:
    import argparse
    p = argparse.ArgumentParser(description="QHA Pro - Extended hazard assessment")
    p.add_argument("cas", nargs="*", default=[], help="CAS number(s)")
    p.add_argument("--input", "-i", default=None, help="Input: JSON array of CAS, or CSV path")
    p.add_argument("--output", "-o", default=None, help="Output: .json, .csv, or directory")
    p.add_argument("--output-format", choices=["json", "csv", "sds"], default=None)
    p.add_argument("--list", metavar="CSV", default=None, help="CSV with CAS column")
    p.add_argument("--sds", action="store_true", help="Export SDS-like report")
    p.add_argument("--no-opera", action="store_true", help="Skip OPERA")
    p.add_argument("--opera-exe", default=None, help="OPERA executable path")
    p.add_argument("--java-home", default=None, help="Java home for OPERA")
    p.add_argument("-q", "--quiet", action="store_true")
    args = p.parse_args()

    cas_list: list[str] = []
    for c in args.cas:
        for cas in _parse_cas_string(c if isinstance(c, str) else ""):
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
            suf = inp.suffix.lower()
            if suf == ".json":
                try:
                    data = json.loads(inp.read_text(encoding="utf-8"))
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        c = item.get("cas") or item.get("CAS") or str(item)
                        for cas in _parse_cas_string(str(c)):
                            if cas not in cas_list:
                                cas_list.append(cas)
                except Exception:
                    pass
            elif suf == ".csv":
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
        r = process_one_cas(
            cas,
            opera_exe=str(exe_path) if exe_path else args.opera_exe,
            java_home=args.java_home,
            run_opera=not args.no_opera,
        )
        results.append(r)
        if not args.quiet and len(cas_list) == 1:
            print(json.dumps(r, indent=2, default=str))

    if args.output:
        out_path = Path(args.output)
        fmt = args.output_format or ("json" if out_path.suffix.lower() == ".json" else "csv" if out_path.suffix.lower() == ".csv" else "json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if args.sds or fmt == "sds":
            sds_path = out_path if out_path.suffix.lower() in (".txt", ".md") else out_path.with_suffix(".txt")
            text = "\n\n".join(format_sds_report(r) for r in results)
            sds_path.write_text(text, encoding="utf-8")
            if not args.quiet:
                print(f"Wrote SDS report: {sds_path}", file=sys.stderr)
        if fmt == "json":
            out_path = out_path if out_path.suffix.lower() == ".json" else out_path.with_suffix(".json")
            out_path.write_text(json.dumps(results if len(results) != 1 else results[0], indent=2, default=str), encoding="utf-8")
            if not args.quiet:
                print(f"Wrote JSON: {out_path}", file=sys.stderr)
        elif fmt == "csv":
            out_path = out_path if out_path.suffix.lower() == ".csv" else out_path.with_suffix(".csv")
            rows = [flatten_for_csv(r) for r in results]
            if rows:
                with open(out_path, "w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), extrasaction="ignore")
                    w.writeheader()
                    w.writerows(rows)
            if not args.quiet:
                print(f"Wrote CSV: {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
