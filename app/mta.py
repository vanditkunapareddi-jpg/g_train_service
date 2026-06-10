"""MTA GTFS-realtime feed fetching and parsing.

This module is the reusable core of the realtime feature. It knows how to:

1. Download a GTFS-realtime protobuf feed from the MTA.
2. Parse it into upcoming arrivals.
3. Filter out canceled trips, skipped stops, past arrivals, and far-future
   schedule noise.

It is intentionally small and well-commented so beginners can follow it.
No API key is required.
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional

import requests
from google.transit import gtfs_realtime_pb2

from .config import FEED_TIMEOUT, MAX_FUTURE_SECONDS, MTA_FEEDS
from .models import Arrival

logger = logging.getLogger(__name__)


class FeedError(Exception):
    """Raised when a feed cannot be fetched or parsed."""


def list_feeds() -> List[dict]:
    """Return metadata for every supported feed (for the API + UI)."""
    return [
        {"id": feed_id, "label": info["label"], "routes": info["routes"]}
        for feed_id, info in MTA_FEEDS.items()
    ]


def _direction_from_stop(stop_id: str) -> Optional[str]:
    """MTA stop ids often end in 'N' (north) or 'S' (south)."""
    if stop_id.endswith("N"):
        return "N"
    if stop_id.endswith("S"):
        return "S"
    return None


def _fetch_feed(feed_id: str) -> gtfs_realtime_pb2.FeedMessage:
    """Download and parse a raw GTFS-realtime feed.

    Raises FeedError on any network or parse problem so callers can decide
    how to present the failure.
    """
    if feed_id not in MTA_FEEDS:
        raise FeedError(f"Unknown feed '{feed_id}'")

    url = MTA_FEEDS[feed_id]["url"]
    try:
        resp = requests.get(url, timeout=FEED_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Failed to fetch feed %s: %s", feed_id, exc)
        raise FeedError(f"Could not reach MTA feed '{feed_id}'") from exc

    feed = gtfs_realtime_pb2.FeedMessage()
    try:
        feed.ParseFromString(resp.content)
    except Exception as exc:  # protobuf raises a variety of errors
        logger.warning("Failed to parse feed %s: %s", feed_id, exc)
        raise FeedError(f"Could not parse MTA feed '{feed_id}'") from exc

    return feed


def _is_canceled_trip(trip_update) -> bool:
    """True if the trip is marked CANCELED (guarding old protobuf bindings)."""
    try:
        canceled = gtfs_realtime_pb2.TripDescriptor.CANCELED
        return trip_update.trip.schedule_relationship == canceled
    except AttributeError:
        return False


def _is_skipped_stop(stop_time_update) -> bool:
    """True if this stop is marked SKIPPED."""
    try:
        skipped = gtfs_realtime_pb2.TripUpdate.StopTimeUpdate.SKIPPED
        return stop_time_update.schedule_relationship == skipped
    except AttributeError:
        # Fall back to the documented enum value (1 == SKIPPED).
        return getattr(stop_time_update, "schedule_relationship", 0) == 1


def get_arrivals(
    feed_id: str,
    stop_id: str,
    route: Optional[str] = None,
    limit: int = 5,
) -> List[Arrival]:
    """Return upcoming arrivals at ``stop_id`` from ``feed_id``.

    Args:
        feed_id: Short feed id, e.g. "g" or "ace".
        stop_id: GTFS stop id, e.g. "G33N".
        route:   Optional route filter, e.g. "G". If None, all routes count.
        limit:   Max number of arrivals to return.

    Raises:
        FeedError: if the feed can't be fetched or parsed.
    """
    feed = _fetch_feed(feed_id)
    now = int(time.time())
    arrivals: List[Arrival] = []

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue

        trip_update = entity.trip_update

        if _is_canceled_trip(trip_update):
            continue

        trip_route = trip_update.trip.route_id
        if route and trip_route != route:
            continue

        for stu in trip_update.stop_time_update:
            if stu.stop_id != stop_id:
                continue
            if _is_skipped_stop(stu):
                continue

            when = stu.arrival.time or stu.departure.time
            if not when:
                continue
            if when <= now:  # already departed
                continue
            if when - now > MAX_FUTURE_SECONDS:  # schedule noise
                continue

            arrivals.append(
                Arrival(
                    route=trip_route or "?",
                    stop_id=stop_id,
                    minutes=int(round((when - now) / 60)),
                    arrival_time=when,
                    direction=_direction_from_stop(stop_id),
                )
            )

    arrivals.sort(key=lambda a: a.arrival_time)
    return arrivals[:limit]
