"""
Provenance, confidence, and conflict detection for hazard data.

Every datum is tagged with:
- source: pubchem | opera | vega | comptox
- method: experimental | predicted | estimated
- confidence: high | medium | low
- validation_notes: optional comparison to reference data
"""

from __future__ import annotations

import re
from typing import Any

# GHS acute toxicity category -> severity (1=most severe, 5=least)
GHS_CAT_SEVERITY: dict[str, int] = {
    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5,
    "H300": 1, "H301": 2, "H302": 3, "H303": 4, "H304": 1,
    "H310": 1, "H311": 2, "H312": 3, "H313": 4,
    "H330": 1, "H331": 2, "H332": 3, "H333": 4,
    "H400": 1, "H410": 1, "H411": 2, "H412": 3, "H413": 4,
}
GHS_H_TO_CAT = re.compile(r"H(300|301|302|303|304|310|311|312|313|330|331|332|333|400|410|411|412|413)")


def tag_datum(value: Any, source: str, method: str = "experimental", confidence: str = "high") -> dict:
    """Wrap a value with provenance metadata."""
    return {
        "value": value,
        "source": source,
        "method": method,
        "confidence": confidence,
    }


def severity_of_h_code(h: str) -> int:
    """Return severity 1-5 for H-code (1=most severe)."""
    m = GHS_H_TO_CAT.search(h)
    if m:
        return GHS_CAT_SEVERITY.get(m.group(1), 3)
    return GHS_CAT_SEVERITY.get(h, 3)


def detect_ghs_conflicts(pubchem_h: list[str], opera_h: list[str]) -> list[dict]:
    """
    Compare PubChem and OPERA GHS H-codes. Return list of conflicts.
    Conflict = different severity for same endpoint (e.g. oral vs oral).
    """
    conflicts = []
    p_set = set(pubchem_h or [])
    o_set = set(opera_h or [])
    if not p_set or not o_set:
        return conflicts
    # Group by endpoint type: oral (H30x), dermal (H31x), inhalation (H33x), aquatic (H4xx)
    def endpoint_type(h: str) -> str:
        if h.startswith("H30") or h in ("H300", "H301", "H302", "H303", "H304"):
            return "oral"
        if h.startswith("H31"):
            return "dermal"
        if h.startswith("H33"):
            return "inhalation"
        if h.startswith("H4"):
            return "aquatic"
        return "other"
    for h_p in p_set:
        for h_o in o_set:
            if endpoint_type(h_p) == endpoint_type(h_o) and h_p != h_o:
                sev_p = severity_of_h_code(h_p)
                sev_o = severity_of_h_code(h_o)
                if abs(sev_p - sev_o) >= 1:
                    conflicts.append({
                        "endpoint": endpoint_type(h_p),
                        "pubchem_code": h_p,
                        "opera_code": h_o,
                        "pubchem_severity": sev_p,
                        "opera_severity": sev_o,
                        "message": f"{endpoint_type(h_p)}: PubChem {h_p} vs OPERA {h_o}",
                    })
    return conflicts


def with_provenance(value: Any, source: str, method: str, confidence: str = "high") -> dict:
    """Create a provenance-tagged datum."""
    return {"value": value, "source": source, "method": method, "confidence": confidence}


def format_provenance_tag(d: dict) -> str:
    """Format provenance for display: value [source: method, confidence]"""
    v = d.get("value")
    src = d.get("source", "?")
    met = d.get("method", "?")
    conf = d.get("confidence", "?")
    if v is None:
        return ""
    return f"{v} [{src}: {met}, {conf}]"
