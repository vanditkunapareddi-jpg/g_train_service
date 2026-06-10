"""Local JSON file storage for custom subway lines.

We deliberately avoid a database so the project runs with zero setup.
Everything lives in ``data/custom_lines.json``. If that file is missing,
it is created automatically with a couple of fun sample lines.
"""

from __future__ import annotations

import json
import re
from typing import Dict, List, Optional

from .config import CUSTOM_LINES_FILE, DATA_DIR
from .models import CustomLine, Station

# --- Sample data -----------------------------------------------------------

# These ship with the repo so the UI is never empty on first run.
SAMPLE_LINES: List[dict] = [
    {
        "id": "sunset-express",
        "name": "Sunset Express",
        "bullet": "S",
        "color": "#FF6B35",
        "description": "A scenic coastal line that only runs at golden hour.",
        "stations": [
            {"id": "pier-1", "name": "Pier One", "borough": "Brooklyn"},
            {"id": "boardwalk", "name": "Boardwalk", "borough": "Brooklyn"},
            {"id": "lighthouse", "name": "Lighthouse Point", "borough": "Queens"},
            {"id": "dune-park", "name": "Dune Park", "borough": "Queens"},
        ],
    },
    {
        "id": "cloud-line",
        "name": "Cloud Line",
        "bullet": "C",
        "color": "#6C5CE7",
        "description": "An imaginary sky tram connecting floating neighborhoods.",
        "stations": [
            {"id": "nimbus", "name": "Nimbus Heights"},
            {"id": "cumulus", "name": "Cumulus Center"},
            {"id": "stratus", "name": "Stratus Yard"},
        ],
    },
]


# --- Helpers ---------------------------------------------------------------


def slugify(text: str) -> str:
    """Turn a name into a url-friendly id, e.g. 'My Line!' -> 'my-line'."""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "line"


def _ensure_file() -> None:
    """Create the data folder and seed file if they don't exist yet."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CUSTOM_LINES_FILE.exists():
        _write_raw(SAMPLE_LINES)


def _read_raw() -> List[dict]:
    _ensure_file()
    with open(CUSTOM_LINES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_raw(lines: List[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(CUSTOM_LINES_FILE, "w", encoding="utf-8") as f:
        json.dump(lines, f, indent=2, ensure_ascii=False)


# --- Public API ------------------------------------------------------------


def list_lines() -> List[CustomLine]:
    """Return all custom lines."""
    return [CustomLine(**raw) for raw in _read_raw()]


def get_line(line_id: str) -> Optional[CustomLine]:
    """Return one line by id, or None if not found."""
    for raw in _read_raw():
        if raw.get("id") == line_id:
            return CustomLine(**raw)
    return None


def save_line(line: CustomLine) -> CustomLine:
    """Insert or replace a line (matched by id)."""
    lines = _read_raw()
    payload = line.model_dump()
    for i, raw in enumerate(lines):
        if raw.get("id") == line.id:
            lines[i] = payload
            break
    else:
        lines.append(payload)
    _write_raw(lines)
    return line


def delete_line(line_id: str) -> bool:
    """Remove a line. Returns True if something was deleted."""
    lines = _read_raw()
    remaining = [raw for raw in lines if raw.get("id") != line_id]
    if len(remaining) == len(lines):
        return False
    _write_raw(remaining)
    return True


def unique_line_id(desired: str) -> str:
    """Return an id based on ``desired`` that isn't already taken."""
    base = slugify(desired)
    existing = {raw.get("id") for raw in _read_raw()}
    if base not in existing:
        return base
    n = 2
    while f"{base}-{n}" in existing:
        n += 1
    return f"{base}-{n}"
