#!/usr/bin/env python3
"""
Resolve CAS to SMILES (PubChem), run OPERA, and return P2OASys-relevant endpoints.

Uses _find_opera_cli() from run_opera_cli for auto-detection. If OPERA is not found
and --opera-exe is not provided, does NOT fail—returns opera_available: False and
empty p2oasys_endpoints.

Usage:
  python opera_p2oasys_by_cas.py --cas 2462-51-3
  python opera_p2oasys_by_cas.py --list compounds.csv --batch -o results.json
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
OPERA_TEST_DIR = PROJECT_ROOT / "OPERA_test"

# Ensure GHhaz is on path for OPERA_test imports
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _find_opera_cli() -> Path | None:
    """Use run_opera_cli's _find_opera_cli for auto-detection."""
    try:
        from OPERA_test.run_opera_cli import _find_opera_cli as find_opera
        return find_opera()
    except ImportError:
        return None


def resolve_cas_to_smiles_pubchem(cas: str) -> str | None:
    """Get SMILES from PubChem PUG by CAS."""
    try:
        import requests
        base = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
        url = f"{base}/compound/xref/RegistryID/{urllib.parse.quote(cas.strip())}/cids/JSON"
        time.sleep(0.3)
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        cids = r.json().get("IdentifierList", {}).get("CID", [])
        if not cids:
            return None
        cid = int(cids[0])
        url2 = f"{base}/compound/cid/{cid}/property/IsomericSMILES/TXT"
        time.sleep(0.3)
        r2 = requests.get(url2, timeout=30)
        r2.raise_for_status()
        return (r2.text or "").strip() or None
    except Exception:
        return None


def run_opera_cli(
    input_csv: Path,
    output_csv: Path,
    opera_exe: str | None = None,
    java_home: str | None = None,
    timeout: int = 600,
) -> int:
    """Run OPERA via run_opera_cli.py. Returns 0 on success."""
    cli_script = OPERA_TEST_DIR / "run_opera_cli.py"
    if not cli_script.exists():
        return 1
    cmd = [
        sys.executable,
        str(cli_script),
        "--input", str(input_csv),
        "--output", str(output_csv),
    ]
    if opera_exe:
        cmd.extend(["--opera-exe", opera_exe])
    if java_home:
        cmd.extend(["--java-home", java_home])
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), timeout=timeout, capture_output=True, text=True)
    return result.returncode


def p2oasys_endpoints_from_opera_row(row: dict) -> dict:
    """Extract P2OASys-relevant fields from an OPERA CSV row."""
    from opera_client import _parse_opera_row
    return _parse_opera_row(row)


def process_one_cas_pubchem_only(
    cas: str,
    opera_exe: str | None = None,
    java_home: str | None = None,
    out_dir: Path | None = None,
) -> dict:
    """
    PubChem SMILES + OPERA. Returns dict with cas, smiles, p2oasys_endpoints, opera_available, error.
    If OPERA is not found (and --opera-exe not given), returns opera_available: False, empty endpoints.
    """
    out_dir = out_dir or OPERA_TEST_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "cas": cas.strip(),
        "dtxsid": None,
        "preferred_name": cas.strip(),
        "smiles": None,
        "p2oasys_endpoints": {},
        "opera_available": False,
        "error": None,
    }
    smiles = resolve_cas_to_smiles_pubchem(cas)
    if not smiles:
        result["error"] = "No SMILES from PubChem"
        return result
    result["smiles"] = smiles

    # Check OPERA availability before attempting to run
    exe_path = None
    if opera_exe:
        exe_path = Path(opera_exe)
    else:
        exe_path = _find_opera_cli()
    if not exe_path or not exe_path.exists():
        result["opera_available"] = False
        result["p2oasys_endpoints"] = {}
        return result

    input_csv = out_dir / "opera_input_by_cas.csv"
    with open(input_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["SMILES", "CAS", "Name"])
        w.writerow([smiles, cas.strip(), cas.strip()])
    output_csv = out_dir / "opera_output_by_cas.csv"
    ret = run_opera_cli(input_csv, output_csv, opera_exe=str(exe_path) if exe_path else opera_exe, java_home=java_home)
    if ret != 0:
        result["error"] = "OPERA run failed"
        result["opera_available"] = True  # OPERA was found but run failed
        return result
    if not output_csv.exists() or output_csv.stat().st_size == 0:
        result["error"] = "OPERA produced no output"
        result["opera_available"] = True
        return result
    result["opera_available"] = True
    with open(output_csv, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            result["p2oasys_endpoints"] = p2oasys_endpoints_from_opera_row(row)
            break
    return result


def main() -> int:
    p = argparse.ArgumentParser(description="Resolve CAS to SMILES (PubChem), run OPERA, return P2OASys endpoints.")
    p.add_argument("--cas", default=None, help="Single CAS (e.g. 2462-51-3)")
    p.add_argument("--list", default=None, metavar="CSV", help="CSV file with CAS column")
    p.add_argument("--batch", action="store_true", help="One OPERA run for all compounds")
    p.add_argument("-o", "--output", default=None, help="Output JSON or CSV path")
    p.add_argument("--out-dir", default=None, type=Path, help="Directory for OPERA input/output")
    p.add_argument("--opera-exe", default=None, help="Path to OPERA executable")
    p.add_argument("--java-home", default=None, help="Java home for OPERA/PaDEL (uses JAVA_HOME if not set)")
    args = p.parse_args()

    if not args.cas and not args.list:
        p.print_help()
        return 1

    cas_list = []
    if args.cas:
        cas_list.append(args.cas.strip())
    if args.list:
        list_path = Path(args.list)
        if not list_path.exists():
            print(f"File not found: {list_path}", file=sys.stderr)
            return 1
        with open(list_path, newline="", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            cas_col = "CAS" if reader.fieldnames and "CAS" in (reader.fieldnames or []) else (reader.fieldnames[0] if reader.fieldnames else None)
            if not cas_col:
                print("CSV has no CAS column", file=sys.stderr)
                return 1
            for row in reader:
                c = (row.get(cas_col) or "").strip()
                if c and c not in cas_list:
                    cas_list.append(c)

    out_dir = args.out_dir or OPERA_TEST_DIR
    results = []
    for cas in cas_list:
        if not cas:
            continue
        r = process_one_cas_pubchem_only(cas, opera_exe=args.opera_exe, java_home=args.java_home, out_dir=out_dir)
        results.append(r)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.suffix.lower() == ".csv" and results:
            with open(out_path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["cas", "smiles", "opera_available", "error"] + ["ld50_mg_kg", "ghs_h_codes", "vp_mmhg", "flash_point_c"])
                for r in results:
                    ep = r.get("p2oasys_endpoints") or {}
                    w.writerow([
                        r.get("cas"), r.get("smiles"), r.get("opera_available"), r.get("error"),
                        ep.get("ld50_mg_kg"), "|".join(ep.get("ghs_h_codes") or []), ep.get("vp_mmhg"), ep.get("flash_point_c"),
                    ])
        else:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(results if len(results) != 1 else results[0], f, indent=2)
    else:
        print(json.dumps(results if len(results) != 1 else results[0], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
