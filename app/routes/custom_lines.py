"""Custom subway line endpoints (CRUD + station editing).

These power the "Make Your Own Subway Line" half of the project. All data is
persisted to ``data/custom_lines.json`` via the storage module.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import storage
from ..models import (
    CustomLine,
    CustomLineCreate,
    CustomLineUpdate,
    Station,
)

router = APIRouter(prefix="/api/custom-lines", tags=["custom-lines"])


@router.get("")
def get_all():
    """List all saved custom lines."""
    return {"lines": [line.model_dump() for line in storage.list_lines()]}


@router.post("", status_code=201)
def create(payload: CustomLineCreate):
    """Create a new custom line. Generates a unique id if none is given."""
    line_id = payload.id or storage.unique_line_id(payload.name)
    if storage.get_line(line_id):
        raise HTTPException(409, f"Line '{line_id}' already exists")

    line = CustomLine(
        id=line_id,
        name=payload.name,
        bullet=payload.bullet,
        color=payload.color,
        description=payload.description,
        stations=payload.stations,
    )
    return storage.save_line(line).model_dump()


@router.get("/{line_id}")
def get_one(line_id: str):
    """Fetch a single custom line by id."""
    line = storage.get_line(line_id)
    if not line:
        raise HTTPException(404, f"Line '{line_id}' not found")
    return line.model_dump()


@router.put("/{line_id}")
def update(line_id: str, payload: CustomLineUpdate):
    """Update fields on a line (partial update — only sent fields change)."""
    line = storage.get_line(line_id)
    if not line:
        raise HTTPException(404, f"Line '{line_id}' not found")

    data = line.model_dump()
    for field, value in payload.model_dump(exclude_unset=True).items():
        data[field] = value

    updated = CustomLine(**data)
    return storage.save_line(updated).model_dump()


@router.delete("/{line_id}", status_code=204)
def delete(line_id: str):
    """Delete a custom line."""
    if not storage.delete_line(line_id):
        raise HTTPException(404, f"Line '{line_id}' not found")
    return None


@router.post("/{line_id}/stations", status_code=201)
def add_station(line_id: str, station: Station):
    """Append a station to a line.

    If a station with the same id already exists, it's rejected so ids stay
    unique within a line.
    """
    line = storage.get_line(line_id)
    if not line:
        raise HTTPException(404, f"Line '{line_id}' not found")
    if any(s.id == station.id for s in line.stations):
        raise HTTPException(409, f"Station '{station.id}' already exists")

    line.stations.append(station)
    return storage.save_line(line).model_dump()


@router.delete("/{line_id}/stations/{station_id}")
def remove_station(line_id: str, station_id: str):
    """Remove a station from a line by station id."""
    line = storage.get_line(line_id)
    if not line:
        raise HTTPException(404, f"Line '{line_id}' not found")

    remaining = [s for s in line.stations if s.id != station_id]
    if len(remaining) == len(line.stations):
        raise HTTPException(404, f"Station '{station_id}' not found")

    line.stations = remaining
    return storage.save_line(line).model_dump()
