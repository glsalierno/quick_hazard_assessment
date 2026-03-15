#!/usr/bin/env python3
"""
Run OPERA from the command line (no GUI) to generate opera_output.csv.

OPERA is a MATLAB-compiled application. Two options:

1) OPERA command-line (CL) installer (recommended for batch)
   - Download OPERA2.9_CL from GitHub releases: https://github.com/kmansouri/OPERA/releases
   - Look for "OPERA2.9_CL_win.zip" (or OPERA2.9_CL_Par for parallel).
   - Install it; the CL executable is separate from the GUI installer.
   - Point this script to the CL .exe, e.g.:
     python run_opera_cli.py --opera-exe "C:\\Program Files\\OPERA2.9_CL\\application\\OPERA.exe"

2) MATLAB (if you have OPERA source and MATLAB)
   - In MATLAB: addpath('path/to/OPERA_Source_code'); OPERA('opera_input.csv','opera_output.csv');
   - Or run the compiled OPERA app from MATLAB with input/output as arguments (see OPERA docs).

If you only have the GUI installer (e.g. OPERA.exe in Program Files), that executable often
does not accept input/output arguments; use the GUI and export, or install OPERA2.9_CL.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

OPERA_TEST_DIR = Path(__file__).resolve().parent


def _find_opera_cli() -> Path | None:
    """
    Suggest possible OPERA CLI exe paths. Prefer non-parallel (OPERA.exe) to avoid
    CDK failure with OPERA_P. Uses portable paths (no user-specific dirs).
    """
    import platform
    system = platform.system()
    candidates = []
    if system == "Windows":
        candidates = [
            Path(r"C:\Program Files\OPERA\application\OPERA.exe"),
            Path(r"C:\Program Files\OPERA\application\OPERA_P.exe"),
            Path(r"C:\Program Files\OPERA2.9_CL\application\OPERA.exe"),
            Path(r"C:\Program Files\OPERA2.9_CL\OPERA.exe"),
            Path(r"C:\Program Files (x86)\OPERA\application\OPERA.exe"),
        ]
    elif system == "Linux":
        candidates = [
            Path("/opt/OPERA/OPERA"),
            Path.home() / "OPERA" / "OPERA",
        ]
    elif system == "Darwin":
        candidates = [
            Path("/Applications/OPERA/OPERA.app/Contents/MacOS/OPERA"),
            Path("/opt/OPERA/OPERA"),
        ]
    for p in candidates:
        if p.exists():
            return p
    return None


def main() -> int:
    p = argparse.ArgumentParser(
        description="Run OPERA on opera_input.csv and write opera_output.csv (requires OPERA CLI)."
    )
    p.add_argument(
        "--opera-exe",
        default=None,
        help="Path to OPERA executable (CL version). If not set, will try common install paths.",
    )
    p.add_argument(
        "--input",
        default=None,
        help="Input CSV with SMILES, CAS (default: opera_input.csv in this folder)",
    )
    p.add_argument(
        "--output",
        default=None,
        help="Output CSV path (default: opera_output.csv in this folder)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print the command that would be run.",
    )
    p.add_argument(
        "--java-home",
        default=None,
        help="Java JDK/JRE home (for PaDEL); prepend bin to PATH. Uses JAVA_HOME env or common paths if not set.",
    )
    args = p.parse_args()

    inp = Path(args.input or OPERA_TEST_DIR / "opera_input.csv")
    out = Path(args.output or OPERA_TEST_DIR / "opera_output.csv")
    exe = args.opera_exe
    if exe:
        exe_path = Path(exe)
    else:
        exe_path = _find_opera_cli()

    if not exe_path or not exe_path.exists():
        print("OPERA executable not found.", file=sys.stderr)
        print("Install the OPERA command-line version (OPERA2.9_CL) from:", file=sys.stderr)
        print("  https://github.com/kmansouri/OPERA/releases", file=sys.stderr)
        print('Then run with: --opera-exe "C:\\Path\\To\\OPERA.exe"', file=sys.stderr)
        return 1

    if not inp.exists():
        print(f"Input file not found: {inp}", file=sys.stderr)
        return 1

    # OPERA 2.9 CLI: -s / --SMI for structure input, -o / --Output for output (see helpP_w.txt).
    # Input must be .sdf/.smi etc.; we have CSV with SMILES,CAS,Name -> convert to .smi (SMILES\tID).
    import csv as csv_module
    smi_path = inp.parent / (inp.stem + ".smi")
    try:
        with open(inp, newline="", encoding="utf-8") as f:
            reader = csv_module.DictReader(f)
            rows = list(reader)
        with open(smi_path, "w", encoding="utf-8", newline="") as f:
            for row in rows:
                smi = (row.get("SMILES") or "").strip()
                if not smi:
                    continue
                cas = (row.get("CAS") or "").strip()
                f.write(f"{smi}\t{cas}\n")
    except Exception as e:
        print(f"Failed to convert CSV to .smi: {e}", file=sys.stderr)
        return 1

    # OPERA 2.9: OPERA -s input.smi -o output.csv [-a] [-v 1]
    cmd = [str(exe_path), "-s", str(smi_path.resolve()), "-o", str(out.resolve()), "-a", "-v", "1"]
    env = os.environ.copy()
    java_home = (args.java_home or os.environ.get("JAVA_HOME", "")).strip()
    if not java_home:
        # Try common Java paths on Windows
        for jpath in [r"C:\Program Files\Java\jdk-17", r"C:\Program Files\Java\jdk-11"]:
            if Path(jpath).exists():
                java_home = jpath
                break
    if java_home:
        java_bin = str(Path(java_home) / "bin")
        if Path(java_bin).exists():
            env["PATH"] = java_bin + os.pathsep + env.get("PATH", "")
    if args.dry_run:
        print("Would run:", " ".join(cmd))
        return 0
    result = subprocess.run(cmd, cwd=str(inp.parent), timeout=600, capture_output=True, text=True, env=env)
    if result.returncode == 0 and out.exists():
        print(f"OPERA finished. Output: {out}")
        return 0
    if result.returncode != 0:
        if result.stderr:
            print("stderr:", result.stderr[:500], file=sys.stderr)
            if "CDK descriptors failed" in result.stderr:
                print('Tip: OPERA_P (parallel) often fails at CDK step. Try non-parallel OPERA.exe', file=sys.stderr)
        if result.stdout:
            print("stdout:", result.stdout[:500], file=sys.stderr)
    print("OPERA did not produce output.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
