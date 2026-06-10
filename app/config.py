"""App-wide configuration.

Everything here is plain data so beginners can read it top-to-bottom.
No API keys are required for the MTA realtime feeds used below.
"""

from pathlib import Path

# --- Paths -----------------------------------------------------------------

# Project root = the folder that contains this "app" package.
BASE_DIR = Path(__file__).resolve().parent.parent

# Where custom subway lines are stored on disk.
DATA_DIR = BASE_DIR / "data"
CUSTOM_LINES_FILE = DATA_DIR / "custom_lines.json"

# Per-feed station list (real names -> stop ids), built by
# scripts/build_stations.py from the MTA's static + realtime data.
STATIONS_FILE = DATA_DIR / "stations.json"

# Where the static frontend lives.
STATIC_DIR = BASE_DIR / "static"


# --- MTA realtime feeds ----------------------------------------------------

# The MTA publishes GTFS-realtime feeds, grouped by which lines share tracks.
# These URLs are public and do NOT require an API key (as of 2024+).
#
# Each key below is a short "feed id" the API uses, e.g. ?feed=g
MTA_FEEDS = {
    "ace": {
        "label": "A / C / E",
        "routes": ["A", "C", "E"],
        "url": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
    },
    "bdfm": {
        "label": "B / D / F / M",
        "routes": ["B", "D", "F", "M"],
        "url": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
    },
    "g": {
        "label": "G",
        "routes": ["G"],
        "url": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g",
    },
    "jz": {
        "label": "J / Z",
        "routes": ["J", "Z"],
        "url": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-jz",
    },
    "nqrw": {
        "label": "N / Q / R / W",
        "routes": ["N", "Q", "R", "W"],
        "url": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
    },
    "l": {
        "label": "L",
        "routes": ["L"],
        "url": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-l",
    },
    "numbered": {
        "label": "1 / 2 / 3 / 4 / 5 / 6 / 7 / S",
        "routes": ["1", "2", "3", "4", "5", "6", "7", "GS"],
        "url": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    },
    "sir": {
        "label": "Staten Island Railway",
        "routes": ["SI"],
        "url": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-si",
    },
}

# How long to wait on the MTA before giving up (seconds).
FEED_TIMEOUT = 10

# Ignore arrivals further out than this — beyond here is usually schedule
# noise rather than a useful realtime prediction (seconds).
MAX_FUTURE_SECONDS = 60 * 60  # 60 minutes
