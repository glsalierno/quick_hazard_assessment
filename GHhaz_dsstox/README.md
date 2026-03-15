# QHA DSSTox – PubChem + EPA CompTox + OPERA

Hazard assessment combining **PubChem**, **EPA CompTox (DSSTox) ToxValDB**, and **OPERA**. Extends [QHA Pro](../QHA_pro/README.md) with EPA CompTox API data.

**See the [main README](../README.md) for a comparison of all versions and their requirements.**

---

## Requirements

| Requirement | Details |
|-------------|---------|
| **Python** | 3.x |
| **Dependencies** | From repo root: `pip install -r requirements.txt` and **`pip install ctx-python`** (CompTox client). |
| **EPA CompTox API key** | **Required.** Stored in a file (e.g. `comptox_api_key.txt`) or in `COMPTOX_API_KEY`; never in code. |
| **OPERA** | **Optional.** If not installed, runs PubChem + CompTox only. |
| **Java** | Only if you use OPERA (JRE/JDK 1.5+ 64-bit). |

---

## Features

| Feature | Description |
|---------|-------------|
| **All QHA Pro features** | GHS, ecotoxicity, exposure bands, provenance, conflicts, SDS export, batch JSON/CSV. |
| **EPA CompTox API** | DTXSID, preferred name, ToxValDB toxicity data. |
| **ToxValDB** | LD50 (with units, species, route), carcinogenicity and genotoxicity record counts. |
| **Merged hazard data** | ToxValDB values merged with PubChem/OPERA (experimental preferred over predicted). |

---

## API Key Required

EPA CompTox requires a free API key. **The API key is never stored in code.**

### Setup

1. **Get an API key**: Email `ccte_api@epa.gov` or visit [EPA CompTox APIs About](https://www.epa.gov/comptox-tools/computational-toxicology-and-exposure-apis-about).

2. **Create the key file** (from this folder):
   ```bash
   cp comptox_api_key.txt.example comptox_api_key.txt
   ```

3. **Edit `comptox_api_key.txt`**: Replace `YOUR_API_KEY_HERE` with your actual key. One line, no quotes:
   ```
   a1b2c3d4-e5f6-7890-abcd-ef1234567890
   ```

4. **Alternative**: Set the `COMPTOX_API_KEY` environment variable instead of using a file.

### Security

- `comptox_api_key.txt` is in `.gitignore` and will not be committed.
- Do not commit your API key. Use the example file as a template only.

---

## Installation

```bash
cd GHhaz
pip install -r requirements.txt
pip install ctx-python
```

---

## Usage

```bash
# Single compound (uses comptox_api_key.txt or COMPTOX_API_KEY)
python QHA_dsstox/haz_assess_dsstox.py 67-64-1

# JSON output
python QHA_dsstox/haz_assess_dsstox.py 67-64-1 -o report.json

# Batch from CSV
python QHA_dsstox/haz_assess_dsstox.py --list compounds.csv -o reports/

# Custom key file location
python QHA_dsstox/haz_assess_dsstox.py 67-64-1 --api-key-file /path/to/comptox_api_key.txt
```

---

## Output

Includes all QHA Pro fields plus:

- **dsstox_dtxsid** – EPA DSSTox substance ID
- **dsstox_ld50** – ToxValDB LD50 (with units, species, route)
- **dsstox_carcinogenicity** – Carcinogenicity record count
- **dsstox_genotoxicity** – Genotoxicity record count
- **dsstox_preferred_name** – Preferred chemical name from CompTox

---

## File Layout

```
QHA_dsstox/
├── haz_assess_dsstox.py         # Main script
├── dsstox_client.py             # CompTox API client (reads key from file/env)
├── hazard_merge.py              # Merge ToxValDB into hazard_data
├── comptox_api_key.txt.example  # Template – copy to comptox_api_key.txt
├── .gitignore                   # Excludes comptox_api_key.txt
└── README.md
```
