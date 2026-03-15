# QHA DSSTox Local – No API Key Required

PubChem + **DSSTox (local mapping file)** + OPERA. Uses a downloaded CAS–DTXSID file instead of the EPA API.

**See the [main README](../README.md) for a comparison of all versions and their requirements.**

---

## Requirements

| Requirement | Details |
|-------------|---------|
| **Python** | 3.x |
| **Dependencies** | Same as parent QHA: `pip install -r requirements.txt` (pandas, openpyxl for Excel). |
| **API key** | **None.** |
| **DSSTox mapping file** | **Required only if you want DSSTox lookup.** Download from EPA (see below). Without it, runs as PubChem + OPERA only (like QHA base). |
| **OPERA** | **Optional.** If not installed, runs PubChem only (and DSSTox lookup if `--dsstox-db` is given). |
| **Java** | Only if you use OPERA (JRE/JDK 1.5+ 64-bit). |

---

## Features

| Feature | Description |
|---------|-------------|
| **All QHA Pro features** | GHS, ecotoxicity, exposure bands, provenance, conflicts, SDS export, batch JSON/CSV. |
| **DTXSID and preferred name** | From a **local** CSV or Excel mapping file (no API). |
| **No ToxValDB in this version** | For ToxValDB LD50/carcinogenicity/genotoxicity, use [QHA DSSTox](../QHA_dsstox/README.md) with an EPA API key. |

---

## No API Key Needed

Download the DSSTox mapping from EPA, point the script at it with `--dsstox-db`, and run. No registration or API key required.

---

## Download DSSTox Mapping

1. Go to [EPA Downloadable Computational Toxicology Data](https://www.epa.gov/comptox-tools/downloadable-computational-toxicology-data).

2. Under **CompTox Chemicals Dashboard**, find the archived data:
   - [CompTox Chemicals Dashboard Archived Data (figshare)](https://figshare.com/projects/NCCT_Chemistry_Dashboard_Data/32198)
   - Or: [CompTox Chemistry Dashboard Content File – DSSTox](https://figshare.com/articles/dataset/The_CompTox_Chemistry_Dashboard_Content_File_DSSTox2015_10_19/4836413) (Excel, ~52 MB)

3. Download the file. Use `.xlsx` directly or export to CSV.

4. The file must have columns for **CAS** (or CASRN) and **DTXSID** (or DSSTox Substance Id). Preferred name is optional but recommended.

---

## Expected File Format

CSV or Excel with at least:

- **CAS / CASRN** – CAS Registry Number
- **DTXSID / DSSTox Substance Id** – DSSTox substance identifier
- **Preferred Name / Substance Name** (optional) – chemical name

Column names are flexible (e.g. `casrn`, `CAS`, `dtxsid`, `DSSTox_Substance_Id`).

---

## Usage

```bash
# With local DSSTox mapping
python QHA_dsstox_local/haz_assess_dsstox_local.py 67-64-1 --dsstox-db dsstox_mapping.csv

# Excel file works too
python QHA_dsstox_local/haz_assess_dsstox_local.py 67-64-1 --dsstox-db DSSToxAll_20151019_v1.xlsx

# Without DSSTox (PubChem + OPERA only, like QHA base)
python QHA_dsstox_local/haz_assess_dsstox_local.py 67-64-1

# Batch
python QHA_dsstox_local/haz_assess_dsstox_local.py --list compounds.csv --dsstox-db dsstox_mapping.csv -o reports/
```

---

## What You Get

- **DTXSID** – EPA DSSTox substance ID (when in mapping file)
- **Preferred name** – from DSSTox when available
- All QHA Pro outputs (GHS, ecotoxicity, exposure bands, conflicts, etc.)
- **No ToxValDB toxicity** in this version. For ToxValDB, use [QHA DSSTox](../QHA_dsstox/README.md) with an API key.

---

## File Layout

```
QHA_dsstox_local/
├── haz_assess_dsstox_local.py   # Main script
├── dsstox_local_client.py       # Local file loader and lookup
└── README.md
```
