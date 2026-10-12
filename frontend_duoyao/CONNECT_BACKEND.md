# Developer Setup

SignalDesk loads its configured dataset automatically. Backend configuration belongs to the deployment setup, not to the user interface.

## 1. Start the Blue Team backend

In `blue-team-backend`:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m backend.cli demo
LLM_ENABLED=false uvicorn backend.app:app --host 127.0.0.1 --port 8000 --workers 1
```

The backend's `demo` job contains the complete real `russellmitchell` scenario: 45,544 alerts grouped into 1,825 incidents. It is not fictional UI data.

Python 3.12.6 was used for integration verification. On Windows, use `.venv\Scripts\activate` and set `LLM_ENABLED=false` in the backend `.env` instead of the shell prefix above.

## 2. Start the website

In `frontend_duoyao`:

```sh
python3 serve.py
```

Open http://127.0.0.1:5173. Events load automatically, including after a refresh.

`serve.py` serves static assets and forwards read-only `/api/v1/` requests to the backend. The browser uses its own origin, so this workflow requires no browser CORS configuration.

Optional operator configuration:

```sh
BACKEND_URL=http://127.0.0.1:8000 SIGNALDESK_JOB_ID=demo PORT=5174 python3 serve.py
```

These settings are for developers. There is no URL field, results upload, or demo-reset action in the website. Do not use `python -m http.server` for this version; it cannot serve the API gateway or application configuration.

## Data flow

```text
Browser → SignalDesk web server → Blue Team API → Stored analysis and evidence
```

The browser requests `/app-config.json` for the configured job ID, retrieves all incident-summary pages, and then loads details on selection. It displays 50 cards per page and supports up to 10,000 events per job. Larger jobs return an explicit limit error rather than being silently truncated.

No backend code changes are required. Backend errors or unavailable services produce a retry state; there is no fictional-data fallback.

## Current boundaries

- Read-only API access; no raw-file uploads, Q&A calls, or analyst-feedback writes.
- Review filters and counts use actual backend statuses.
- Explanations come from the backend's local explanation endpoint. No paid LLM is called by this interface.
- Representative evidence is labeled with its displayed count and total incident count.
- Citation membership is checked, but factual correctness and attack detection accuracy still require evaluation.
- This local gateway expects a backend without API-token authentication. Public hosting needs a separate authentication and deployment design.
- Both servers bind to the local computer. For the initial demo, run them on the same computer.

## Troubleshooting

- **Events unavailable:** Check the backend process, the configured job, and both terminal logs. Then click **Try again**.
- **Missing job:** Run `python -m backend.cli demo` or configure an existing ready job with `SIGNALDESK_JOB_ID`.
- **Port in use:** Stop the older static preview, or choose a different `PORT`.
- **Individual event fails:** Use its **Retry** action after restoring the service.
