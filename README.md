# Quick Hazard Assessment (QHA)

Chemical hazard assessment from **PubChem**, optional **OPERA**, and optional **EPA DSSTox**. This repository contains several versions; choose the one that matches your requirements.

**Repository description** (for GitHub, under 350 characters):
> CLI and Python tools for quick chemical hazard assessment from PubChem, optional OPERA QSAR, and optional EPA DSSTox. GHS H/P phrases, ecotoxicity, exposure bands, provenance, SDS-style export. Four variants: base (PubChem+OPERA), Pro (extended), DSSTox API (ToxValDB), DSSTox local (no API key).

---

## Which version do I use?

| Version | Data sources | API key? | OPERA | Best for |
|--------|---------------|----------|--------|----------|
| **[QHA (base)](#qha-base)** | PubChem + OPERA | **No** | Optional | Simple reports, GHS with phrases, CSV/Excel |
| **[QHA Pro](#qha-pro)** | PubChem + OPERA | **No** | Optional | Ecotoxicity, exposure bands, provenance, SDS export, pipelines |
| **[QHA DSSTox](#qha-dsstox)** | PubChem + **EPA CompTox (API)** + OPERA | **Yes** (EPA) | Optional | ToxValDB LD50, carcinogenicity, genotoxicity, preferred name |
| **[QHA DSSTox Local](#qha-dsstox-local)** | PubChem + **DSSTox (local file)** + OPERA | **No** | Optional | DTXSID + preferred name without an API key |

---

## Requirements summary

| Requirement | QHA (base) | QHA Pro | QHA DSSTox | QHA DSSTox Local |
|-------------|-------|-----------|--------------|--------------------|
| Python 3.x | ✓ | ✓ | ✓ | ✓ |
| pip install -r requirements.txt | ✓ | ✓ (parent) | ✓ + ctx-python | ✓ (parent) |
| EPA CompTox API key | — | — | **Required** (file or env) | — |
| Downloaded DSSTox mapping file | — | — | — | **Required** for DSSTox (optional otherwise) |
| OPERA executable | Optional | Optional | Optional | Optional |
| Java (for OPERA) | If using OPERA | If using OPERA | If using OPERA | If using OPERA |

---

## QHA (base)

**Folder:** `./` (this directory)

**Data sources:** PubChem PUG REST API, optional OPERA QSAR.

**Requirements:**
- Python 3.x
- `pip install -r requirements.txt` (pubchempy, requests, pandas, openpyxl)
- No API key
- OPERA is optional; if missing, runs PubChem only

**Features:**
- GHS hazard (H) and precautionary (P) codes with full phrase legends
- LD50/LC50, flash point, vapor pressure, DTXSID from PubChem
- Optional OPERA predictions (LD50, GHS category, VP, flash point)
- Output: command line, CSV, Excel
- Status column: "PubChem + OPERA" or "PubChem only (OPERA not found)"
- Single or multiple CAS (command line or CSV list, vertical/horizontal)

**Quick start:**
```bash
python cas_hazard_report_pubchem_opera.py 67-64-1
python cas_hazard_report_pubchem_opera.py --list compounds.csv -o reports
```

See [OPERA (optional)](#opera-optional--for-toxicity-predictions) below for OPERA installation.

---

## GHhaz Pro

**Folder:** `GHhaz_pro/`

**Data sources:** Same as GHhaz (PubChem + optional OPERA), plus extended processing.

**Requirements:**
- Same as GHhaz (install parent `requirements.txt`)
- No API key
- OPERA optional; VEGA optional (set `VEGA_API_URL` if used)

**Features:**
- Everything in QHA base, plus:
- **Ecotoxicity:** aquatic LC50, H400–H413, species
- **Route-specific exposure bands:** oral, dermal, inhalation (GHS categories 1–5)
- **Provenance:** every value tagged with source, method (experimental/predicted), confidence
- **Conflict detection:** flags when PubChem and OPERA disagree on GHS
- **Batch API/CLI:** JSON/CSV input and output for pipelines
- **SDS-like export:** structured report (Sections 2, 9, 11, 12)
- **VEGA:** optional QSAR (mutagenicity, carcinogenicity, etc.) if `VEGA_API_URL` is set

**Quick start:**
```bash
python GHhaz_pro/haz_assess_pro.py 67-64-1 -o report.json
python GHhaz_pro/haz_assess_pro.py 67-64-1 --sds -o sds.txt
```

Full details: [GHhaz_pro/README.md](GHhaz_pro/README.md)

---

## QHA DSSTox

**Folder:** `GHhaz_dsstox/`

**Data sources:** PubChem + **EPA CompTox (ToxValDB) via API** + optional OPERA.

**Requirements:**
- Same as QHA Pro
- **EPA CompTox API key required.** Create `comptox_api_key.txt` from `comptox_api_key.txt.example` (see folder README) or set `COMPTOX_API_KEY`.
- OPERA optional

**Features:**
- Everything in QHA Pro, plus:
- **DTXSID** and **preferred name** from EPA CompTox
- **ToxValDB:** LD50 (with units, species, route), carcinogenicity and genotoxicity record counts
- ToxValDB data merged into hazard assessment (experimental preferred over predicted)

**Quick start:**
```bash
# After creating comptox_api_key.txt:
python GHhaz_dsstox/haz_assess_dsstox.py 67-64-1 -o report.json
```

Full details: [GHhaz_dsstox/README.md](GHhaz_dsstox/README.md)

---

## QHA DSSTox Local

**Folder:** `GHhaz_dsstox_local/`

**Data sources:** PubChem + **DSSTox from a local mapping file** (no API) + optional OPERA.

**Requirements:**
- Same as QHA base (parent `requirements.txt`); pandas and openpyxl for Excel support
- **No API key**
- **Downloaded DSSTox mapping file** (CSV or Excel from EPA) if you want DSSTox lookup; otherwise runs as PubChem + OPERA only
- OPERA optional

**Features:**
- Same outputs as QHA Pro
- **DTXSID** and **preferred name** from a user-downloaded CAS–DTXSID mapping file (EPA figshare)
- **No ToxValDB toxicity** in this version (use QHA DSSTox + API key for that)

**Quick start:**
```bash
# With local mapping file (download from EPA first):
python GHhaz_dsstox_local/haz_assess_dsstox_local.py 67-64-1 --dsstox-db dsstox_mapping.csv

# Without DSSTox (PubChem + OPERA only):
python GHhaz_dsstox_local/haz_assess_dsstox_local.py 67-64-1
```

Full details: [GHhaz_dsstox_local/README.md](GHhaz_dsstox_local/README.md)

---

## OPERA (optional – for toxicity predictions)

OPERA provides QSAR predictions (LD50, GHS category, vapor pressure, etc.). **All versions work without OPERA** (PubChem only); OPERA is optional. Folder names (e.g. `GHhaz_pro`) are kept for compatibility; the project name is **Quick Hazard Assessment (QHA)**.

**Version and download:**
- **OPERA v2.9.2** (64-bit)
- [OPERA releases](https://github.com/kmansouri/OPERA/releases)
- Download: **OPERA2.9_CL_win.zip** (command-line; recommended)

**Installation (Windows):**
1. Download and unzip from the releases page.
2. Run the installer (MATLAB runtime if needed).
3. Executable is typically at `C:\Program Files\OPERA2.9_CL\application\OPERA.exe`.
4. **Java:** OPERA needs Java JRE/JDK 1.5+ (64-bit). Set `JAVA_HOME` or `--java-home` if needed.

**Usage:** If installed in a standard location, OPERA is auto-detected. Otherwise use `--opera-exe "C:\Path\To\OPERA.exe"`.

---

## File layout (overview)

```
Quick Hazard Assessment (repo root)/
├── README.md                          # This file – overview of all versions
├── .gitignore                         # Tells Git which files not to track
├── requirements.txt                  # Base dependencies
├── cas_hazard_report_pubchem_opera.py
├── ghs_phrases.py
├── hazard_query_structured.py
├── opera_client.py
├── opera_p2oasys_by_cas.py
├── OPERA_test/
│   └── run_opera_cli.py
├── GHhaz_pro/                        # Extended assessment (ecotoxicity, provenance, SDS)
├── GHhaz_dsstox/                     # + EPA CompTox API (ToxValDB) – API key required
└── GHhaz_dsstox_local/               # + DSSTox from local file – no API key
```

---

## .gitignore

`.gitignore` tells Git which files and folders not to track. The repo includes a root `.gitignore` (and one in `GHhaz_dsstox/` for the API key file) so that build artifacts, virtual envs, API keys, and generated reports are not committed. For more, see [GitHub: Ignoring files](https://docs.github.com/en/get-started/git-basics/ignoring-files).

---

## License

See parent project.
