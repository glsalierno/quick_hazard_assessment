"""Merge EPA CompTox ToxValDB into hazard_data (same shape as PubChem)."""

from __future__ import annotations

from typing import Any


def merge_comptox_into_hazard_data(
    hazard_data: dict[str, Any],
    comptox_result: dict[str, Any],
    prefer_experimental: bool = True,
) -> None:
    """Merge CompTox process_chemical() result into hazard_data in-place."""
    tox_data = (comptox_result or {}).get("ToxicityData")
    if not tox_data:
        return
    for item in tox_data.get("ld50") or []:
        num = item.get("toxvalNumeric")
        if num is None:
            continue
        try:
            val = float(num)
        except (TypeError, ValueError):
            continue
        unit = (item.get("toxvalUnits") or "mg/kg").replace("-", "/")
        species = item.get("speciesCommon") or "Rat"
        route = (item.get("exposureRoute") or "oral").lower()
        has_ld50 = any(
            "LD50" in (t.get("type") or "") or "LD50" in (t.get("value") or "").upper()
            for t in hazard_data.get("toxicities", [])
        )
        if not prefer_experimental or not has_ld50:
            hazard_data.setdefault("toxicities", []).append({
                "type": "LD50 (EPA CompTox)",
                "value": f"LD50 {species} {route} {val} {unit}",
                "unit": unit,
                "species_route": [route, species.lower()],
                "source": "EPA CompTox",
            })
        break
