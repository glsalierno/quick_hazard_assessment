"""
Route-specific exposure bands.

Maps LD50/LC50 values to GHS-style exposure categories for:
- Oral (LD50 mg/kg)
- Dermal (LD50 mg/kg)
- Inhalation (LC50 mg/m³ or ppm)
"""

from __future__ import annotations

import re
from typing import Any

# GHS Acute Toxicity Categories (oral LD50 mg/kg)
# Cat 1: ≤5, Cat 2: >5–50, Cat 3: >50–300, Cat 4: >300–2000, Cat 5: >2000–5000
ORAL_BANDS = [(5, 1), (50, 2), (300, 3), (2000, 4), (5000, 5)]
DERMAL_BANDS = [(50, 1), (200, 2), (1000, 3), (2000, 4), (5000, 5)]


def _extract_ld50_mg_kg(toxicities: list, route: str) -> float | None:
    """Extract LD50 in mg/kg for oral or dermal from toxicities."""
    route_lower = route.lower()
    for t in toxicities or []:
        val = (t.get("value") or "").upper()
        vr = (t.get("value") or "").lower()
        if "LD50" not in val:
            continue
        if route_lower == "oral" and ("oral" in vr or "po" in vr or "rat" in vr and "oral" not in vr):
            m = re.search(r"(\d+(?:\.\d+)?)\s*mg\s*/\s*kg", vr)
            if m:
                try:
                    return float(m.group(1))
                except ValueError:
                    pass
        if route_lower == "dermal" and ("dermal" in vr or "skin" in vr):
            m = re.search(r"(\d+(?:\.\d+)?)\s*mg\s*/\s*kg", vr)
            if m:
                try:
                    return float(m.group(1))
                except ValueError:
                    pass
    for t in toxicities or []:
        val = (t.get("value") or "").lower()
        if "LD50" in val.upper() and "mg" in val and "kg" in val:
            m = re.search(r"(\d+(?:\.\d+)?)\s*mg\s*/\s*kg", val)
            if m:
                try:
                    return float(m.group(1))
                except ValueError:
                    pass
    return None


def _extract_lc50_inhalation(toxicities: list) -> float | None:
    """Extract LC50 inhalation in mg/m³ (or approximate from ppm)."""
    for t in toxicities or []:
        val = (t.get("value") or "").lower()
        if "LC50" not in val.upper():
            continue
        m = re.search(r"(\d+(?:[.,]\d+)*)\s*mg\s*/\s*m", val)
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except ValueError:
                pass
        m = re.search(r"=\s*(\d+(?:[.,]\d+)*)\s*mg/m3", val, re.I)
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except ValueError:
                pass
    return None


def _band_from_value(value: float, bands: list[tuple[float, int]]) -> int:
    """Map numeric value to band (1=most severe)."""
    for threshold, band in bands:
        if value <= threshold:
            return band
    return 5


def compute_exposure_bands(hazard_data: dict, opera_ld50: float | None = None) -> dict:
    """
    Compute route-specific exposure bands for oral, dermal, inhalation.
    Returns dict with oral_band, dermal_band, inhalation_band, and raw values.
    """
    tox = hazard_data.get("toxicities") or []
    out = {
        "oral": {"band": None, "ld50_mg_kg": None, "source": None},
        "dermal": {"band": None, "ld50_mg_kg": None, "source": None},
        "inhalation": {"band": None, "lc50_mg_m3": None, "source": None},
    }
    ld50_oral = _extract_ld50_mg_kg(tox, "oral")
    ld50_dermal = _extract_ld50_mg_kg(tox, "dermal")
    lc50_inh = _extract_lc50_inhalation(tox)
    if opera_ld50 is not None:
        ld50_oral = ld50_oral or opera_ld50
        out["oral"]["source"] = "opera" if ld50_oral == opera_ld50 else "pubchem"
    if ld50_oral is not None:
        out["oral"]["ld50_mg_kg"] = ld50_oral
        out["oral"]["band"] = _band_from_value(ld50_oral, ORAL_BANDS)
        out["oral"]["source"] = out["oral"]["source"] or "pubchem"
    if ld50_dermal is not None:
        out["dermal"]["ld50_mg_kg"] = ld50_dermal
        out["dermal"]["band"] = _band_from_value(ld50_dermal, DERMAL_BANDS)
        out["dermal"]["source"] = "pubchem"
    if lc50_inh is not None:
        out["inhalation"]["lc50_mg_m3"] = lc50_inh
        if lc50_inh <= 100:
            out["inhalation"]["band"] = 1
        elif lc50_inh <= 500:
            out["inhalation"]["band"] = 2
        elif lc50_inh <= 2500:
            out["inhalation"]["band"] = 3
        elif lc50_inh <= 20000:
            out["inhalation"]["band"] = 4
        else:
            out["inhalation"]["band"] = 5
        out["inhalation"]["source"] = "pubchem"
    return out
