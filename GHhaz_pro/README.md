# QHA Pro – Extended Hazard Assessment

QHA Pro extends [Quick Hazard Assessment](../README.md) (QHA base) with professional hazard assessment features for pipelines and structured reporting.

**See the [main README](../README.md) for a comparison of all versions (QHA base, QHA Pro, QHA DSSTox, QHA DSSTox Local) and their requirements.**

---

## Requirements

| Requirement | Details |
|-------------|---------|
| **Python** | 3.x |
| **Dependencies** | Same as parent QHA. From repo root: `pip install -r requirements.txt` (no extra packages). |
| **API key** | **None** |
| **OPERA** | **Optional.** If not installed, runs PubChem only. |
| **Java** | Only if you use OPERA (JRE/JDK 1.5+ 64-bit). |
| **VEGA** | **Optional.** For QSAR predictions set `VEGA_API_URL`; otherwise VEGA is skipped. |

---

## Features

| Feature | Description |
|---------|-------------|
| **All QHA base features** | GHS H/P with phrases, PubChem PUG, optional OPERA, CSV/Excel, batch from CSV. |
| **Ecotoxicity** | Aquatic LC50, H-codes (H400–H413), species. |
| **Route-specific exposure bands** | Oral, dermal, inhalation categories (GHS 1–5). |
| **Batch API / CLI** | JSON/CSV input and output for pipelines. |
| **Data provenance** | Source, method (experimental/predicted), confidence on every value. |
| **Conflict detection** | Flags when PubChem and OPERA disagree on GHS. |
| **Provenance tags** | Every datum tagged experimental vs predicted. |
| **VEGA integration** | Optional QSAR checks (mutagenicity, carcinogenicity, skin sensitization) when `VEGA_API_URL` is set. |
| **SDS-like export** | Structured report (Sections 2, 9, 11, 12). |

---

## Installation

```bash
cd <repo root>
pip install -r requirements.txt
# QHA_pro uses same deps; no extra install needed
```

---

## Quick Start

```bash
# Single compound
python QHA_pro/haz_assess_pro.py 67-64-1

# JSON output
python QHA_pro/haz_assess_pro.py 67-64-1 -o report.json

# CSV output
python QHA_pro/haz_assess_pro.py 67-64-1 -o report.csv --output-format csv

# SDS-like report
python QHA_pro/haz_assess_pro.py 67-64-1 --sds -o sds.txt

# Batch from JSON input
echo '[{"cas":"67-64-1"},{"cas":"50-00-0"}]' > in.json
python QHA_pro/haz_assess_pro.py -i in.json -o out.json

# Batch from CSV
python QHA_pro/haz_assess_pro.py --list compounds.csv -o reports/
```

---

## Output Structure (JSON)

```json
{
  "cas": "67-64-1",
  "status": "PubChem + OPERA",
  "ghs": {"h_codes": [...], "p_codes": [...], "h_codes_with_phrases": [...]},
  "pubchem": {"cid": 180, "ld50": {"value": "...", "source": "pubchem", "method": "experimental", "confidence": "high"}},
  "opera": {"ld50_mg_kg": {"value": 5800, "source": "opera", "method": "predicted"}},
  "conflicts": [{"endpoint": "oral", "pubchem_code": "H302", "opera_code": "H301", "message": "..."}],
  "ecotoxicity": {"aquatic_lc50_mg_l": 4.8, "h_codes_aquatic": ["H400"]},
  "exposure_bands": {"oral": {"band": 4, "ld50_mg_kg": 5800}, "dermal": {...}, "inhalation": {...}}
}
```

---

## VEGA Integration

VEGA provides QSAR predictions (mutagenicity, carcinogenicity, skin sensitization). To enable:

1. Run VEGA REST API (Docker) or CLI.
2. Set environment variable: `VEGA_API_URL=http://localhost:8080/vega`
3. QHA Pro will fetch predictions when available.

See [VEGA HUB](https://www.vegahub.eu/) for installation.

---

## File Layout

```
QHA_pro/
├── haz_assess_pro.py    # Main entry point
├── provenance.py        # Provenance, confidence, conflict detection
├── ecotoxicity.py       # Aquatic toxicity extraction
├── exposure_bands.py    # Oral/dermal/inhalation bands
├── vega_client.py       # VEGA QSAR (optional)
├── sds_export.py        # SDS-like report
└── README.md
```
