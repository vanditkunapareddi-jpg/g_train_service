from fastapi import FastAPI, Response
from google.transit import gtfs_realtime_pb2
import requests
import time
import logging

app = FastAPI()

# MTA G line realtime feed
FEED_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g"

# Bedford–Nostrand northbound (toward Court Sq)
TARGET_STOP_ID = "G33N"
LABEL = "G to COURT SQ"


def get_next_g_trains(max_trains: int = 3):
    """
    Return a sorted list of arrival times (in minutes) for TARGET_STOP_ID.
    More defensive about canceled/skipped/ghost trains so we don't show
    obviously bogus predictions.
    """
    try:
        # Get realtime feed
        resp = requests.get(FEED_URL, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logging.exception("Error fetching MTA feed")
        return []

    # Parse GTFS-realtime protobuf
    feed = gtfs_realtime_pb2.FeedMessage()
    try:
        feed.ParseFromString(resp.content)
    except Exception as e:
        logging.exception("Error parsing GTFS feed")
        return []

    now = int(time.time())
    arrivals = []

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue

        tu = entity.trip_update

        # --- skip canceled trips (if enum exists) ---
        try:
            trip_sr = tu.trip.schedule_relationship
            if trip_sr == gtfs_realtime_pb2.TripDescriptor.CANCELED:
                continue
        except AttributeError:
            # Older bindings might not have the enum constant – ignore
            pass

        for stu in tu.stop_time_update:
            if stu.stop_id != TARGET_STOP_ID:
                continue

            # --- skip skipped stops (if enum exists) ---
            try:
                stop_sr = stu.schedule_relationship
                if stop_sr == gtfs_realtime_pb2.StopTimeUpdate.SKIPPED:
                    continue
            except AttributeError:
                pass

            # pick arrival or departure time
            t = stu.arrival.time or stu.departure.time
            if not t:
                continue

            # ignore past arrivals
            if t <= now:
                continue

            # ignore trains more than 60 minutes out (likely schedule noise)
            if t - now > 60 * 60:
                continue

            mins = int(round((t - now) / 60))
            arrivals.append(mins)

    arrivals.sort()
    return arrivals[:max_trains]


@app.get("/g-trains")
def g_trains():
    try:
        mins = get_next_g_trains()
    except Exception:
        logging.exception("/g-trains failed")
        text = f"{LABEL}: error"
        return Response(content=text, media_type="text/plain")

    if not mins:
        text = f"{LABEL}: no trains"
    else:
        text = LABEL + ": " + " ".join(f"{m}m" for m in mins)

    return Response(content=text, media_type="text/plain")


@app.get("/health")
def health():
    return {"status": "ok"}
