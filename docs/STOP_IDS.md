# Finding MTA Stop IDs

The realtime API needs a **stop ID** to tell you which trains are coming. This
page explains where those IDs come from and how to find the one you want.

> ⚠️ This document does **not** list every stop ID — there are ~1,500 of them.
> Instead it explains the system and points you to the authoritative source.

---

## Where stop IDs come from (GTFS)

Stop IDs are defined in the MTA's **GTFS static** dataset — the same data that
powers schedules in trip planners. Each station/platform has a stable id used by
both the static schedule and the realtime feeds.

- GTFS static (with `stops.txt`): <https://www.mta.info/developers>
- The relevant file is `stops.txt`, which maps `stop_id` → `stop_name`.

The realtime feeds reference these exact ids, which is why you pass them to
`/api/arrivals`.

---

## Direction suffixes: `N` and `S`

Most subway stop IDs have a **base id** plus a **direction suffix**:

| Suffix | Meaning |
| ------ | ------- |
| `N`    | Northbound platform (railroad "north" — not always literal north) |
| `S`    | Southbound platform |
| _(none)_ | The parent station (covers both directions) |

So for Bedford–Nostrand Avs on the G line:

| Stop ID | What it is |
| ------- | ---------- |
| `G33`   | Parent station (both directions) |
| `G33N`  | Northbound platform (toward Court Sq) |
| `G33S`  | Southbound platform (toward Church Av) |

The realtime feeds report arrivals at the **directional** platforms (`G33N`,
`G33S`), so those are what you normally query.

This app reads the suffix and reports it as `direction: "N"` / `"S"` in the JSON.

---

## Examples

| Stop ID | Station | Feed |
| ------- | ------- | ---- |
| `G33N`  | Bedford–Nostrand Avs (N) | `g` |
| `A41N`  | Jay St–MetroTech (N), A/C side | `ace` |
| `L08N`  | Bedford Av (N) | `l` |
| `R31N`  | Atlantic Av–Barclays (N), N/Q/R/W | `nqrw` |
| `635N`  | 14 St–Union Sq (N), numbered lines | `numbered` |

> IDs above are illustrative. Always confirm against the current `stops.txt`,
> since the MTA occasionally revises the dataset.

---

## How to find more stop IDs

You have a few easy options:

1. **Download `stops.txt`** from the MTA developer page and search by station
   name. The `stop_id` column is what you want. Add `N`/`S` for direction.
2. **Browse a community map.** Sites and repos that visualize GTFS often show
   the stop id when you click a station.
3. **Peek at a live feed.** Hit `/api/arrivals` with a guessed id; if you get
   results, it's valid. You can also inspect a feed's raw `stop_id` values in
   `app/mta.py` by logging them.

---

## Quick start IDs to try

If you just want to see the app work, try these on their feeds:

```
feed=g       stop_id=G33N
feed=l       stop_id=L08N
feed=ace     stop_id=A41N
feed=numbered stop_id=635N
```

If a stop returns nothing, it may simply have no service at the moment, or the
direction suffix may be flipped — try the `S` variant.
