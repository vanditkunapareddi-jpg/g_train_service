# Development Guide

This project is intentionally small and readable. This guide explains how it's
put together and how to extend it.

---

## Architecture at a glance

```
HTTP request
   │
   ▼
main.py  ── creates the FastAPI app, mounts routers + static files
   │
   ├── app/routes/arrivals.py      → realtime endpoints
   │       └── app/mta.py          → fetch + parse GTFS-realtime
   │               └── app/config.py (feed URLs)
   │
   └── app/routes/custom_lines.py  → CRUD endpoints
           └── app/storage.py      → read/write data/custom_lines.json
                   └── app/models.py (Pydantic shapes)
```

Layering, top to bottom:

| Layer | Responsibility | Files |
| ----- | -------------- | ----- |
| **Entry** | App setup, routing, static serving | `main.py` |
| **Routes** | HTTP I/O, validation, status codes | `app/routes/*.py` |
| **Logic** | Feed parsing, storage | `app/mta.py`, `app/storage.py` |
| **Data** | Shapes + config | `app/models.py`, `app/config.py` |
| **Frontend** | UI | `static/*` |

The key idea: **routes stay thin**, and the real work lives in `mta.py` and
`storage.py`, which are plain functions you can unit-test without a server.

---

## Running locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

`--reload` restarts the server on file changes. Open `/docs` for live API docs.

---

## Adding a new API endpoint

1. **Pick or create a router.** Realtime → `app/routes/arrivals.py`; custom
   lines → `app/routes/custom_lines.py`. For a new area, make a new file in
   `app/routes/` that defines `router = APIRouter(prefix="/api/...")`.
2. **Add the handler:**
   ```python
   @router.get("/api/example")
   def example(q: str = Query(...)):
       return {"you_sent": q}
   ```
3. **Use models for bodies/responses** (define them in `app/models.py`) so you
   get validation and auto-docs for free.
4. **Register a new router** in `main.py`:
   ```python
   from app.routes import example
   app.include_router(example.router)
   ```
5. Keep handlers thin — push logic into a helper module.

### Adding a new MTA feed
Just add an entry to `MTA_FEEDS` in `app/config.py`:
```python
"mynewfeed": {
    "label": "My New Feed",
    "routes": ["X"],
    "url": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-...",
}
```
It immediately appears in `/api/feeds` and the UI dropdown — no other code changes.

---

## Adding a frontend feature

The frontend is plain HTML/CSS/JS with **no build step**:

- `static/index.html` — markup + element ids
- `static/styles.css` — all styling (CSS variables at `:root`)
- `static/app.js` — logic, organized into clearly commented sections
  (helpers → Tabs → Live Arrivals → Line Builder → Boot)

To add a feature:
1. Add the markup/ids you need in `index.html`.
2. Style it in `styles.css` (reuse the `.card`, `.btn`, `.bullet` classes).
3. Wire behavior in `app.js`. Use the existing `API` object for calls and
   `toast()` for feedback. Use `escapeHtml()` whenever you inject user data.

There's no framework, so changes are just an edit + browser refresh.

---

## Formatting & tests

No formatter or tests are required, but here's the recommended setup if you add
them:

```bash
pip install black pytest httpx

# format
black app main.py

# tests (see suggestion below)
pytest
```

A simple test using FastAPI's `TestClient` (needs `httpx`):

```python
from fastapi.testclient import TestClient
import main

client = TestClient(main.app)

def test_health():
    assert client.get("/health").json() == {"status": "ok"}

def test_custom_line_crud():
    r = client.post("/api/custom-lines", json={"name": "Test"})
    assert r.status_code == 201
    line_id = r.json()["id"]
    assert client.get(f"/api/custom-lines/{line_id}").status_code == 200
    assert client.delete(f"/api/custom-lines/{line_id}").status_code == 204
```

> Tip: tests that hit `/api/arrivals` touch the live MTA feeds, so they can be
> flaky offline. Prefer testing `mta.py`'s parsing with a saved sample feed, or
> mock `requests.get`.

---

## Known limitations

- **Realtime needs internet.** Without outbound HTTPS to `api-endpoint.mta.info`,
  arrivals return a graceful error. The line builder works fully offline.
- **Storage isn't concurrent-safe.** Two simultaneous writes to
  `custom_lines.json` could race. Fine for local/single-user use; swap in a DB
  for multi-user deployments.
- **No auth.** Anyone who can reach the server can edit lines. Don't expose it
  publicly without adding auth.
- **No station name validation against real GTFS** — custom stations are
  fictional by design.
- **Direction is inferred** from the `N`/`S` stop-id suffix, which is the MTA
  convention but not guaranteed for every id.

---

## Code style

- Type hints everywhere.
- Small, single-purpose functions.
- Comment the "why," not the obvious "what."
- Keep API responses consistent (`{"lines": [...]}`, `{"feeds": [...]}`, the
  `ArrivalsResponse` envelope).
