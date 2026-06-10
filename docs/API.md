# API Reference

Base URL (local): `http://127.0.0.1:8000`

All responses are JSON unless noted. Interactive docs are auto-generated at
[`/docs`](http://127.0.0.1:8000/docs) (Swagger) and [`/redoc`](http://127.0.0.1:8000/redoc).

---

## Conventions

- **Feed ids** are short slugs: `ace`, `bdfm`, `g`, `jz`, `nqrw`, `l`, `numbered`, `sir`.
- **Stop ids** are GTFS ids, often with an `N`/`S` direction suffix, e.g. `G33N`. See [STOP_IDS.md](STOP_IDS.md).
- Arrival errors (MTA unreachable) return **HTTP 200** with an `error` field and an empty `arrivals` list, so simple clients don't crash.
- CRUD errors return standard HTTP codes (`404`, `409`) with `{"detail": "..."}`.

---

## Meta

### `GET /health`
Liveness check.

**Response**
```json
{ "status": "ok" }
```

### `GET /g-trains` (legacy)
Plain-text board kept for backwards compatibility: next 3 G trains toward Court Sq from `G33N`.

**Response** (`text/plain`)
```
G to COURT SQ: 2m 9m 16m
```

---

## Realtime arrivals

### `GET /api/feeds`
List supported MTA feed groups.

**Response**
```json
{
  "feeds": [
    { "id": "ace", "label": "A / C / E", "routes": ["A", "C", "E"] },
    { "id": "g",   "label": "G",         "routes": ["G"] }
  ]
}
```

### `GET /api/arrivals`
Upcoming arrivals at a stop, as JSON.

**Query params**

| Param     | Type   | Required | Default | Description |
| --------- | ------ | -------- | ------- | ----------- |
| `feed`    | string | yes      | —       | Feed id, e.g. `g`. |
| `stop_id` | string | yes      | —       | GTFS stop id, e.g. `G33N`. |
| `route`   | string | no       | —       | Filter to one route, e.g. `G`. |
| `limit`   | int    | no       | `5`     | 1–20 arrivals. |

**Example**
```
GET /api/arrivals?feed=g&stop_id=G33N&limit=5
```

**Response 200**
```json
{
  "feed": "g",
  "stop_id": "G33N",
  "count": 2,
  "arrivals": [
    { "route": "G", "stop_id": "G33N", "minutes": 2, "arrival_time": 1718000520, "direction": "N" },
    { "route": "G", "stop_id": "G33N", "minutes": 9, "arrival_time": 1718000940, "direction": "N" }
  ]
}
```

**Response 200 (feed error — graceful)**
```json
{
  "feed": "g",
  "stop_id": "G33N",
  "count": 0,
  "arrivals": [],
  "error": "Could not reach MTA feed 'g'"
}
```

### `GET /api/arrivals/text`
Same data as a compact text line — handy for display boards.

**Query params**

| Param     | Type   | Required | Default        | Description |
| --------- | ------ | -------- | -------------- | ----------- |
| `feed`    | string | yes      | —              | Feed id. |
| `stop_id` | string | yes      | —              | GTFS stop id. |
| `route`   | string | no       | —              | Route filter. |
| `label`   | string | no       | `Next trains`  | Prefix shown before the times. |
| `limit`   | int    | no       | `3`            | 1–10 arrivals. |

**Example**
```
GET /api/arrivals/text?feed=g&stop_id=G33N&label=G%20to%20Court%20Sq
```

**Response** (`text/plain`)
```
G to Court Sq: 2m 9m 16m
```

When there are no trains: `G to Court Sq: no trains`. On feed error: `G to Court Sq: error`.

---

## Custom lines

### `GET /api/custom-lines`
List all saved lines.

**Response**
```json
{ "lines": [ { "id": "sunset-express", "name": "Sunset Express", "bullet": "S", "color": "#FF6B35", "description": "...", "stations": [ ... ] } ] }
```

### `POST /api/custom-lines`
Create a line. `id` is generated from `name` if omitted.

**Request body**
```json
{
  "name": "Sunset Express",
  "bullet": "S",
  "color": "#FF6B35",
  "description": "A scenic coastal line.",
  "stations": [
    { "id": "pier-1", "name": "Pier One", "borough": "Brooklyn" }
  ]
}
```

**Response 201** — the created line (with its generated `id`).

**Error 409** — `id` already exists:
```json
{ "detail": "Line 'sunset-express' already exists" }
```

### `GET /api/custom-lines/{line_id}`
Fetch one line. **404** if not found.

### `PUT /api/custom-lines/{line_id}`
Partial update — only the fields you send are changed.

**Request body** (any subset)
```json
{ "color": "#00A1DE", "description": "Now express!" }
```

**Response 200** — the updated line. **404** if not found.

### `DELETE /api/custom-lines/{line_id}`
Delete a line. **204** on success, **404** if not found.

### `POST /api/custom-lines/{line_id}/stations`
Append a station.

**Request body**
```json
{ "id": "boardwalk", "name": "Boardwalk", "borough": "Brooklyn", "x": null, "y": null, "notes": null }
```

**Response 201** — the updated line.
**Error 409** — station id already exists. **404** — line not found.

### `DELETE /api/custom-lines/{line_id}/stations/{station_id}`
Remove a station by id.

**Response 200** — the updated line. **404** — line or station not found.

---

## Error shape (CRUD)

```json
{ "detail": "Line 'nope' not found" }
```

| Code | Meaning |
| ---- | ------- |
| 200  | OK |
| 201  | Created |
| 204  | Deleted (no body) |
| 404  | Line or station not found |
| 409  | Duplicate line or station id |
| 422  | Validation error (bad/missing fields) — FastAPI default |
