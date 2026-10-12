# SignalDesk Frontend

A local security alert investigation interface built with HTML, CSS, and vanilla JavaScript. No dependency installation is required. All interface text and project documentation are in English.

## Start locally

In VS Code, open the frontend folder (`frontend_duoyao` in the team repository, or `frontend` in the standalone package). Run this command from that folder:

```sh
python3 -m http.server 5173 --bind 127.0.0.1 --directory dist
```

Open http://localhost:5173 in your browser. On Windows, use `python` if `python3` is unavailable.

If port 5173 is already in use, replace it with 5174 and open http://localhost:5174.

Alternatively, from the root of the team repository:

```sh
python3 -m http.server 5174 --bind 127.0.0.1 --directory frontend_duoyao/dist
```

Do not open the HTML file by double-clicking it; JavaScript modules require an HTTP server.
No `npm install`, API key, external CDN, or external font is needed.

## Features

- Five clearly labeled fictional demo cases, not findings from the AIT dataset.
- Search, priority filtering, review-status filtering, and sorting by priority and score.
- Event timelines, assessments, and expandable original evidence.
- In-session review tracking and single-case JSON export.
- JSON file import or read-only loading from a backend endpoint.
- Data validation, error messages, empty states, and responsive layouts.

Refreshing the page restores the demo and resets review progress. There is no database or account system.
The frontend does not run detection or call a language model. The backend supplies analysis results.

## Backend collaboration

Share `BACKEND_CONTRACT.md` and `examples/demo-results.json` with the backend developer.
Start by having the backend produce a JSON file in the agreed format, then use **Import results**.
For the existing Blue Team backend, use **Connect backend → Blue Team API** with base URL `http://127.0.0.1:8000` and job ID `demo`. See `CONNECT_BACKEND.md` for startup and integration instructions. The adapter uses the existing API without requiring the backend to adopt the file-import format.

**Do not import raw Wazuh or AMiner JSON Lines files directly.** The frontend accepts investigation groups prepared by the backend.
Use `mode: "results"` for actual pipeline results and `mode: "demo"` for simulated examples.

## Project files

- `dist/index.html`: Page structure.
- `dist/styles.css`: Visual design and responsive styles.
- `dist/app.js`: Interactions, imports, and backend connection.
- `dist/data.js`: Separate fictional demo fixtures.
- `dist/schema.js`: Validation of imported and backend data.
- `dist/backend.js`: Read-only adapter for the Blue Team API.
- `CONNECT_BACKEND.md`: Startup, field mapping, and integration limits.
- `tests/backend.test.js`: Adapter regression tests.
- `examples/demo-results.json`: Complete example of the expected results format.
- `BACKEND_CONTRACT.md`: Backend integration specification.

This is a local development frontend and has not been published publicly. Teammates can copy the entire frontend folder to run it locally.
