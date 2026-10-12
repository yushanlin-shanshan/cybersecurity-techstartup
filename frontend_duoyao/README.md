# sigsig

An English-language investigation interface driven by the Blue Team backend. Opening the page automatically loads the configured dataset. Users do not enter service URLs, import result files, or switch to fictional demo data.

## Run locally

Start the backend using its README, including `python -m backend.cli demo` to prepare the bundled real AIT scenario. Then run this from the frontend folder:

```sh
python3 serve.py
```

Open http://127.0.0.1:5173. Do not double-click `dist/index.html`: a file preview cannot load backend data and instead shows an Open sigsig link. On Windows, use `python` if needed.

Use `serve.py`, not a plain static HTTP server: it serves both the interface and the same-origin API gateway. No frontend dependency installation is needed. See `CONNECT_BACKEND.md` for the complete developer setup.

## Deploy on Netlify

See [DEPLOY_NETLIFY.md](DEPLOY_NETLIFY.md). The deployment needs the included Netlify function and a hosted Python backend with persistent data. Uploading `dist` alone will not load events.

## Behavior

- Automatically loads real event summaries on opening or refreshing the page.
- Displays counts calculated from loaded backend incident groups.
- Uses the backend's actual `new`, `investigating`, `resolved`, and `dismissed` review statuses. The Reviewed metric counts resolved and dismissed events.
- Lets reviewers update status, assessment, and notes using **Update status → Save review**. Changes are stored in the backend and survive refreshes. Any status can be reopened as New or Investigating.
- Provides search, priority/status filters, and pagination across the loaded queue.
- Loads representative original evidence and explanations when an event is selected.
- Preserves original records, source files, line references, and citations.
- Formats event summaries with paragraphs, headings, emphasis, and lists. Long explanations expand on demand without discarding any text.
- Exports a selected event as JSON.
- Shows a retry state if data cannot be loaded. Never substitutes fictional records or zero counts for a failed request.

This interface can save analyst reviews when enabled. It does not upload raw datasets. Status tracks workflow; assessment separately records whether activity is unassessed, suspicious, benign, or a confirmed threat. Dismissal does not automatically declare an event benign. Reviews are shared for the dataset, with the most recent saved edit taking effect. When enabled on the backend, opening an event generates a paid LLM explanation using bounded evidence excerpts. The timeline displays representative evidence rather than every member record.

## Files

- `serve.py`: Local web server and same-origin investigation/review API gateway.
- `dist/index.html`, `dist/styles.css`: Interface structure and styling.
- `dist/app.js`: Automatic loading, filtering, pagination, and evidence display.
- `dist/backend.js`: Adapter for the Blue Team API.
- `dist/schema.js`: Internal result validation.
- `dist/summary.js`: Escaped formatting for the supported summary Markdown subset.
- `CONNECT_BACKEND.md`: Developer service setup and integration limits.
- `BACKEND_CONTRACT.md`: Internal data mapping and export format.
- `tests/backend.test.js`: Adapter regression tests.
- `examples/demo-results.json`: Historical developer fixture only; not loaded or accessible through an import control in the application.

## Tests

```sh
node --test tests/*.test.js
```


## Review controls

**New** means waiting for review; **Investigating** means being checked; **Resolved** means the investigation and needed actions are complete; **Dismissed** means closed without further action (for example, a duplicate or expected activity). The status dropdown above the event list only filters events. Use **Update status** inside the event detail to edit it. Save failures keep the draft and do not change the displayed saved status. Cancel discards the draft. Switching tabs or events preserves drafts within the current page session; refreshing discards unsaved edits.

The local server enables writes by default; set `ENABLE_REVIEW_WRITES=false` to disable them. Netlify defaults to read-only until `ENABLE_REVIEW_WRITES=true` is set for Functions and redeployed. No user accounts or reviewer identity tracking are implemented. Everyone with access to an editing-enabled deployment can change the shared reviews. The backend records feedback history, but this version displays the latest review only.
