# SignalDesk Internal Data Contract · v1

The website automatically reads the Blue Team API through `dist/backend.js`. This document describes the internal normalized shape and single-event export format, not a user-facing upload requirement. The backend keeps its native API schema. See `CONNECT_BACKEND.md` for deployment setup.

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

## Limits and behavior

- Normalized results support at most 10,000 groups and 200 representative evidence records per group.
- `schema_version` must be 1. Invalid responses are rejected and surfaced as a loading error.
- Returned text is HTML-escaped. Log content is not treated as instructions or executable code.
- Do not use `labels.csv` or known attack time windows as inputs to inference scores. Keep evaluation separate from inference.
- The backend is responsible for preserving and interpreting AMiner's `TrainingMode` flag, missing fields, and source-field semantics.
- Severity values from different detectors must not be treated as a shared numerical scale without an explicit mapping.
- Review status is read from backend records. This UI does not write feedback. Single-case exports include `review_status`.
