"""
SDS-like structured export (Sections 2, 9, 11, 12).

Generates a report mimicking Safety Data Sheet structure:
- Section 2: Hazards identification (GHS, signal word, pictograms)
- Section 9: Physical and chemical properties
- Section 11: Toxicological information
- Section 12: Ecological information (ecotoxicity)
"""

from __future__ import annotations

from typing import Any


def format_sds_report(assessment: dict) -> str:
    """Format assessment as SDS-like text report."""
    lines = []
    cas = assessment.get("cas", "N/A")
    name = assessment.get("name") or cas
    lines.append("=" * 70)
    lines.append(f"HAZARD ASSESSMENT REPORT (SDS-style)")
    lines.append(f"Substance: {name}  |  CAS: {cas}")
    lines.append("=" * 70)

    # Section 2: Hazards identification
    lines.append("")
    lines.append("2. HAZARDS IDENTIFICATION")
    lines.append("-" * 40)
    ghs = assessment.get("ghs", {})
    h_codes = ghs.get("h_codes", [])
    p_codes = ghs.get("p_codes", [])
    if h_codes:
        lines.append("GHS Hazard statements:")
        for h in h_codes:
            lines.append(f"  - {h}")
    if p_codes:
        lines.append("GHS Precautionary statements:")
        for p in p_codes[:10]:
            lines.append(f"  - {p}")
        if len(p_codes) > 10:
            lines.append(f"  ... and {len(p_codes) - 10} more")
    conflicts = assessment.get("conflicts", [])
    if conflicts:
        lines.append("")
        lines.append("Conflict note (PubChem vs OPERA):")
        for c in conflicts:
            lines.append(f"  - {c.get('message', c)}")
    lines.append("")

    # Section 9: Physical and chemical properties
    lines.append("9. PHYSICAL AND CHEMICAL PROPERTIES")
    lines.append("-" * 40)
    props = assessment.get("physical_properties", {})
    for k, v in props.items():
        if v is not None and str(v).strip():
            lines.append(f"  {k}: {v}")
    lines.append("")

    # Section 11: Toxicological information
    lines.append("11. TOXICOLOGICAL INFORMATION")
    lines.append("-" * 40)
    tox = assessment.get("toxicology", {})
    for k, v in tox.items():
        if v is not None and str(v).strip():
            prov = v.get("_provenance", "")
            val = v.get("value", v) if isinstance(v, dict) else v
            if prov:
                lines.append(f"  {k}: {val} [{prov}]")
            else:
                lines.append(f"  {k}: {val}")
    exp = assessment.get("exposure_bands", {})
    if exp:
        lines.append("  Exposure bands:")
        for route, data in exp.items():
            if data.get("band"):
                lines.append(f"    - {route}: Category {data['band']} (LD50/LC50: {data.get('ld50_mg_kg') or data.get('lc50_mg_m3')})")
    lines.append("")

    # Section 12: Ecological information
    lines.append("12. ECOLOGICAL INFORMATION")
    lines.append("-" * 40)
    eco = assessment.get("ecotoxicity", {})
    if eco.get("aquatic_lc50_mg_l"):
        lines.append(f"  Aquatic LC50: {eco['aquatic_lc50_mg_l']} mg/L")
        if eco.get("aquatic_value_raw"):
            lines.append(f"  Raw: {eco['aquatic_value_raw'][:100]}...")
    if eco.get("h_codes_aquatic"):
        lines.append(f"  Aquatic H-codes: {', '.join(eco['h_codes_aquatic'])}")
    if not eco.get("aquatic_lc50_mg_l") and not eco.get("h_codes_aquatic"):
        lines.append("  No ecotoxicity data available.")
    lines.append("")
    lines.append("=" * 70)
    return "\n".join(lines)
