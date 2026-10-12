# SignalDesk Backend Contract · v1

This document describes the standalone JSON import format. The existing Blue Team API is supported through `dist/backend.js`; see `CONNECT_BACKEND.md`. The backend does not need to change its native response schema.

## Easiest integration path

Generate a JSON file for the frontend to import. A live HTTP endpoint is not required for the first integration.
See `examples/demo-results.json` for a complete example. Do not send raw JSON Lines.

```json
{
  "schema_version": 1,
  "mode": "results",
  "dataset": {"name": "russellmitchell", "description": "Wazuh + AMiner grouped alerts"},
  "incidents": []
}
```

An empty `incidents` array is valid and displays an empty state. Simulated data must use `mode: "demo"`.

## Incident fields (all required)

| Field | Type / meaning |
| --- | --- |
| `id` | Unique non-empty string |
| `title` | Short descriptive title |
| `priority` | `high`, `medium`, or `low` |
| `score` | Finite number, 0–100; review priority, NOT attack probability |
| `entity` | Display identifier for reporting host/entity; use `Unknown` if absent |
| `start`, `end` | ISO 8601 timestamps with timezone; end >= start |
| `alert_count` | Positive integer; number of original alerts represented by this group |
| `sources` | Array of strings, e.g. `["Wazuh", "AMiner"]` |
| `summary` | Evidence-grounded summary string |
| `reasons` | Array of strings explaining priority |
| `benign_explanations` | Array of possible normal explanations |
| `missing_context` | Array of uncertainties/missing information |
| `next_steps` | Array of investigation suggestions, not executed actions |
| `evidence` | Array of evidence objects, below |

Arrays may be empty. Do not invent missing facts.
The overview alert count is the sum of `alert_count` across all groups, **not an automatically deduplicated dataset total**.
Prefer assigning each original alert to only one group. A group's evidence may include only representative records; the interface displays the evidence count separately.

## Evidence

```json
{
  "id": "russellmitchell_wazuh.json:137",
  "timestamp": "2022-01-21T05:24:07.306756Z",
  "title": "Use actual detector description",
  "description": "Optional evidence-grounded description",
  "source": "Wazuh",
  "raw": {"original_json_record": "Replace this placeholder with the complete original object"}
}
```

Required fields: `id`, `timestamp`, `title`, and `raw`. Store the original record object directly in `raw`; the example above only illustrates the structure.
Evidence IDs must be unique within each group. Use the original filename plus its one-based line number as a stable evidence ID.
All displayed times use UTC. Preserve event timestamps rather than substituting the report generation time.

## Optional HTTP endpoint

`GET http://localhost:8000/api/incidents` returns the complete results object with `Content-Type: application/json`.
The frontend requests the user-provided URL directly. It omits credentials, performs no write operations, and uses a 15-second timeout.

The backend must allow the frontend's actual origin through CORS. Examples include `http://localhost:5173`, `http://127.0.0.1:5173`, or the corresponding origin on port 5174. These are distinct origins.
Allow only the local development origins you need. When teammates use different computers, `localhost` refers to each person's own computer. Exchanging a results JSON file is the simplest initial integration.

## Limits and behavior

- JSON files are limited to 10 MB, with at most 10,000 groups and 200 displayed evidence records per group.
- `schema_version` must be 1. Invalid data is rejected without replacing the currently displayed results.
- Imported text is HTML-escaped. Log content is not treated as instructions or executable code.
- Do not use `labels.csv` or known attack time windows as inputs to inference scores. Keep evaluation separate from inference.
- The backend is responsible for preserving and interpreting AMiner's `TrainingMode` flag, missing fields, and source-field semantics.
- Severity values from different detectors must not be treated as a shared numerical scale without an explicit mapping.
- Review marks last only for the current page session. Refreshing or importing results resets them. Single-case exports include `review_status`.
