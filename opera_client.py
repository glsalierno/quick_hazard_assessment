#!/usr/bin/env python3
"""
OPERA client for GHhaz hazard reports.

Fetches predicted hazard/toxicity endpoints from OPERA (CATMoS, physicochemical, etc.)
via the OPERA executable. Provides merge_opera_into_hazard_data and _parse_opera_row.

Ref: https://github.com/kmansouri/OPERA
"""

from __future__ import annotations

from typing import Any


def _parse_opera_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert one CSV row to our prediction dict. Supports OPERA 2.9 columns (MoleculeID, CATMoS_*, LogVP_pred) and legacy names."""
    pred: dict[str, Any] = {
        "source": "OPERA",
        "ld50_mg_kg": None,
        "ghs_h_codes": [],
        "vp_mmhg": None,
        "flash_point_c": None,
        "catmos_epa_pred": None,
    }
    mol_id = (row.get("MoleculeID") or row.get("CAS") or "").strip()
    if mol_id:
        pred["molecule_id"] = mol_id
    ld50_raw = (
        row.get("CATMoS_LD50_pred")
        or row.get("LD50_pred_mg_kg")
        or row.get("LD50_log_mg_kg")
        or row.get("LD50 (log mg/kg)")
        or ""
    )
    if ld50_raw != "":
        try:
            v = float(str(ld50_raw).strip())
            if row.get("CATMoS_LD50_pred") is not None and str(row.get("CATMoS_LD50_pred")).strip() != "":
                pred["ld50_mg_kg"] = v
            elif v < 100 and v > 0:
                pred["ld50_mg_kg"] = 10 ** v
            else:
                pred["ld50_mg_kg"] = v
        except ValueError:
            pass
    ghs_col = (
        row.get("CATMoS_GHS_pred")
        or row.get("GHS_category")
        or row.get("GHS category")
        or row.get("GHS Category")
        or ""
    )
    if ghs_col != "":
        pred["ghs_h_codes"] = _ghs_category_to_h_codes(str(ghs_col).strip())
    vp_raw = (
        row.get("LogVP_pred")
        or row.get("VP_pred_mmHg")
        or row.get("VP_log_mmHg")
        or row.get("VP (log mmHg)")
        or ""
    )
    if vp_raw != "":
        try:
            v = float(str(vp_raw).strip())
            if v < 10 and v > -20:
                pred["vp_mmhg"] = 10 ** v
            else:
                pred["vp_mmhg"] = v
        except ValueError:
            pass
    fp_raw = row.get("Flash_point_pred_C") or row.get("Flash point (°C)") or ""
    if fp_raw != "":
        try:
            pred["flash_point_c"] = float(str(fp_raw).strip())
        except ValueError:
            pass
    epa_raw = row.get("CATMoS_EPA_pred") or row.get("EPA_category") or ""
    if epa_raw != "":
        try:
            pred["catmos_epa_pred"] = int(float(str(epa_raw).strip()))
        except ValueError:
            pred["catmos_epa_pred"] = str(epa_raw).strip()
    return pred


def _ghs_category_to_h_codes(cat: str) -> list[str]:
    """Map GHS category text or number to approximate H-codes for P2OASys matrix."""
    cat_str = str(cat).strip().upper()
    try:
        n = int(float(cat_str))
        if 1 <= n <= 5:
            return _ghs_category_to_h_codes(f"Acute {n}" if "ACUTE" not in cat_str else cat_str)
    except (ValueError, TypeError):
        pass
    if "ACUTE 1" in cat_str or "CAT 1" in cat_str or cat_str == "1":
        return ["H300", "H310", "H330"]
    if "ACUTE 2" in cat_str or "CAT 2" in cat_str or cat_str == "2":
        return ["H300", "H310", "H330"]
    if "ACUTE 3" in cat_str or "CAT 3" in cat_str or cat_str == "3":
        return ["H301", "H311", "H331"]
    if "ACUTE 4" in cat_str or "CAT 4" in cat_str or cat_str == "4":
        return ["H302", "H312", "H332"]
    if "ACUTE 5" in cat_str or "CAT 5" in cat_str or cat_str == "5":
        return ["H303", "H313", "H333"]
    return []


def merge_opera_into_hazard_data(
    hazard_data: dict[str, Any],
    opera_predictions: dict[str, Any],
    prefer_experimental: bool = True,
) -> None:
    """
    Merge OPERA predictions into hazard_data in-place.
    Only adds predicted values where experimental is missing (if prefer_experimental).
    """
    if not opera_predictions:
        return
    ld50 = opera_predictions.get("ld50_mg_kg")
    if ld50 is not None:
        has_ld50 = any(
            "LD50" in (t.get("value") or "").upper()
            for t in hazard_data.get("toxicities", [])
        )
        if not prefer_experimental or not has_ld50:
            hazard_data.setdefault("toxicities", []).append({
                "type": "LD50 (OPERA predicted)",
                "value": f"LD50 Rat oral {ld50:.1f} mg/kg (OPERA)",
                "unit": "mg/kg",
                "species_route": ["oral"],
                "source": "OPERA",
            })
    h_codes = opera_predictions.get("ghs_h_codes") or []
    if h_codes:
        existing = (hazard_data.get("ghs") or {}).get("h_codes") or []
        if not prefer_experimental or not existing:
            hazard_data.setdefault("ghs", {})["h_codes"] = list(existing) + [c for c in h_codes if c not in existing]
    vp = opera_predictions.get("vp_mmhg")
    if vp is not None:
        hm = hazard_data.get("hazard_metrics") or {}
        other = hm.get("other_designations") or []
        has_vp = any("mm" in str(x).lower() and "hg" in str(x).lower() for x in other)
        if not prefer_experimental or not has_vp:
            hazard_data.setdefault("hazard_metrics", {}).setdefault("other_designations", []).append(
                f"{vp:.2f} mm Hg (OPERA)"
            )
    fp = opera_predictions.get("flash_point_c")
    if fp is not None:
        existing_fp = (hazard_data.get("hazard_metrics") or {}).get("flash_point") or []
        if not prefer_experimental or not existing_fp:
            hazard_data.setdefault("hazard_metrics", {}).setdefault("flash_point", []).append(
                f"{fp:.1f} °C (OPERA)"
            )
