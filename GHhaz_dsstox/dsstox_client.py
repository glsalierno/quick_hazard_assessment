"""
EPA CompTox (DSSTox) client - ToxValDB hazard data.

API key is read from comptox_api_key.txt (same folder as this script).
Do NOT hardcode the API key. Create comptox_api_key.txt from comptox_api_key.txt.example.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

DSSTOX_DIR = Path(__file__).resolve().parent
DEFAULT_KEY_FILE = DSSTOX_DIR / "comptox_api_key.txt"
ENV_VAR = "COMPTOX_API_KEY"


def load_api_key(key_file: Path | str | None = None) -> str:
    """
    Load CompTox API key from file or environment.
    Priority: key_file path > COMPTOX_API_KEY env > comptox_api_key.txt in script dir.
    """
    if key_file:
        p = Path(key_file)
        if p.exists():
            for line in p.read_text(encoding="utf-8").strip().splitlines():
                line = line.split("#")[0].strip()
                if line and line != "YOUR_API_KEY_HERE":
                    return line
            return ""
    key = os.environ.get(ENV_VAR, "").strip()
    if key:
        return key
    if DEFAULT_KEY_FILE.exists():
        for line in DEFAULT_KEY_FILE.read_text(encoding="utf-8").strip().splitlines():
            line = line.split("#")[0].strip()
            if line and line != "YOUR_API_KEY_HERE":
                return line
    return ""


def get_hazard_data(dtxsid: str, api_key: str, use_ctxpy: bool = True) -> Optional[list[dict[str, Any]]]:
    """Fetch hazard data from EPA ToxValDB for a DTXSID."""
    if not api_key:
        return None
    if use_ctxpy:
        try:
            import ctxpy as ctx
            haz = ctx.Hazard(x_api_key=api_key)
            df = haz.search_toxvaldb(by="all", dtxsid=dtxsid)
            if df is not None and not df.empty and hasattr(df, "attrs") and df.attrs.get("response"):
                return df.attrs["response"]
            if df is not None and not df.empty:
                return df.to_dict("records")
            return []
        except ImportError:
            use_ctxpy = False
        except Exception:
            use_ctxpy = False
    import requests
    url = f"https://comptox.epa.gov/ctx-api/hazard/toxval/search/by-dtxsid/{dtxsid}"
    headers = {"x-api-key": api_key, "accept": "application/json"}
    try:
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        records = data if isinstance(data, list) else data.get("data", data)
        return records if isinstance(records, list) else [records]
    except Exception:
        return None


def extract_toxicity_data(hazard_records: Optional[list[dict[str, Any]]]) -> dict[str, Any]:
    """Extract LD50, carcinogenicity, genotoxicity from ToxValDB records."""
    out = {"ld50": [], "carcinogenicity": [], "genotoxicity": []}
    if not hazard_records:
        return out
    for item in hazard_records:
        tox_type = str(item.get("toxvalType", "") or "").upper()
        effect = str(item.get("toxicologicalEffect", "") or "").lower()
        combined = f"{tox_type} {effect}"
        if "LD50" in tox_type or "ld50" in combined or "lc50" in combined:
            out["ld50"].append(item)
        elif "carcinogen" in effect or "cancer" in combined:
            out["carcinogenicity"].append(item)
        elif "genotox" in effect or "mutagen" in effect or "genetox" in combined:
            out["genotoxicity"].append(item)
    return out


def process_chemical(
    identifier: str,
    id_type: str,
    api_key: str,
    use_ctxpy: bool = True,
) -> dict[str, Any]:
    """
    Resolve CAS/DTXSID and fetch ToxValDB hazard data.
    Returns dict with Identifier, IdType, ToxicityData, DTXSID, Error.
    """
    result = {"Identifier": identifier, "IdType": id_type, "ToxicityData": None, "Error": None}
    if not api_key:
        result["Error"] = "No CompTox API key. Create comptox_api_key.txt (see comptox_api_key.txt.example)."
        return result
    if id_type.upper() == "DTXSID":
        hazard_data = get_hazard_data(identifier, api_key, use_ctxpy=use_ctxpy)
        if hazard_data is not None:
            result["ToxicityData"] = extract_toxicity_data(hazard_data)
        else:
            result["Error"] = "Failed to retrieve hazard data"
    elif id_type.upper() == "CAS":
        try:
            import ctxpy as ctx
            chem = ctx.Chemical(x_api_key=api_key)
            search_result = chem.search(by="equals", query=identifier.strip())
            if search_result and len(search_result) > 0:
                dtxsid = search_result[0].get("dtxsid")
                if dtxsid:
                    result["DTXSID"] = dtxsid
                    result["preferredName"] = search_result[0].get("preferredName")
                    hazard_data = get_hazard_data(dtxsid, api_key, use_ctxpy=use_ctxpy)
                    if hazard_data is not None:
                        result["ToxicityData"] = extract_toxicity_data(hazard_data)
                    else:
                        result["Error"] = "Failed to retrieve hazard data"
                else:
                    result["Error"] = "CAS found but no DTXSID"
            else:
                result["Error"] = "CAS not found in CompTox"
        except ImportError:
            result["Error"] = "ctx-python required: pip install ctx-python"
        except Exception as e:
            result["Error"] = str(e)
    else:
        result["Error"] = "Invalid id_type (use DTXSID or CAS)"
    return result
