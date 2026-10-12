# SignalDesk

An English-language investigation interface driven by the Blue Team backend. Opening the page automatically loads the configured dataset. Users do not enter service URLs, import result files, or switch to fictional demo data.

## Run locally

Start the backend using its README, including `python -m backend.cli demo` to prepare the bundled real AIT scenario. Then run this from the frontend folder:

```sh
python3 serve.py
```

Open http://127.0.0.1:5173. On Windows, use `python` if needed.

Use `serve.py`, not a plain static HTTP server: it serves both the interface and the same-origin API gateway. No frontend dependency installation is needed. See `CONNECT_BACKEND.md` for the complete developer setup.

## Behavior

- Automatically loads real event summaries on opening or refreshing the page.
- Displays counts calculated from loaded backend incident groups.
- Uses the backend's actual `new`, `investigating`, `resolved`, and `dismissed` review statuses. The Reviewed metric counts resolved and dismissed events.
- Provides search, priority/status filters, and pagination across the loaded queue.
- Loads representative original evidence and explanations when an event is selected.
- Preserves original records, source files, line references, and citations.
- Exports a selected event as JSON.
- Shows a retry state if data cannot be loaded. Never substitutes fictional records or zero counts for a failed request.

This interface is read-only. It does not change backend review status, upload raw datasets, or invoke paid language models. The timeline displays representative evidence rather than every member record.

## Files

- `serve.py`: Local web server and read-only same-origin API gateway.
- `dist/index.html`, `dist/styles.css`: Interface structure and styling.
- `dist/app.js`: Automatic loading, filtering, pagination, and evidence display.
- `dist/backend.js`: Adapter for the Blue Team API.
- `dist/schema.js`: Internal result validation.
- `CONNECT_BACKEND.md`: Developer service setup and integration limits.
- `BACKEND_CONTRACT.md`: Internal data mapping and export format.
- `tests/backend.test.js`: Adapter regression tests.
- `examples/demo-results.json`: Historical developer fixture only; not loaded or accessible through an import control in the application.

## Tests

```sh
node --test tests/backend.test.js
```
