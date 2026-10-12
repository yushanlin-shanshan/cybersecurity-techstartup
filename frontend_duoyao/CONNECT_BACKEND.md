# Connect SignalDesk to the Blue Team Backend

## What is integrated

The frontend now understands the existing Blue Team `/api/v1` endpoints. The backend does not need to change its response format.

- Retrieves every incident-list page, including dismissed incidents, up to a 10,000-event browser limit.
- Searches and filters across all loaded incident summaries, with 50 events displayed per page.
- Retrieves explanations and representative original records only when an event is selected.
- Shows the backend's final priority score and priority band, not the separate rule-only score.
- Preserves raw evidence, evidence IDs, original filenames, line references, and event times.
- Shows backend review status separately from local review marks.
- Retains SignalDesk JSON file import and the fictional UI demo.

## Start the backend

In a terminal inside `blue-team-backend`:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m backend.cli demo
CORS_ORIGINS='http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174' LLM_ENABLED=false uvicorn backend.app:app --host 127.0.0.1 --port 8000 --workers 1
```

The integration was verified with Python 3.12.6 and the backend's pinned dependencies. The backend README also documents Python 3.13. On Windows, activate `.venv\Scripts\activate` and set `CORS_ORIGINS` and `LLM_ENABLED` in the backend's `.env` instead of using the shell environment prefix above.

The `demo` command loads the bundled real `russellmitchell` scenario. Its job ID is `demo`; this name does **not** mean the records are fictional. The separate frontend **Reset demo** button does restore fictional UI examples.

## Start the frontend

In a second terminal inside `frontend_duoyao`:

```sh
python3 -m http.server 5173 --bind 127.0.0.1 --directory dist
```

Open http://127.0.0.1:5173. If the port is already occupied by this preview, use the existing page. Otherwise use port 5174.

1. Click **Connect backend**.
2. Select **Blue Team API**.
3. Enter `http://127.0.0.1:8000` as the backend URL.
4. Enter `demo` as the job ID.
5. Click **Load results**.

Expected result for the bundled scenario: **45,544 alerts and 1,825 events**, with a **BACKEND CONNECTED** badge.
Refreshing returns to fictional UI examples; reconnect to restore backend results. The connection address and data are not persisted in browser storage.

## Response mapping

| Blue Team field | Frontend field |
| --- | --- |
| `priority_band` | `priority` (`high`, `medium`, `low`) |
| `priority` | `score` (final review priority) |
| `count` | `alert_count` |
| `anchor[1:]` | `entity` |
| `sensors` | `sources` |
| `explanation.answer` | `summary` |
| `explanation.claims` | `reasons`, retaining citation IDs |
| `explanation.caveats` | `missing_context` |
| `representative_evidence[].original_record` | `evidence[].raw` |
| `normalized.time` | UTC ISO timestamp |
| `normalized.source` and `normalized.line` | Original file and line reference |

The backend does not provide a separate benign-explanations field for this response. The UI leaves it empty rather than inventing an explanation.

## Current boundaries

This connection is read-only. It does not upload raw datasets, call the Q&A endpoint, enable a paid LLM, or write analyst feedback. The backend supports some of those operations, but they are not wired into this UI yet.

The timeline contains **representative evidence**, not every member record. The interface explicitly shows the displayed count and the full incident alert count. Complete membership remains available through the backend's paginated evidence endpoint.

Backend explanations and scores are not independently validated by the frontend. Citation membership is checked; this does not establish the correctness of every claim.

The current connector expects a local backend without an `API_TOKEN`. A backend requiring authentication returns a clear error. Do not put API keys or shared tokens into frontend source code.

## Troubleshooting

- **Failed to fetch:** Confirm the backend is running and CORS allows the exact frontend origin. `localhost` and `127.0.0.1` are different origins.
- **Job not found:** Run `python -m backend.cli demo`, or enter an existing ready job ID.
- **Job running/failed:** Wait for processing or inspect the backend job response.
- **Unable to load an event:** Click **Retry** after fixing the connection. The event is not replaced with made-up evidence.
- **Wrong backend:** Enter the base URL, not the full `/api/v1/jobs/.../incidents` route.
- **Different computers:** `localhost` points to the computer running the browser. Run both services on the same computer for initial integration.

## Verification

Run adapter regression tests from the frontend folder:

```sh
node --test tests/backend.test.js
```

The integration was checked against the live backend for all 1,825 summaries and 45,544 represented alerts, plus original evidence and explanations for high-, medium-, and low-priority incidents. Browser CORS, pagination, filtering, and evidence display were checked. These are integration checks, not attack-detection accuracy measurements.
