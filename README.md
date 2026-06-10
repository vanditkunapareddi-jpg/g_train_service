# 🚇 NextStop

**Know exactly when your next train is coming — so you can plan your day around it.**

NextStop is a small, readable FastAPI app that serves **realtime NYC subway arrivals** for any station, using the MTA's public GTFS-realtime feeds. **No API key required.**

It's designed to be the engine behind whatever you want to build:

- 🖥️ A live arrivals **display board** on an Arduino + LED matrix or e-ink screen by your front door.
- 📧 A morning **"leave now to catch your train"** email or push alert.
- ⌚ A terminal/desktop widget that shows the next few trains at your stop.
- 🏠 A Home Assistant / smart-home tile.

Because it exposes a clean JSON API **and** a dead-simple plain-text endpoint, you can wire it into almost anything — a microcontroller, a cron job, a shell script, or another app.

> It also ships with a **Subway Line Builder** — a fun secondary tool for designing your own fictional subway line. See [Custom Lines](#-bonus-build-your-own-subway-line) below.

---

## ✨ What you can do

- 🚉 See the **next trains at your station**, by name — pick a feed, a station, and a direction.
- 🔌 Get arrivals as **JSON** (for apps) or **plain text** (for display boards / terminals).
- 🛰️ Covers **all** major MTA feed groups: A/C/E, B/D/F/M, G, J/Z, N/Q/R/W, L, the numbered lines (1–7, S), and Staten Island Railway.
- 🩺 `/health` endpoint and graceful feed-error handling — it never crashes on a network hiccup.
- 🔌 Auto-generated, interactive API docs at `/docs`.
- 🎨 *(Bonus)* Design, save, and export your own custom subway lines.

---

## 🚀 Quick start

```bash
# 1. (Recommended) create a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run it
uvicorn main:app --reload
```

Then open:

- **Web UI:** http://127.0.0.1:8000
- **API docs:** http://127.0.0.1:8000/docs
- **Health check:** http://127.0.0.1:8000/health

**Requirements:** Python 3.9+. No Node.js, no database, no API keys.

---

## 🖥️ Using the web UI

On the **Live Arrivals** tab:

1. Choose a **feed** (e.g. `G`).
2. Pick your **station** by name from the dropdown.
3. Choose a **direction** (Northbound / Southbound).
4. *(Optional)* Filter by **route** and set a **limit**.
5. Click **Get Arrivals** to see the next trains in minutes.

Station names come from the MTA's static dataset, mapped to the right stop IDs for you — no need to memorize codes like `G33N`. Regenerate the station list anytime with `python scripts/build_stations.py`.

---

## 🔌 The API — build your own thing on top

NextStop is meant to be wired into hardware and automations. Two endpoints do the heavy lifting.

### JSON — for apps and scripts

```bash
# Next 5 G trains at Bedford–Nostrand Avs, northbound (toward Court Sq)
curl "http://127.0.0.1:8000/api/arrivals?feed=g&stop_id=G33N&limit=5"
```

```json
{
  "feed": "g",
  "stop_id": "G33N",
  "count": 2,
  "arrivals": [
    { "route": "G", "stop_id": "G33N", "minutes": 3, "direction": "N", "arrival_time": 1717900000 },
    { "route": "G", "stop_id": "G33N", "minutes": 11, "direction": "N", "arrival_time": 1717900480 }
  ]
}
```

### Plain text — for display boards & terminals

Perfect for an e-ink screen, an LED matrix, or piping into a script. One short line, no JSON parsing needed:

```bash
curl "http://127.0.0.1:8000/api/arrivals/text?feed=g&stop_id=G33N&label=G%20to%20Court%20Sq"
# -> G to Court Sq: 3m 11m 20m
```

### Other endpoints

```bash
curl http://127.0.0.1:8000/api/feeds            # which feed groups exist
curl "http://127.0.0.1:8000/api/stops?feed=g"   # stations on a feed (name -> stop id)
curl http://127.0.0.1:8000/g-trains             # legacy plain-text G board
```

Full reference: [docs/API.md](docs/API.md). Finding stop IDs: [docs/STOP_IDS.md](docs/STOP_IDS.md).

---

## 💡 Use-case recipes

These aren't separate features to install — they're things the API makes easy. Treat them as starting points.

### 📟 Arduino / ESP32 LED board

Have the microcontroller poll the **text endpoint** every ~30 seconds and print the result to your display:

```cpp
// Pseudocode — your ESP32 sketch
String url = "http://<your-server>:8000/api/arrivals/text?feed=g&stop_id=G33N&label=G";
String line = httpGet(url);   // "G: 3m 11m 20m"
display.print(line);
```

Because the response is a single line of plain text, there's no JSON library or parsing required on the device.

### 📧 "Leave now" email alert (cron)

Run a small script on a schedule (e.g. weekday mornings at 8:10) that checks your stop and emails you if a train is within your walking window:

```bash
# crontab: 10 8 * * 1-5  /path/to/leave-now.sh
mins=$(curl -s "http://127.0.0.1:8000/api/arrivals?feed=g&stop_id=G33N&limit=1" | jq '.arrivals[0].minutes')
if [ "$mins" -le 8 ]; then
  echo "Leave now — next G in ${mins} min" | mail -s "🚇 Catch your train" you@example.com
fi
```

Swap `mail` for a push service (Pushover, ntfy, a Slack webhook) to get a phone notification instead.

### ⌚ Terminal widget

```bash
watch -n 30 'curl -s "http://127.0.0.1:8000/api/arrivals/text?feed=g&stop_id=G33N&label=G"'
```

---

## 📁 Folder structure

```txt
nextstop/
├── main.py                 # FastAPI entrypoint (run this)
├── requirements.txt
├── app/
│   ├── config.py           # MTA feed URLs + settings
│   ├── models.py           # Pydantic models
│   ├── storage.py          # local JSON storage (custom lines)
│   ├── mta.py              # GTFS-realtime fetch + parse
│   └── routes/
│       ├── arrivals.py     # realtime + station endpoints
│       └── custom_lines.py # custom line CRUD
├── scripts/
│   └── build_stations.py   # regenerate data/stations.json from MTA data
├── data/
│   ├── stations.json       # station names -> stop ids, per feed
│   └── custom_lines.json   # saved custom lines (auto-created)
├── docs/
│   ├── API.md
│   ├── STOP_IDS.md
│   ├── CUSTOM_LINES.md
│   └── DEVELOPMENT.md
└── static/                 # no-build web UI (HTML + CSS + vanilla JS)
```

---

## 🛰️ How realtime MTA data works

The MTA publishes **GTFS-realtime** feeds — binary [protocol buffer](https://protobuf.dev/) files updated every few seconds. Each feed covers a group of lines that share track (e.g. the `ace` feed covers A, C, and E).

NextStop:

1. Downloads the feed for your chosen group ([app/mta.py](app/mta.py)).
2. Parses it with `gtfs-realtime-bindings`.
3. Finds `trip_update` entries that stop at your `stop_id`.
4. Filters out canceled trips, skipped stops, past arrivals, and anything more than 60 minutes out (schedule noise).
5. Returns the soonest arrivals.

Feed URLs live in [app/config.py](app/config.py). They're public and need **no API key**. Station names come from the MTA's static GTFS dataset, baked into `data/stations.json` by [scripts/build_stations.py](scripts/build_stations.py).

---

## 🎨 Bonus: build your own subway line

NextStop also includes a small **Line Builder** (the **Line Builder** tab) — a creative side-feature for designing fictional subway lines.

- Pick a **name**, a colored **bullet**, and a **route color** (live preview).
- **Add, rename, reorder** (drag-to-reorder), and **remove** stations.
- **Save** lines locally (plain JSON in `data/custom_lines.json` — no database) and **export** any line as JSON.

See [docs/CUSTOM_LINES.md](docs/CUSTOM_LINES.md) for the schema and import/export details.

---

## 🧰 Troubleshooting

| Problem | Fix |
| --- | --- |
| `uvicorn: command not found` | Activate your venv and `pip install -r requirements.txt`. |
| Arrivals show "error" or empty | The MTA feed may be briefly down, or the station has no service right now. The app degrades gracefully and never crashes. |
| "No upcoming trains" | Normal late at night, or try the other direction (N ↔ S). |
| Station dropdown looks short | It only lists stops the feed was serving when `stations.json` was built. Re-run `python scripts/build_stations.py` at a busier time. |
| Port already in use | `uvicorn main:app --reload --port 8001`. |
| Feeds unreachable | Realtime needs outbound HTTPS to `api-endpoint.mta.info`. The line builder works fully offline. |

---

## 🗺️ Roadmap ideas

- [ ] Built-in alert scheduler (define "remind me to leave for the G at 8am") in the UI
- [ ] Native push/webhook support (Pushover, ntfy, Slack)
- [ ] Example Arduino/ESP32 sketch in `examples/`
- [ ] Cache feeds briefly to cut MTA requests under load
- [ ] Save favorite stops for one-click arrivals
- [ ] Import a custom line from a JSON file in the UI
- [ ] Dark mode

---

## 🤝 Contributing

Contributions welcome — this repo is meant to be approachable!

1. Fork and create a branch: `git checkout -b my-feature`.
2. Keep code readable and beginner-friendly (type hints, small functions).
3. Run the app and confirm `/health`, live arrivals, and the API still work.
4. Open a pull request describing your change.

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for architecture notes.

---

## 📄 License

MIT — do whatever you like, just keep the notice.

Realtime data is provided by the **MTA** under their open-data terms; this project is not affiliated with the MTA.
