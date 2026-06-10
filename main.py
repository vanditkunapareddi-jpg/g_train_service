"""NextStop — FastAPI entrypoint.

Run locally with:

    uvicorn main:app --reload

Then open http://127.0.0.1:8000 for the web UI, or http://127.0.0.1:8000/docs
for the auto-generated API documentation.
"""

from __future__ import annotations

from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import STATIC_DIR
from app.mta import FeedError, get_arrivals
from app.routes import arrivals, custom_lines

app = FastAPI(
    title="NextStop",
    description=(
        "Realtime NYC subway arrivals for any station — built to drive display "
        "boards, alerts, and integrations. Also includes a custom line builder."
    ),
    version="1.0.0",
)

# Register the API routers.
app.include_router(arrivals.router)
app.include_router(custom_lines.router)


@app.get("/health", tags=["meta"])
def health():
    """Simple liveness check."""
    return {"status": "ok"}


# --- Backwards-compatible original endpoint --------------------------------
# The project started as a single G-train board. We keep this working so older
# display boards pointed at /g-trains don't break.


@app.get("/g-trains", tags=["meta"])
def g_trains():
    """Legacy plain-text board: next G trains toward Court Sq from G33N."""
    label = "G to COURT SQ"
    try:
        results = get_arrivals("g", "G33N", route="G", limit=3)
    except FeedError:
        return Response(content=f"{label}: error", media_type="text/plain")

    if not results:
        body = f"{label}: no trains"
    else:
        body = f"{label}: " + " ".join(f"{a.minutes}m" for a in results)
    return Response(content=body, media_type="text/plain")


# --- Frontend --------------------------------------------------------------
# Serve the static web UI. We mount it last so it doesn't shadow /api routes.

if STATIC_DIR.exists():

    @app.get("/", include_in_schema=False)
    def index():
        """Serve the single-page web UI."""
        return FileResponse(STATIC_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
