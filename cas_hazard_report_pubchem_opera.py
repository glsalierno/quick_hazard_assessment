#!/usr/bin/env python3
"""
PubChem PUG + OPERA hazard report. GHS H and P codes with full phrase legends.

OPERA auto-detection: uses _find_opera_cli(). If OPERA not found, retrieves from
PubChem only and prints a legend. Status column indicates "PubChem + OPERA" or
"PubChem only (OPERA not found)".

Usage:
  python cas_hazard_report_pubchem_opera.py 67-64-1
  python cas_hazard_report_pubchem_opera.py 67-64-1 50-00-0 67-56-1
  python cas_hazard_report_pubchem_opera.py --list compounds.csv -o reports
  python cas_hazard_report_pubchem_opera.py 67-64-1 --output-format csv -o report.csv
"""

from __future__ import annotations

import csv
import re
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from hazard_query_structured import get_cid, fetch_structured_hazards
from ghs_phrases import expand_h_codes_with_phrases, expand_p_codes_with_phrases
from opera_client import merge_opera_into_hazard_data

OPERA_NOT_FOUND_LEGEND = """
*** OPERA not found. Retrieving hazard data from PubChem only. ***
To enable OPERA: install OPERA2.9_CL from https://github.com/kmansouri/OPERA/releases
and use --opera-exe "C:\\Path\\To\\OPERA.exe"
"""


def _get_opera_exe(opera_exe_arg: str | None) -> tuple[Path | None, bool]:
    """Return (exe_path or None, opera_available)."""
    if opera_exe_arg:
        p = Path(opera_exe_arg)
        return (p, True) if p.exists() else (None, False)
    try:
        from OPERA_test.run_opera_cli import _find_opera_cli
        exe = _find_opera_cli()
        return (exe, exe is not None)
    except ImportError:
        return (None, False)


def _summarize_pubchem(h: dict, with_phrases: bool = True) -> dict:
    """Extract PubChem fields. When with_phrases, expand GHS codes with phrases."""
    out = {"pubchem_cid": h.get("cid"), "pubchem_dtxsid": h.get("dtxsid")}
    ghs = h.get("ghs") or {}
    h_codes = ghs.get("h_codes") or []
    p_codes = ghs.get("p_codes") or []
    if with_phrases:
        out["pubchem_ghs_h"] = expand_h_codes_with_phrases(h_codes)
        out["pubchem_ghs_p"] = expand_p_codes_with_phrases(p_codes)
        out["pubchem_ghs_h_raw"] = "|".join(h_codes)
        out["pubchem_ghs_p_raw"] = "|".join(p_codes)
    else:
        out["pubchem_ghs_h"] = "|".join(h_codes)
        out["pubchem_ghs_p"] = "|".join(p_codes)
    tox = h.get("toxicities") or []
    ld50 = [t for t in tox if "LD50" in (t.get("value") or "").upper()]
    lc50 = [t for t in tox if "LC50" in (t.get("value") or "").upper()]
    out["pubchem_ld50"] = ld50[0].get("value", "")[:120] if ld50 else ""
    out["pubchem_lc50"] = lc50[0].get("value", "")[:120] if lc50 else ""
    hm = h.get("hazard_metrics") or {}
    fp = hm.get("flash_point") or []
    vp = hm.get("other_designations") or []
    out["pubchem_flash_point"] = fp[0] if fp else ""
    out["pubchem_vapor_pressure"] = next((x for x in vp if "mm" in str(x).lower() and "hg" in str(x).lower()), "")
    return out


def _summarize_opera(o: dict, with_phrases: bool = True) -> dict:
    """Extract OPERA fields. When with_phrases, expand GHS H-codes."""
    ep = o.get("p2oasys_endpoints") or o
    h_codes = ep.get("ghs_h_codes") or []
    if with_phrases:
        out = {
            "opera_ld50_mg_kg": ep.get("ld50_mg_kg"),
            "opera_ghs_h": expand_h_codes_with_phrases(h_codes),
            "opera_ghs_h_raw": "|".join(h_codes),
            "opera_vp_mmhg": ep.get("vp_mmhg"),
            "opera_flash_c": ep.get("flash_point_c"),
            "opera_catmos_epa": ep.get("catmos_epa_pred"),
        }
    else:
        out = {
            "opera_ld50_mg_kg": ep.get("ld50_mg_kg"),
            "opera_ghs_h": "|".join(h_codes),
            "opera_vp_mmhg": ep.get("vp_mmhg"),
            "opera_flash_c": ep.get("flash_point_c"),
            "opera_catmos_epa": ep.get("catmos_epa_pred"),
        }
    return out


def process_one_cas(
    cas: str,
    opera_exe: str | None = None,
    java_home: str | None = None,
    run_opera: bool = True,
    with_phrases: bool = True,
) -> dict:
    """
    PubChem PUG + OPERA only. Returns dict with cas, name, raw_pubchem, raw_opera,
    status ("PubChem + OPERA" or "PubChem only (OPERA not found)"), etc.
    """
    cas = cas.strip()
    result = {
        "cas": cas,
        "name": cas,
        "raw_pubchem": {},
        "raw_opera": {},
        "status": "PubChem only (OPERA not found)",
        "error": None,
    }
    cid = get_cid(cas, "cas")
    if not cid:
        result["error"] = "No PubChem CID"
        return result
    haz = fetch_structured_hazards(cid)
    haz["identifier"] = cas
    result["raw_pubchem"] = _summarize_pubchem(haz, with_phrases=with_phrases)
    time.sleep(0.25)

    if run_opera:
        try:
            from opera_p2oasys_by_cas import process_one_cas_pubchem_only
            op = process_one_cas_pubchem_only(cas, opera_exe=opera_exe, java_home=java_home)
            if op.get("opera_available") and op.get("error") is None:
                result["raw_opera"] = _summarize_opera(op, with_phrases=with_phrases)
                result["status"] = "PubChem + OPERA"
                merge_opera_into_hazard_data(haz, op.get("p2oasys_endpoints") or {}, prefer_experimental=False)
            else:
                result["status"] = "PubChem only (OPERA not found)"
        except Exception as e:
            result["raw_opera"] = {"opera_error": str(e)[:100]}
            result["status"] = "PubChem only (OPERA not found)"
    return result


def print_report(r: dict, verbose: bool = True) -> None:
    """Print report with GHS codes and phrases (H and P with full legends)."""
    print("\n" + "=" * 70)
    print(f"CAS: {r['cas']}" + (f"  |  {r.get('name')}" if r.get("name") else ""))
    print(f"Status: {r.get('status', 'N/A')}")
    print("=" * 70)
    print("\n--- PubChem ---")
    for k, v in (r.get("raw_pubchem") or {}).items():
        if v is None or (isinstance(v, str) and not v):
            continue
        if k in ("pubchem_ghs_h", "pubchem_ghs_p") and isinstance(v, list):
            for item in v:
                print(f"  {item}")
        elif k in ("pubchem_ghs_h_raw", "pubchem_ghs_p_raw"):
            continue
        else:
            print(f"  {k}: {v}")
    print("\n--- OPERA ---")
    for k, v in (r.get("raw_opera") or {}).items():
        if v is None or (isinstance(v, str) and not v):
            continue
        if k == "opera_ghs_h" and isinstance(v, list):
            for item in v:
                print(f"  {item}")
        elif k == "opera_ghs_h_raw":
            continue
        else:
            print(f"  {k}: {v}")
    print("\n" + "=" * 70)


def row_for_export(r: dict) -> dict:
    """Flatten for CSV/Excel. GHS with phrases as newline-separated strings."""
    row = {
        "CAS": r["cas"],
        "Name": r.get("name") or "",
        "Status": r.get("status", "PubChem only (OPERA not found)"),
        "Error": r.get("error") or "",
    }
    pub = r.get("raw_pubchem") or {}
    for k, v in pub.items():
        if k in ("pubchem_ghs_h", "pubchem_ghs_p") and isinstance(v, list):
            row[k] = "\n".join(v)
        elif k in ("pubchem_ghs_h_raw", "pubchem_ghs_p_raw"):
            row[k] = v
        elif v is not None:
            row[k] = v
    op = r.get("raw_opera") or {}
    for k, v in op.items():
        if k == "opera_ghs_h" and isinstance(v, list):
            row[k] = "\n".join(v)
        elif k == "opera_ghs_h_raw":
            row[k] = v
        elif v is not None:
            row[k] = v
    return row


CAS_PATTERN = re.compile(r"\d+-\d+-\d+")


def _parse_cas_string(s: str) -> list[str]:
    """Extract CAS numbers from a string (handles comma/pipe/semicolon/space separated)."""
    if not s or not s.strip():
        return []
    cas_list = []
    for sep in [",", "|", ";", "\t"]:
        if sep in s:
            for part in s.split(sep):
                m = CAS_PATTERN.search(part.strip())
                if m:
                    cas_list.append(m.group(0))
            return list(dict.fromkeys(cas_list))
    m = CAS_PATTERN.search(s.strip())
    if m:
        return [m.group(0)]
    return []


def _load_cas_from_csv(path: Path) -> list[str]:
    """
    Load CAS list from CSV. Handles both layouts:
    - Vertical: one CAS per row in a column (CAS, CAS Number, etc.)
    - Horizontal: one row with CAS in multiple columns
    - Mixed: cells may contain multiple CAS (comma/pipe separated)
    """
    cas_seen: set[str] = set()
    cas_order: list[str] = []
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        return []
    header = rows[0]
    cas_col_names = {"cas", "cas number", "casrn", "cas_no", "casno", "registry id", "registryid"}
    header_lower = [str(h).strip().lower() for h in header]
    # Include columns named CAS/CAS1/CAS2, or whose header contains a CAS number
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


def _sanitize_sheet_name(cas: str) -> str:
    s = re.sub(r'[\[\]:*?/\\]', "_", str(cas))[:31]
    return s or "Sheet"


def _output_filename_from_cas(cas_list: list[str], base_dir: Path, fmt: str = "xlsx") -> Path:
    def safe(s: str) -> str:
        return re.sub(r'[^\w\-]', "_", s)[:20]
    if len(cas_list) == 1:
        name = f"hazard_report_pubchem_opera_{safe(cas_list[0])}.{fmt}"
    elif len(cas_list) <= 3:
        parts = [safe(c) for c in cas_list[:3]]
        name = f"hazard_report_pubchem_opera_{'_'.join(parts)}.{fmt}"
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        name = f"hazard_report_pubchem_opera_{len(cas_list)}compounds_{ts}.{fmt}"
    return base_dir / name


def write_csv(results: list[dict], out_path: Path) -> None:
    """Write results to CSV with all GHS phrase columns."""
    if not results:
        return
    rows = [row_for_export(r) for r in results]
    all_keys = set()
    for row in rows:
        all_keys.update(row.keys())
    fieldnames = ["CAS", "Name", "Status", "Error"] + sorted(k for k in all_keys if k not in ("CAS", "Name", "Status", "Error"))
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def write_excel_sheets(results: list[dict], out_path: Path) -> None:
    import pandas as pd
    seen_sheets = set()
    with pd.ExcelWriter(out_path, engine="openpyxl") as wr:
        summary_rows = [row_for_export(r) for r in results]
        if summary_rows:
            all_keys = set()
            for row in summary_rows:
                all_keys.update(row.keys())
            fieldnames = ["CAS", "Name", "Status", "Error"] + sorted(k for k in all_keys if k not in ("CAS", "Name", "Status", "Error"))
            df_summary = pd.DataFrame(summary_rows, columns=fieldnames)
            df_summary.to_excel(wr, sheet_name="Summary", index=False)
        for r in results:
            cas = r.get("cas", "unknown")
            sheet_name = _sanitize_sheet_name(cas)
            if sheet_name in seen_sheets:
                sheet_name = _sanitize_sheet_name(f"{cas}_{id(r)}")
            seen_sheets.add(sheet_name)
            row = row_for_export(r)
            df = pd.DataFrame([row])
            df.to_excel(wr, sheet_name=sheet_name, index=False)


def main() -> int:
    import argparse
    p = argparse.ArgumentParser(description="PubChem PUG + OPERA, GHS H/P codes with phrases")
    p.add_argument("cas", nargs="*", default=[], help="One or more CAS numbers (e.g. 67-64-1 50-00-0)")
    p.add_argument("--list", metavar="CSV", default=None, help="Batch: CSV with CAS (vertical or horizontal layout)")
    p.add_argument("-o", "--output", default=None, help="Output path (dir, .xlsx, or .csv)")
    p.add_argument("--output-format", choices=["csv", "xlsx", "both"], default=None,
                   help="Force output format: csv, xlsx, or both. Uses -o extension if not set.")
    p.add_argument("--no-opera", action="store_true", help="Skip OPERA")
    p.add_argument("--opera-exe", default=None, help="OPERA executable path")
    p.add_argument("--java-home", default=None, help="Java home for OPERA (uses JAVA_HOME if not set)")
    p.add_argument("-q", "--quiet", action="store_true", help="Minimal output")
    args = p.parse_args()

    cas_list: list[str] = []
    for c in args.cas:
        parsed = _parse_cas_string(c) if isinstance(c, str) else []
        if parsed:
            for cas in parsed:
                if cas not in cas_list:
                    cas_list.append(cas)
    if args.list:
        path = Path(args.list)
        if not path.exists():
            print(f"File not found: {path}", file=sys.stderr)
            return 1
        from_csv = _load_cas_from_csv(path)
        for c in from_csv:
            if c not in cas_list:
                cas_list.append(c)

    if not cas_list:
        p.print_help()
        print("\nExample: python cas_hazard_report_pubchem_opera.py 67-64-1", file=sys.stderr)
        return 1

    # Check OPERA availability and print legend if not found
    exe_path, opera_available = _get_opera_exe(args.opera_exe)
    if not opera_available and not args.no_opera:
        print(OPERA_NOT_FOUND_LEGEND, file=sys.stderr)

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
            print_report(r)
        elif not args.quiet and len(cas_list) > 1:
            print(f"  -> Status: {r.get('status')}", file=sys.stderr)

    if args.output:
        out_arg = Path(args.output)
        output_format = args.output_format
        if output_format is None and out_arg.suffix:
            output_format = "csv" if out_arg.suffix.lower() == ".csv" else "xlsx"

        if out_arg.suffix.lower() in (".xlsx", ".xls", ".csv"):
            out_path = out_arg
            out_dir = out_arg.parent
        else:
            out_dir = out_arg
            out_dir.mkdir(parents=True, exist_ok=True)
            fmt = "csv" if output_format == "csv" else "xlsx"
            out_path = _output_filename_from_cas(cas_list, out_dir, fmt=fmt)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if output_format == "csv" or (output_format is None and out_path.suffix.lower() == ".csv"):
            write_csv(results, out_path)
            print(f"Wrote CSV: {out_path}", file=sys.stderr)
        elif output_format == "xlsx" or (output_format is None and out_path.suffix.lower() in (".xlsx", ".xls")):
            write_excel_sheets(results, out_path)
            print(f"Wrote Excel: {out_path}", file=sys.stderr)
        elif output_format == "both":
            out_dir = out_path.parent
            csv_path = _output_filename_from_cas(cas_list, out_dir, "csv")
            xlsx_path = _output_filename_from_cas(cas_list, out_dir, "xlsx")
            write_csv(results, csv_path)
            write_excel_sheets(results, xlsx_path)
            print(f"Wrote CSV: {csv_path}", file=sys.stderr)
            print(f"Wrote Excel: {xlsx_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
