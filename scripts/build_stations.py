"""One-off generator for data/stations.json.

Combines two MTA data sources so the UI can offer real station NAMES instead of
raw GTFS stop IDs:

1. GTFS *static* `stops.txt`  -> stop_id -> stop_name   (the human names)
2. GTFS *realtime* feeds      -> which stop_ids each feed actually serves

The result is a per-feed list of stations:

    { "g": [ {"id": "G33", "name": "Bedford-Nostrand Avs"}, ... ], ... }

`id` is the *base* (parent) stop id; the app appends the N/S direction suffix at
query time. Re-run this whenever the MTA revises its dataset:

    python scripts/build_stations.py
"""

from __future__ import annotations

import csv
import io
import json
import sys
import zipfile
from pathlib import Path
from urllib.request import urlopen

# Make the app package importable when run from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google.transit import gtfs_realtime_pb2  # noqa: E402

from app.config import CUSTOM_LINES_FILE, MTA_FEEDS  # noqa: E402

STATIC_GTFS_URL = "https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip"
OUT_FILE = CUSTOM_LINES_FILE.parent / "stations.json"


def load_stop_names() -> dict[str, str]:
    """Download stops.txt and map every stop_id -> stop_name."""
    print(f"Downloading static GTFS from {STATIC_GTFS_URL} ...")
    with urlopen(STATIC_GTFS_URL, timeout=60) as resp:
        raw = resp.read()
    names: dict[str, str] = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        with zf.open("stops.txt") as fh:
            reader = csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig"))
            for row in reader:
                names[row["stop_id"]] = row["stop_name"]
    print(f"  loaded {len(names)} stop names")
    return names


def base_id(stop_id: str) -> str:
    """Strip a trailing N/S direction suffix to get the parent station id."""
    if stop_id and stop_id[-1] in ("N", "S"):
        return stop_id[:-1]
    return stop_id


def stops_for_feed(feed_id: str, url: str) -> set[str]:
    """Fetch a realtime feed and collect every base stop id it references."""
    feed = gtfs_realtime_pb2.FeedMessage()
    with urlopen(url, timeout=30) as resp:
        feed.ParseFromString(resp.read())
    ids: set[str] = set()
    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue
        for stu in entity.trip_update.stop_time_update:
            if stu.stop_id:
                ids.add(base_id(stu.stop_id))
    return ids


def main() -> None:
    names = load_stop_names()
    result: dict[str, list[dict[str, str]]] = {}

    for feed_id, info in MTA_FEEDS.items():
        print(f"Fetching feed '{feed_id}' ...")
        try:
            base_ids = stops_for_feed(feed_id, info["url"])
        except Exception as exc:  # noqa: BLE001 - best-effort generation
            print(f"  !! could not fetch '{feed_id}': {exc}")
            result[feed_id] = []
            continue

        stations = [
            {"id": bid, "name": names.get(bid, bid)}
            for bid in base_ids
        ]
        stations.sort(key=lambda s: s["name"])
        result[feed_id] = stations
        print(f"  {len(stations)} stations")

    OUT_FILE.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nWrote {OUT_FILE}")


if __name__ == "__main__":
    main()
