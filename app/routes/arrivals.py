"""Realtime arrivals endpoints.

Provides both a clean JSON API and a plain-text endpoint that's handy for
simple "display board" projects (e-ink screens, terminals, etc.).
"""

from __future__ import annotations

import json
from functools import lru_cache

from fastapi import APIRouter, Query, Response

from ..config import MTA_FEEDS, STATIONS_FILE
from ..mta import FeedError, get_arrivals, list_feeds
from ..models import ArrivalsResponse

router = APIRouter(prefix="/api", tags=["arrivals"])


@router.get("/feeds")
def feeds():
    """List every supported MTA realtime feed group."""
    return {"feeds": list_feeds()}


@lru_cache(maxsize=1)
def _load_stations() -> dict:
    """Load the per-feed station list (real names -> base stop ids).

    Returns an empty mapping if the file is missing so the UI can fall back to
    a plain stop-id box. Regenerate with: python scripts/build_stations.py
    """
    try:
        return json.loads(STATIONS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


@router.get("/stops")
def stops(feed: str = Query(..., description="Feed id, e.g. 'g' or 'ace'")):
    """List the stations on a feed, as ``{id, name}`` pairs.

    ``id`` is the *base* (parent) stop id; append ``N``/``S`` for direction
    when querying ``/api/arrivals``.
    """
    if feed not in MTA_FEEDS:
        return {"feed": feed, "stops": []}
    return {"feed": feed, "stops": _load_stations().get(feed, [])}


@router.get("/arrivals", response_model=ArrivalsResponse)
def arrivals(
    feed: str = Query(..., description="Feed id, e.g. 'g' or 'ace'"),
    stop_id: str = Query(..., description="GTFS stop id, e.g. 'G33N'"),
    route: str | None = Query(None, description="Optional route filter, e.g. 'G'"),
    limit: int = Query(5, ge=1, le=20, description="Max arrivals to return"),
):
    """Return upcoming arrivals at a stop as JSON.

    On a feed error we return an empty list with HTTP 200 plus an ``error``
    note, so simple frontends don't have to special-case network hiccups.
    """
    try:
        results = get_arrivals(feed, stop_id, route=route, limit=limit)
    except FeedError as exc:
        return ArrivalsResponse(
            feed=feed, stop_id=stop_id, count=0, arrivals=[], error=str(exc)
        )

    return ArrivalsResponse(
        feed=feed,
        stop_id=stop_id,
        count=len(results),
        arrivals=results,
    )


@router.get("/arrivals/text")
def arrivals_text(
    feed: str = Query(..., description="Feed id, e.g. 'g'"),
    stop_id: str = Query(..., description="GTFS stop id, e.g. 'G33N'"),
    route: str | None = Query(None, description="Optional route filter"),
    label: str = Query("Next trains", description="Display label prefix"),
    limit: int = Query(3, ge=1, le=10),
):
    """Return arrivals as a compact line of text, e.g. ``G to Court Sq: 2m 9m``."""
    try:
        results = get_arrivals(feed, stop_id, route=route, limit=limit)
    except FeedError:
        return Response(content=f"{label}: error", media_type="text/plain")

    if not results:
        body = f"{label}: no trains"
    else:
        body = f"{label}: " + " ".join(f"{a.minutes}m" for a in results)

    return Response(content=body, media_type="text/plain")
