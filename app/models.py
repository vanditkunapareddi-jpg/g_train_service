"""Pydantic data models.

These describe the shape of our data for both validation and the API docs
that FastAPI generates automatically at ``/docs``.

Two groups of models live here:

1. Realtime arrivals (read-only, built from MTA feeds).
2. Custom subway lines (user created, saved to disk).
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


# --- Realtime arrivals -----------------------------------------------------


class Arrival(BaseModel):
    """A single upcoming train at a stop."""

    route: str = Field(..., description="Route id, e.g. 'G' or '7'")
    stop_id: str = Field(..., description="GTFS stop id, e.g. 'G33N'")
    minutes: int = Field(..., description="Minutes until arrival (rounded)")
    arrival_time: int = Field(..., description="Unix timestamp of arrival")
    direction: Optional[str] = Field(
        None, description="'N' or 'S' if encoded in the stop id"
    )


class ArrivalsResponse(BaseModel):
    """Standard JSON envelope returned by the arrivals endpoint."""

    feed: str
    stop_id: str
    count: int
    arrivals: List[Arrival]
    error: Optional[str] = Field(
        None, description="Set when the feed could not be fetched/parsed"
    )


# --- Custom subway lines ---------------------------------------------------


class Station(BaseModel):
    """One stop on a custom line."""

    id: str = Field(..., description="Unique station id within the line")
    name: str = Field(..., description="Display name, e.g. 'Cloud City'")
    borough: Optional[str] = Field(None, description="Optional borough/area")
    x: Optional[float] = Field(None, description="Optional map x coordinate")
    y: Optional[float] = Field(None, description="Optional map y coordinate")
    notes: Optional[str] = Field(None, description="Optional free-form notes")


class CustomLine(BaseModel):
    """A complete fictional subway line."""

    id: str = Field(..., description="Unique line id (slug)")
    name: str = Field(..., description="Line name, e.g. 'Sunset Express'")
    bullet: str = Field(..., description="Short bullet label, e.g. 'X'")
    color: str = Field("#0039A6", description="Hex route color, e.g. '#0039A6'")
    description: str = Field("", description="Optional description")
    stations: List[Station] = Field(default_factory=list)


class CustomLineCreate(BaseModel):
    """Request body for creating a line. ``id`` is generated if omitted."""

    id: Optional[str] = None
    name: str
    bullet: str = "?"
    color: str = "#0039A6"
    description: str = ""
    stations: List[Station] = Field(default_factory=list)


class CustomLineUpdate(BaseModel):
    """Request body for updating a line. All fields optional (partial update)."""

    name: Optional[str] = None
    bullet: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None
    stations: Optional[List[Station]] = None
