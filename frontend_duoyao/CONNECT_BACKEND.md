# Developer Setup

sigsig loads its configured dataset automatically. Backend configuration belongs to the deployment setup, not to the user interface.

## 1. Start the Blue Team backend

In `blue-team-backend`:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m backend.cli demo
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --workers 1
```

The backend's `demo` job contains the complete real `russellmitchell` scenario: 45,544 alerts grouped into 1,825 incidents. It is not fictional UI data.

Python 3.12.6 was used for integration verification. On Windows, use `.venv\Scripts\activate` and configure LLM settings in the backend `.env`.

## 2. Start the website

In `frontend_duoyao`:

```sh
python3 serve.py
```

Open http://127.0.0.1:5173. Events load automatically, including after a refresh.

`serve.py` serves static assets and forwards dataset uploads, investigation reads, and validated review updates to the backend. The browser uses its own origin, so this workflow requires no browser CORS configuration.

Optional operator configuration:

```sh
BACKEND_URL=http://127.0.0.1:8000 SIGNALDESK_JOB_ID=demo PORT=5174 python3 serve.py
```

These settings are for developers. The Upload dataset button accepts raw log files; there is no backend URL field or demo-reset action. Do not use `python -m http.server` for this version; it cannot serve the API gateway or application configuration.

## Data flow

```text
Browser → sigsig web server → Blue Team API → Stored analysis and evidence
```

The browser requests `/app-config.json` for the configured job ID, retrieves all incident-summary pages, and then loads details on selection. It displays 50 cards per page and supports up to 10,000 events per job. Larger jobs return an explicit limit error rather than being silently truncated.

Use the matching updated backend, which returns `benign_explanations` and `benign_assessment` in the explanation response. Backend errors or unavailable services produce a retry state; there is no fictional-data fallback.

## Current boundaries

- Multipart dataset uploads, job catalog and progress reads, incident reads, and analyst-feedback PATCH updates; no Q&A UI.
- Review filters and counts use actual backend statuses. Update status saves the workflow status, separate assessment, and note to the existing feedback endpoint. Editing can be disabled with `ENABLE_REVIEW_WRITES=false`.
- When the backend has `LLM_ENABLED=true` and a server-side `OPENAI_API_KEY`, event details include an LLM explanation only when the uploaded job has `allow_llm=true` (existing imported demo jobs retain their prior behavior). Successful results are cached server-side for 10 minutes. API credentials never enter the frontend.
- Possible normal explanations display AI hypotheses, verification steps, and links to related evidence. If generation fails or is disabled, the page clearly labels AI analysis as unavailable; no alternatives are invented.
- Representative evidence is labeled with its displayed count and total incident count.
- Citation membership is checked, but factual correctness and attack detection accuracy still require evaluation.
- This local gateway expects a backend without API-token authentication. Public hosting needs a separate authentication and deployment design.
- Both servers bind to the local computer. For the initial demo, run them on the same computer.

## Troubleshooting

- **Events unavailable:** Check the backend process, the configured job, and both terminal logs. Then click **Try again**.
- **Missing job:** Run `python -m backend.cli demo` or configure an existing ready job with `SIGNALDESK_JOB_ID`.
- **Port in use:** Stop the older static preview, or choose a different `PORT`.
- **Individual event fails:** Use its **Retry** action after restoring the service.

## Upload integration

`GET /app-config.json` returns `job_id`, `can_review`, `can_upload`, and `max_upload_bytes`. The browser lists `GET /api/v1/jobs`, posts multipart `file`, `dataset_name`, `syslog_year`, and `allow_llm` to `/api/v1/jobs`, and polls the returned job ID until ready or failed. A ready job uses the existing incident and evidence endpoints. Every upload creates a separate job; no existing evidence or review is overwritten.

Update the backend as well as the frontend: older backends do not honor per-dataset AI consent. The bundled OpenAPI schema and TypeScript client include the new fields.
