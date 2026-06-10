/* ============================================================
   NextStop — frontend logic
   Plain JavaScript, no framework, no build step.
   ============================================================ */

const API = {
  feeds: () => fetch("/api/feeds").then(r => r.json()),
  stops: (feed) =>
    fetch("/api/stops?" + new URLSearchParams({ feed })).then(r => r.json()),
  arrivals: (params) =>
    fetch("/api/arrivals?" + new URLSearchParams(params)).then(r => r.json()),
  listLines: () => fetch("/api/custom-lines").then(r => r.json()),
  getLine: (id) => fetch(`/api/custom-lines/${id}`).then(r => r.json()),
  createLine: (body) =>
    fetch("/api/custom-lines", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(r => r.json()),
  updateLine: (id, body) =>
    fetch(`/api/custom-lines/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(r => r.json()),
  deleteLine: (id) =>
    fetch(`/api/custom-lines/${id}`, { method: "DELETE" }),
};

// ---------- tiny helpers ----------
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

function toast(msg, isError = false) {
  const el = $("#toast");
  el.textContent = msg;
  el.classList.toggle("err", isError);
  el.classList.remove("hidden");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => el.classList.add("hidden"), 2600);
}

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}

function slugify(text) {
  return (
    String(text).trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") ||
    "line"
  );
}

// ============================================================
// Tabs
// ============================================================
$$(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    $$(".tab").forEach((b) => b.classList.remove("active"));
    $$(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    $("#tab-" + btn.dataset.tab).classList.add("active");
  });
});

// ============================================================
// Live Arrivals
// ============================================================
async function loadFeeds() {
  try {
    const { feeds } = await API.feeds();
    const sel = $("#feed-select");
    sel.innerHTML = feeds
      .map((f) => `<option value="${f.id}">${escapeHtml(f.label)}</option>`)
      .join("");
    sel.value = "g"; // sensible default for the original G project
    sel.addEventListener("change", () => loadStations(sel.value));
    await loadStations(sel.value);
  } catch {
    toast("Could not load feeds", true);
  }
}

// Populate the Station dropdown for the chosen feed.
async function loadStations(feed) {
  const sel = $("#station-select");
  sel.innerHTML = `<option value="">Loading…</option>`;
  try {
    const { stops } = await API.stops(feed);
    if (!stops.length) {
      sel.innerHTML = `<option value="">No stations found</option>`;
      return;
    }
    // Disambiguate duplicate names (different complexes share a name) by
    // appending the stop id, so each option is distinguishable.
    const nameCounts = stops.reduce((m, s) => m.set(s.name, (m.get(s.name) || 0) + 1), new Map());
    sel.innerHTML = stops
      .slice()
      .sort((a, b) => a.name.localeCompare(b.name))
      .map((s) => {
        const label = nameCounts.get(s.name) > 1 ? `${s.name} (${s.id})` : s.name;
        return `<option value="${escapeHtml(s.id)}">${escapeHtml(label)}</option>`;
      })
      .join("");
    // Default to Bedford–Nostrand on the original G project.
    if (feed === "g" && stops.some((s) => s.id === "G33")) sel.value = "G33";
  } catch {
    sel.innerHTML = `<option value="">Could not load stations</option>`;
  }
}

$("#arrivals-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const box = $("#arrivals-result");
  const baseId = $("#station-select").value;
  if (!baseId) { toast("Pick a station first", true); return; }
  const stopId = baseId + $("#direction-select").value;
  const params = {
    feed: $("#feed-select").value,
    stop_id: stopId,
    limit: $("#limit").value || 5,
  };
  const route = $("#route-filter").value.trim();
  if (route) params.route = route;

  box.innerHTML = `<p class="empty">Loading…</p>`;
  try {
    const data = await API.arrivals(params);
    if (data.error) {
      box.innerHTML = `<div class="error-box">⚠️ ${escapeHtml(data.error)}</div>`;
      return;
    }
    if (!data.arrivals.length) {
      const station = $("#station-select").selectedOptions[0]?.textContent || params.stop_id;
      box.innerHTML = `<p class="empty">No upcoming trains at <strong>${escapeHtml(
        station
      )}</strong> right now. Try the other direction.</p>`;
      return;
    }
    box.innerHTML = data.arrivals
      .map((a) => {
        const dir = a.direction === "N" ? "Northbound" : a.direction === "S" ? "Southbound" : "";
        return `
          <div class="arrival-row">
            <div class="arrival-mins">${a.minutes}m</div>
            <span class="pill">${escapeHtml(a.route)}</span>
            <div class="arrival-meta">${escapeHtml(a.stop_id)}${dir ? " · " + dir : ""}</div>
          </div>`;
      })
      .join("");
  } catch {
    box.innerHTML = `<div class="error-box">⚠️ Something went wrong fetching arrivals.</div>`;
  }
});

// ============================================================
// Line Builder
// ============================================================
let lines = [];          // all saved lines
let current = null;      // the line being edited (working copy)

async function loadLines() {
  const data = await API.listLines();
  lines = data.lines || [];
  renderLinesList();
}

function renderLinesList() {
  const ul = $("#lines-list");
  if (!lines.length) {
    ul.innerHTML = `<li class="empty">No lines yet. Click “+ New”.</li>`;
    return;
  }
  ul.innerHTML = lines
    .map(
      (l) => `
      <li data-id="${l.id}" class="${current && current.id === l.id ? "selected" : ""}">
        <span class="bullet sm" style="--c:${escapeHtml(l.color)}">${escapeHtml(l.bullet)}</span>
        <span>${escapeHtml(l.name)}</span>
      </li>`
    )
    .join("");
  $$("#lines-list li[data-id]").forEach((li) =>
    li.addEventListener("click", () => selectLine(li.dataset.id))
  );
}

async function selectLine(id) {
  current = await API.getLine(id);
  showEditor();
}

$("#new-line-btn").addEventListener("click", () => {
  current = {
    id: null,
    name: "New Line",
    bullet: "?",
    color: "#0039A6",
    description: "",
    stations: [],
  };
  showEditor();
});

function showEditor() {
  $("#editor-empty").classList.add("hidden");
  $("#line-form").classList.remove("hidden");
  $("#f-name").value = current.name;
  $("#f-bullet").value = current.bullet;
  $("#f-color").value = current.color || "#0039A6";
  $("#f-description").value = current.description || "";
  renderStations();
  renderPreview();
  renderLinesList();
}

function renderPreview() {
  $("#preview-bullet").textContent = current.bullet || "?";
  $("#preview-bullet").style.setProperty("--c", current.color || "#0039A6");
  $("#preview-name").textContent = current.name || "Untitled";
  $("#preview-id").textContent = current.id || slugify(current.name);
}

// keep working copy + preview in sync as the user types
$("#f-name").addEventListener("input", (e) => { current.name = e.target.value; renderPreview(); });
$("#f-bullet").addEventListener("input", (e) => { current.bullet = e.target.value; renderPreview(); });
$("#f-color").addEventListener("input", (e) => { current.color = e.target.value; renderPreview(); renderDiagram(); });
$("#f-description").addEventListener("input", (e) => { current.description = e.target.value; });

// ---------- Stations ----------
function renderStations() {
  const ol = $("#stations-list");
  $("#station-count").textContent = `${current.stations.length} stop${current.stations.length === 1 ? "" : "s"}`;

  if (!current.stations.length) {
    ol.innerHTML = `<li class="empty">No stations yet — add one below.</li>`;
  } else {
    ol.innerHTML = current.stations
      .map(
        (s, i) => `
        <li class="station-item" draggable="true" data-index="${i}">
          <span class="grip" title="Drag to reorder">⠿</span>
          <span class="name">${escapeHtml(s.name)}</span>
          ${s.borough ? `<span class="borough">${escapeHtml(s.borough)}</span>` : ""}
          <button type="button" class="icon-btn up" title="Move up">▲</button>
          <button type="button" class="icon-btn down" title="Move down">▼</button>
          <button type="button" class="icon-btn del" title="Remove">✕</button>
        </li>`
      )
      .join("");
    wireStationButtons();
    wireDragAndDrop();
  }
  renderDiagram();
}

function wireStationButtons() {
  $$("#stations-list .station-item").forEach((li) => {
    const i = Number(li.dataset.index);
    li.querySelector(".del").addEventListener("click", () => {
      current.stations.splice(i, 1);
      renderStations();
    });
    li.querySelector(".up").addEventListener("click", () => move(i, i - 1));
    li.querySelector(".down").addEventListener("click", () => move(i, i + 1));
  });
}

function move(from, to) {
  if (to < 0 || to >= current.stations.length) return;
  const [s] = current.stations.splice(from, 1);
  current.stations.splice(to, 0, s);
  renderStations();
}

// Drag-and-drop reordering
let dragIndex = null;
function wireDragAndDrop() {
  $$("#stations-list .station-item").forEach((li) => {
    li.addEventListener("dragstart", () => {
      dragIndex = Number(li.dataset.index);
      li.classList.add("dragging");
    });
    li.addEventListener("dragend", () => li.classList.remove("dragging"));
    li.addEventListener("dragover", (e) => e.preventDefault());
    li.addEventListener("drop", (e) => {
      e.preventDefault();
      const dropIndex = Number(li.dataset.index);
      if (dragIndex !== null && dragIndex !== dropIndex) move(dragIndex, dropIndex);
      dragIndex = null;
    });
  });
}

$("#add-station-btn").addEventListener("click", () => {
  const name = $("#new-station-name").value.trim();
  const borough = $("#new-station-borough").value.trim();
  if (!name) { toast("Enter a station name first", true); return; }

  // build a unique station id within this line
  let id = slugify(name);
  const taken = new Set(current.stations.map((s) => s.id));
  let n = 2;
  while (taken.has(id)) id = `${slugify(name)}-${n++}`;

  current.stations.push({ id, name, borough: borough || null, x: null, y: null, notes: null });
  $("#new-station-name").value = "";
  $("#new-station-borough").value = "";
  renderStations();
});

// ---------- Route diagram ----------
function renderDiagram() {
  const wrap = $("#route-diagram");
  if (!current.stations.length) {
    wrap.innerHTML = `<span class="diagram-empty">Add stations to see your route map.</span>`;
    return;
  }
  const color = current.color || "#0039A6";
  wrap.innerHTML = current.stations
    .map(
      (s) => `
      <div class="diagram-stop" style="--line-color:${escapeHtml(color)}">
        <span class="dot"></span>
        <span class="label">${escapeHtml(s.name)}</span>
      </div>`
    )
    .join("");
}

// ---------- Save / Delete / Export ----------
$("#line-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = {
    name: current.name,
    bullet: current.bullet || "?",
    color: current.color || "#0039A6",
    description: current.description || "",
    stations: current.stations,
  };
  try {
    if (current.id) {
      await API.updateLine(current.id, body);
    } else {
      const created = await API.createLine(body);
      current.id = created.id;
    }
    await loadLines();
    renderPreview();
    renderLinesList();
    toast("Line saved ✓");
  } catch {
    toast("Could not save line", true);
  }
});

$("#delete-btn").addEventListener("click", async () => {
  if (!current.id) { resetEditor(); return; }
  if (!confirm(`Delete “${current.name}”? This can't be undone.`)) return;
  await API.deleteLine(current.id);
  current = null;
  await loadLines();
  resetEditor();
  toast("Line deleted");
});

function resetEditor() {
  $("#line-form").classList.add("hidden");
  $("#editor-empty").classList.remove("hidden");
  renderLinesList();
}

$("#export-btn").addEventListener("click", () => {
  const data = {
    id: current.id || slugify(current.name),
    name: current.name,
    bullet: current.bullet || "?",
    color: current.color || "#0039A6",
    description: current.description || "",
    stations: current.stations,
  };
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${data.id}.json`;
  a.click();
  URL.revokeObjectURL(url);
  toast("Exported JSON ✓");
});

// ============================================================
// Boot
// ============================================================
loadFeeds();
loadLines();
