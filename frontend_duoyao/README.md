# sigsig

An English-language investigation interface driven by the Blue Team backend. Opening the page loads the last selected dataset, or the configured default. Users can upload new supported raw logs and switch datasets without entering service URLs.

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

This interface can save analyst reviews when enabled. It also uploads raw datasets when enabled. Status tracks workflow; assessment separately records whether activity is unassessed, suspicious, benign, or a confirmed threat. Dismissal does not automatically declare an event benign. Reviews are shared for the dataset, with the most recent saved edit taking effect. For uploaded datasets, paid LLM explanations require both backend enablement and the upload consent checkbox. The timeline displays representative evidence rather than every member record.

## Files

- `serve.py`: Local web server and same-origin investigation/review API gateway.
- `dist/index.html`, `dist/styles.css`: Interface structure and styling.
- `dist/app.js`: Automatic loading, filtering, pagination, and evidence display.
- `dist/datasets.js`: Dataset catalog, upload validation, and multipart requests.
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

## Upload a different dataset

1. Click **Upload dataset**, choose a file, and optionally give it a name.
2. Set the log year if timestamps omit their year.
3. Enable AI explanations only if you want event summaries and up to 12 evidence excerpts sent to OpenAI. This may incur API charges. Leaving it unchecked keeps processing on the backend.
4. Click **Upload and analyze**. The page shows analysis stages, then displays the new dataset.
5. Use **Dataset** to switch back. The choice is remembered in this browser; evidence and reviews are stored separately on the backend.

Supported inputs are Wazuh/AMiner or normalized alert records, one JSON object per line, in `.json`, `.jsonl`, or `.ndjson`, or a ZIP containing those files. Arbitrary JSON arrays and CSV require conversion. See [examples/upload-demo.jsonl](examples/upload-demo.jsonl) for a three-record synthetic example. Partial ingestion displays a rejected-record count; an invalid dataset shows a failure instead of replacing the old dataset.

Local uploads are enabled by default, with a 150 MB file cap (`MAX_UPLOAD_MB`). The backend's configured limit must also permit that size. Set `ENABLE_DATASET_UPLOADS=false` to hide uploads. On Netlify, enable `ENABLE_DATASET_UPLOADS=true` for Functions and redeploy; the gateway caps files at 4 MB. Upload-enabled deployments expose a shared dataset catalog to everyone who can access the site; this is not a private per-user workspace.

A static published snapshot can still be viewed, but cannot accept uploads, run analysis, or save reviews. Those features need the live Python backend and gateway.
