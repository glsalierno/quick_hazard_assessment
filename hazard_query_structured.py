#!/usr/bin/env python3
"""
Structured Hazard Metrics Extractor

Extracts specific hazard data from PubChem:
  - GHS codes (H-codes, P-codes)
  - Toxicities with units, references, species
  - DTXSID (EPA DSSTox)
  - Flash point, NFPA, IARC, California Prop 65

Output: structured dict/JSON.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any, Optional

import pubchempy as pcp
import requests
from urllib.parse import quote

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
PUG_VIEW_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view"
REQUEST_DELAY = 0.25
MAX_RETRIES = 3

GHS_H_CODE = re.compile(r"H\d+(?:\+\d+)?(?:\s*\([^)]+\))?")
GHS_P_CODE = re.compile(r"P\d+(?:\+\d+)?(?:\s*\([^)]+\))?")
DTXSID_PATTERN = re.compile(r"DTXSID\d+", re.I)


def get_cid(identifier: str, input_type: str = "name") -> Optional[int]:
    """Resolve chemical identifier to PubChem CID."""
    try:
        if input_type.lower() == "cid":
            return int(identifier)
        if input_type.lower() == "cas":
            url = f"{PUBCHEM_BASE}/compound/xref/RegistryID/{quote(identifier)}/cids/JSON"
            time.sleep(REQUEST_DELAY)
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            data = r.json()
            cids = data.get("IdentifierList", {}).get("CID", [])
            return int(cids[0]) if cids else None
        cids = pcp.get_cids(identifier, input_type, "compound")
        return cids[0] if cids else None
    except (pcp.BadRequestError, pcp.NotFoundError, ValueError, requests.RequestException):
        return None


def _fetch_full_pug_view(cid: int) -> Optional[dict]:
    """Fetch full PUG View compound record."""
    url = f"{PUG_VIEW_BASE}/data/compound/{cid}/JSON"
    for attempt in range(MAX_RETRIES):
        try:
            time.sleep(REQUEST_DELAY)
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 503:
                time.sleep(2**attempt)
                continue
            r.raise_for_status()
        except (requests.RequestException, json.JSONDecodeError):
            if attempt == MAX_RETRIES - 1:
                return None
            time.sleep(2**attempt)
    return None


def _get_string_from_value(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, dict):
        swm = val.get("StringWithMarkup", [])
        if isinstance(swm, dict):
            swm = [swm]
        parts = []
        for item in (swm or []):
            if isinstance(item, dict) and "String" in item:
                parts.append(item["String"])
        return " ".join(parts).strip() if parts else val.get("String", "")
    return ""


def _get_reference_urls(val: Any) -> list[str]:
    urls = []
    if not isinstance(val, dict):
        return urls
    swm = val.get("StringWithMarkup", [])
    if isinstance(swm, dict):
        swm = [swm]
    for item in (swm or []):
        if isinstance(item, dict):
            for m in (item.get("Markup") or []):
                if isinstance(m, dict) and m.get("URL"):
                    urls.append(m["URL"])
    return urls


def _extract_ghs_codes(data: dict) -> dict[str, list[str]]:
    result = {"h_codes": [], "p_codes": [], "signal_word": "", "pictograms": []}
    if not isinstance(data, dict):
        return result

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            h = obj.get("TOCHeading", "")
            if "GHS" in str(h) or "Classification" in str(h):
                for info in obj.get("Information", []) or []:
                    name = info.get("Name", "")
                    val = info.get("Value", {})
                    text = _get_string_from_value(val)
                    if "pictogram" in name.lower():
                        for x in (val.get("StringWithMarkup") or []):
                            if isinstance(x, dict):
                                for m in (x.get("Markup") or []):
                                    extra = (m or {}).get("Extra", "").strip()
                                    if extra and extra not in result["pictograms"]:
                                        result["pictograms"].append(extra)
                    elif "signal" in name.lower():
                        result["signal_word"] = text or name
                    elif "hazard" in name.lower() and text:
                        for m in GHS_H_CODE.findall(text):
                            code = re.sub(r"\s*\([^)]+\)", "", m).strip()
                            if code and code not in result["h_codes"]:
                                result["h_codes"].append(code)
                    elif "precautionary" in name.lower() and text:
                        for m in GHS_P_CODE.findall(text):
                            code = re.sub(r"\s*\([^)]+\)", "", m).strip()
                            if code and code not in result["p_codes"]:
                                result["p_codes"].append(code)
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(data)
    result["h_codes"] = list(dict.fromkeys(result["h_codes"]))
    result["p_codes"] = list(dict.fromkeys(result["p_codes"]))
    return result


def _extract_toxicities_structured(data: dict) -> list[dict[str, Any]]:
    tox_entries: list[dict[str, Any]] = []
    tox_keywords = ["tox", "safety", "hazard", "health", "exposure", "pharmacokinetics", "carcinogen"]
    unit_pattern = re.compile(r"(mg/kg|mg/m³|ppm|g/kg|mL/kg|mg/L|µg/kg|mg/m3|ppb)\b", re.I)
    species_pattern = re.compile(r"\b(rat|mouse|rabbit|dog|guinea pig|human|oral|dermal|inhalation|ip|iv|sc|ld50|lc50)\b", re.I)

    def process_section(section: dict, parent_heading: str = "") -> None:
        if not isinstance(section, dict):
            return
        heading = section.get("TOCHeading", "")
        if not any(kw in str(heading).lower() for kw in tox_keywords):
            for sub in section.get("Section", []) or []:
                process_section(sub, heading)
            return
        for info in section.get("Information", []) or []:
            name = info.get("Name", "")
            val = info.get("Value", {})
            text = _get_string_from_value(val)
            if not text:
                continue
            refs = _get_reference_urls(val)
            units = unit_pattern.findall(text)
            species_route = species_pattern.findall(text)
            entry = {
                "type": name or "Toxicity",
                "value": text,
                "unit": units[0] if units else None,
                "species_route": list(dict.fromkeys(species_route)) if species_route else None,
                "reference_urls": refs[:5] if refs else None,
                "source_section": heading or parent_heading,
            }
            tox_entries.append(entry)
        for sub in section.get("Section", []) or []:
            process_section(sub, heading)

    record = data.get("Record", {}) or {}
    for section in record.get("Section", []) or []:
        process_section(section)
    return tox_entries


def _extract_alerts_structured(data: dict) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    if not isinstance(data, dict):
        return alerts

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            h = obj.get("TOCHeading", "")
            if "Pistoia" in str(h) or "CSL" in str(h) or "Reactivity" in str(h):
                for info in obj.get("Information", []) or []:
                    name = info.get("Name", "")
                    val = info.get("Value", {})
                    text = _get_string_from_value(val)
                    if not text and not name:
                        continue
                    key = (name or "").strip().lower().replace(" ", "_")
                    if key in ("csl_no", "csl_no.", "cslnumber"):
                        if alerts and "csl_no" not in alerts[-1]:
                            alerts[-1]["csl_no"] = text
                        else:
                            alerts.append({"csl_no": text, "details": {}})
                    elif key and alerts:
                        alerts[-1].setdefault("details", {})[name or "info"] = text
                    elif text and not alerts:
                        alerts.append({"csl_no": None, "details": {name or "info": text}})
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(data)
    if not alerts:
        def collect(obj: Any) -> None:
            if isinstance(obj, dict):
                h = obj.get("TOCHeading", "")
                if "Pistoia" in str(h) or "CSL" in str(h) or "Reactivity" in str(h):
                    for info in obj.get("Information", []) or []:
                        name = info.get("Name", "")
                        text = _get_string_from_value(info.get("Value", {}))
                        if name or text:
                            alerts.append({"name": name or "Alert", "value": text})
                for v in obj.values():
                    collect(v)
            elif isinstance(obj, list):
                for item in obj:
                    collect(item)
        collect(data)
    return alerts


def _extract_dtxsid(data: dict) -> Optional[str]:
    found: Optional[str] = None
    def walk(obj: Any) -> None:
        nonlocal found
        if found:
            return
        if isinstance(obj, str):
            m = DTXSID_PATTERN.search(obj)
            if m:
                found = m.group(0)
        elif isinstance(obj, dict):
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)
    walk(data)
    return found


def _extract_hazard_metrics(data: dict) -> dict[str, Any]:
    result = {"flash_point": [], "nfpa": [], "iarc": [], "prop65": [], "other_designations": []}

    def process_info(name: str, val: Any, heading: str) -> None:
        text = _get_string_from_value(val)
        if not text:
            return
        name_l = (name or "").lower()
        head_l = (heading or "").lower()
        if "flash point" in name_l or "flash point" in head_l:
            if text not in result["flash_point"]:
                result["flash_point"].append(text)
        if "nfpa" in name_l or "nfpa" in head_l or "national fire protection" in head_l:
            if text not in result["nfpa"]:
                result["nfpa"].append(text)
        if "iarc" in name_l or "iarc" in head_l or "iarc monographs" in head_l:
            if text not in result["iarc"]:
                result["iarc"].append(text)
        if "proposition 65" in name_l or "prop 65" in name_l or "prop. 65" in name_l:
            if text not in result["prop65"]:
                result["prop65"].append(text)
        if "california" in head_l and ("prop" in head_l or "65" in head_l):
            if text not in result["prop65"]:
                result["prop65"].append(text)
        for key in ["autoignition", "flammability", "explosive limit", "vapor pressure"]:
            if key in name_l or key in head_l:
                if text not in result["other_designations"]:
                    result["other_designations"].append(text)
                return

    def walk_section(section: dict, heading: str = "") -> None:
        if not isinstance(section, dict):
            return
        h = section.get("TOCHeading", "") or heading
        for info in section.get("Information", []) or []:
            process_info(info.get("Name", ""), info.get("Value", {}), h)
        for sub in section.get("Section", []) or []:
            walk_section(sub, h)

    record = data.get("Record", {}) or {}
    for section in record.get("Section", []) or []:
        walk_section(section)
    return result


def fetch_structured_hazards(cid: int) -> dict[str, Any]:
    """Fetch and extract structured hazard metrics from PubChem."""
    out = {
        "cid": cid,
        "dtxsid": None,
        "ghs": {},
        "toxicities": [],
        "alerts": [],
        "hazard_metrics": {},
    }
    compound_data = _fetch_full_pug_view(cid)
    if not compound_data:
        return out
    out["dtxsid"] = _extract_dtxsid(compound_data)
    out["ghs"] = _extract_ghs_codes(compound_data)
    out["toxicities"] = _extract_toxicities_structured(compound_data)
    out["alerts"] = _extract_alerts_structured(compound_data)
    out["hazard_metrics"] = _extract_hazard_metrics(compound_data)
    return out
