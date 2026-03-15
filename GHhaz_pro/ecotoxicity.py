"""
Ecotoxicity extraction from hazard data.

Extracts aquatic toxicity (fish LC50, Daphnia EC50, algae, etc.) from
PubChem toxicities and hazard_metrics. OPERA 2.9 has limited aquatic
endpoints; we focus on PubChem and structured extraction.
"""

from __future__ import annotations

import re
from typing import Any


def _parse_lc50_mg_l(value: str) -> float | None:
    """Extract numeric LC50/EC50 in mg/L from text."""
    if not value:
        return None
    # Patterns: "LC50 = 2.5 mg/L", "5,540 mg/L", "96h LC50 1.2 mg/L"
    m = re.search(r"(?:LC50|EC50|LC50\s*\([^)]+\))\s*[=:]?\s*([0-9.,]+)\s*mg\s*/\s*L", value, re.I)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except ValueError:
            pass
    m = re.search(r"([0-9.,]+)\s*mg\s*/\s*L", value, re.I)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except ValueError:
            pass
    return None


def extract_ecotoxicity(hazard_data: dict) -> dict:
    """
    Extract ecotoxicity endpoints from PubChem hazard data.
    Returns dict with aquatic_lc50_mg_l, aquatic_species, h_codes_aquatic, etc.
    """
    out = {
        "aquatic_lc50_mg_l": None,
        "aquatic_ec50_mg_l": None,
        "aquatic_species": None,
        "aquatic_value_raw": None,
        "h_codes_aquatic": [],
        "source": "pubchem",
        "method": "experimental",
        "confidence": "medium",
    }
    ghs = hazard_data.get("ghs") or {}
    h_codes = ghs.get("h_codes") or []
    aquatic_codes = [h for h in h_codes if h.startswith("H4")]
    if aquatic_codes:
        out["h_codes_aquatic"] = aquatic_codes

    tox = hazard_data.get("toxicities") or []
    for t in tox:
        val = (t.get("value") or "").lower()
        if "fish" in val or "trout" in val or "daphnia" in val or "algae" in val or "aquatic" in val:
            raw = t.get("value", "")
            lc50 = _parse_lc50_mg_l(raw)
            if lc50 is not None:
                out["aquatic_lc50_mg_l"] = lc50
                out["aquatic_value_raw"] = raw[:200]
                out["aquatic_species"] = "fish" if "fish" in val or "trout" in val else "other"
                out["method"] = "experimental"
                out["confidence"] = "high"
                break
    if not out["aquatic_lc50_mg_l"]:
        for t in tox:
            if "LC50" in (t.get("value") or "").upper() and "mg" in (t.get("value") or "").lower():
                lc50 = _parse_lc50_mg_l(t.get("value", ""))
                if lc50 is not None:
                    out["aquatic_lc50_mg_l"] = lc50
                    out["aquatic_value_raw"] = t.get("value", "")[:200]
                    out["method"] = "experimental"
                    out["confidence"] = "medium"
                    break
    return out
