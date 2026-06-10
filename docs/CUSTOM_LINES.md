# Custom Subway Lines

Custom lines are how you "make your own subway line." They're stored as plain
JSON in `data/custom_lines.json` and edited through the **Line Builder** tab or
the `/api/custom-lines` endpoints.

---

## The JSON schema

A line looks like this:

```json
{
  "id": "sunset-express",
  "name": "Sunset Express",
  "bullet": "S",
  "color": "#FF6B35",
  "description": "A scenic coastal line that only runs at golden hour.",
  "stations": [
    {
      "id": "pier-1",
      "name": "Pier One",
      "borough": "Brooklyn",
      "x": null,
      "y": null,
      "notes": null
    }
  ]
}
```

### Line fields

| Field         | Type   | Required | Description |
| ------------- | ------ | -------- | ----------- |
| `id`          | string | yes\*    | Unique url-friendly slug. Auto-generated from `name` if you don't supply it on create. |
| `name`        | string | yes      | Display name, e.g. `Sunset Express`. |
| `bullet`      | string | no       | Short label shown in the colored circle, e.g. `S`. Defaults to `?`. 1–3 chars works best. |
| `color`       | string | no       | Hex route color, e.g. `#FF6B35`. Defaults to `#0039A6` (MTA navy). |
| `description` | string | no       | Free-form text. Defaults to `""`. |
| `stations`    | array  | no       | Ordered list of station objects (see below). Order **is** the route order. |

\* `id` is required in the stored file, but optional in the **create** request —
the server generates a unique one for you.

### Station fields

| Field     | Type            | Required | Description |
| --------- | --------------- | -------- | ----------- |
| `id`      | string          | yes      | Unique **within the line**. The UI slugifies the name for you. |
| `name`    | string          | yes      | Display name, e.g. `Pier One`. |
| `borough` | string \| null  | no       | Optional area/borough label. |
| `x`       | number \| null  | no       | Optional map x-coordinate (for future 2D map features). |
| `y`       | number \| null  | no       | Optional map y-coordinate. |
| `notes`   | string \| null  | no       | Optional free-form notes. |

Station **order in the array is the route order**. Reordering in the UI (drag
the `⠿` handle, or ▲/▼) just rearranges this array.

---

## Examples

### Minimal line (server fills in the rest)

`POST /api/custom-lines`
```json
{ "name": "Cloud Line" }
```
Result: `id` becomes `cloud-line`, `bullet` `?`, `color` `#0039A6`, empty stations.

### Full line

```json
{
  "id": "cloud-line",
  "name": "Cloud Line",
  "bullet": "C",
  "color": "#6C5CE7",
  "description": "An imaginary sky tram connecting floating neighborhoods.",
  "stations": [
    { "id": "nimbus",  "name": "Nimbus Heights" },
    { "id": "cumulus", "name": "Cumulus Center" },
    { "id": "stratus", "name": "Stratus Yard" }
  ]
}
```

---

## Export & import behavior

### Export
- In the UI, click **Export JSON** on any line. Your browser downloads
  `<line-id>.json` containing the full line object above.
- This is a standalone snapshot — perfect for sharing or version control.

### Import
There are two simple ways to bring a line back in:

1. **Via the API:** `POST` the exported JSON to `/api/custom-lines`. If the
   `id` already exists you'll get a `409` — either delete the old one first or
   change the `id`.
2. **Via the file:** paste the object into the array in
   `data/custom_lines.json` and restart the app. The file is a top-level JSON
   **array** of line objects.

> A UI "Import" button is on the [roadmap](../README.md#-roadmap-ideas) — PRs welcome!

---

## Storage notes

- The file is created automatically (with two sample lines) the first time the
  app reads it, so a fresh clone is never empty.
- Saving through the UI or API rewrites the whole file with pretty-printed JSON.
- Because it's just a file, you can hand-edit it — but keep it valid JSON, and
  keep `id` values unique (both line ids, and station ids within a line).
