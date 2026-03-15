"""
EPA DSSTox local lookup - no API key required.

Uses a user-downloaded mapping file (CSV or Excel) from EPA CompTox.
Download from: https://www.epa.gov/comptox-tools/downloadable-computational-toxicology-data
See README for links to CAS-DTXSID mapping files.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

# Flexible column name variants for CAS and DTXSID
CAS_COLS = ("casrn", "cas", "cas_registry_number", "cas_number", "cas number")
DTXSID_COLS = ("dtxsid", "dsstox_substance_id", "dsstox substance id")
NAME_COLS = ("preferred_name", "preferredname", "substance_name", "preferred chemical name", "chemical_name")


CAS_PATTERN = re.compile(r"^\d+-\d+-\d+$")


def _norm_cas(s) -> str:
    """Normalize CAS for lookup. Returns empty if not a valid CAS format."""
    if s is None or (isinstance(s, float) and (s != s or s == 0)):
        return ""
    t = str(s).strip()
    # Excel may convert 67-64-1 to 67.64; try to recover
    if "." in t and t.replace(".", "-", 1).count("-") == 2:
        t = t.replace(".", "-", 1)
    return t if CAS_PATTERN.match(t) else ""


def load_dsstox_db(path: Path | str) -> dict[str, dict[str, Any]]:
    """
    Load DSSTox mapping from CSV or Excel.
    Returns dict: normalized_cas -> {dtxsid, preferred_name, ...}
    """
    path = Path(path)
    if not path.exists():
        return {}
    try:
        import pandas as pd
    except ImportError:
        return {}
    try:
        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path, dtype=str, low_memory=False)
        elif path.suffix.lower() in (".xlsx", ".xls"):
            df = pd.read_excel(path, dtype=str, engine="openpyxl")
        else:
            return {}
    except Exception:
        return {}
    if df.empty:
        return {}
    cols_lower = {c.strip().lower(): c for c in df.columns}
    cas_col = next((cols_lower.get(c) for c in CAS_COLS if c in cols_lower), None)
    dtxsid_col = next((cols_lower.get(c) for c in DTXSID_COLS if c in cols_lower), None)
    name_col = next((cols_lower.get(c) for c in NAME_COLS if c in cols_lower), None)
    if not cas_col or not dtxsid_col:
        return {}
    out: dict[str, dict[str, Any]] = {}
    for _, row in df.iterrows():
        cas = _norm_cas(row.get(cas_col))
        dtxsid = str(row.get(dtxsid_col) or "").strip()
        if not dtxsid or not dtxsid.upper().startswith("DTXSID"):
            continue
        name = str(row.get(name_col) or "").strip() if name_col else ""
        # Prefer first occurrence; CAS may appear multiple times
        if cas not in out:
            out[cas] = {"dtxsid": dtxsid, "preferred_name": name or None}
    return out


class DSSToxLocalDB:
    """In-memory DSSTox lookup from a local file."""

    def __init__(self, db_path: Path | str | None = None):
        self._db: dict[str, dict[str, Any]] = {}
        if db_path:
            self.load(db_path)

    def load(self, path: Path | str) -> bool:
        """Load mapping from file. Returns True if loaded."""
        self._db = load_dsstox_db(Path(path))
        return len(self._db) > 0

    def lookup(self, cas: str) -> Optional[dict[str, Any]]:
        """Lookup by CAS. Returns {dtxsid, preferred_name} or None."""
        if not cas:
            return None
        key = _norm_cas(cas)
        if key:
            r = self._db.get(key)
            if r:
                return r
        t = str(cas).strip()
        return self._db.get(t)

    def get_dtxsid(self, cas: str) -> Optional[str]:
        r = self.lookup(cas)
        return r.get("dtxsid") if r else None

    def get_preferred_name(self, cas: str) -> Optional[str]:
        r = self.lookup(cas)
        return r.get("preferred_name") if r else None
