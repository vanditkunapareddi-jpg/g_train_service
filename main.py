from fastapi import FastAPI, Response
from google.transit import gtfs_realtime_pb2
import requests
import time

app = FastAPI()

FEED_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g"
TARGET_STOP_ID = "G33N"  # Bedford–Nostrand Avs, COURT SQUARE–bound

def get_next_g_trains(max_trains: int = 3):
    # Get realtime feed
    resp = requests.get(FEED_URL, timeout=10)
    resp.raise_for_status()

    # Parse GTFS-realtime protobuf
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)

    now = int(time.time())
    arrivals = []

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue
        tu = entity.trip_update

        for stu in tu.stop_time_update:
            if stu.stop_id != TARGET_STOP_ID:
                continue

            # arrival if available, otherwise departure time
            t = stu.arrival.time or stu.departure.time
            if t <= now:
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
        text = "G to COURT SQ: error"
        return Response(content=text, media_type="text/plain")

    if not mins:
        text = "G to COURT SQ: no trains"
    else:
        text = "G to COURT SQ: " + " ".join(f"{m}m" for m in mins)

    return Response(content=text, media_type="text/plain")


@app.get("/health")
def health():
    return {"status": "ok"}
