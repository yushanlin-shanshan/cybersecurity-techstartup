# Blue Team Incident Backend

A website-ready backend for **Track 2: Detect — AI-Powered Blue Team**. It ingests the AIT alert dataset, groups related records into investigation incidents, ranks them with transparent rules plus real local ML, and explains incidents with citations to the original evidence. It also supports analyst review and an optional LLM Q&A mode.

**No LLM API key is needed for the default demo.** Python 3.13 is the tested runtime. A complete real scenario is included, so the demo runs without downloading the full dataset.

## Start in five commands

Open a terminal in this folder:

```sh
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m backend.cli demo
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --workers 1
```

On Windows, use `py -3.13 -m venv .venv` and `.venv\Scripts\activate` for the first two steps.

Open **http://localhost:8000/docs** for the interactive API explorer. `GET /api/v1/jobs/demo/incidents` returns the preloaded incident queue. The demo contains all **45,544 real alerts** from `russellmitchell`, grouped into **1,825 incidents**, with an Isolation Forest trained on those groups. The raw record payloads and their original file/line references are preserved.

To test ingestion instead of using precomputed groups, upload `demo/raw-alerts.zip` in the API explorer's `POST /api/v1/jobs`, or run:

```sh
curl -X POST http://localhost:8000/api/v1/jobs \
  -F 'file=@demo/raw-alerts.zip'
```

This returns `202` with a job ID. Poll `GET /api/v1/jobs/JOB_ID` until `status` is `ready`, then query `/api/v1/jobs/JOB_ID/incidents`. Failures are reported as `status=failed` with an error; querying incidents before a job is ready returns `409`.

## Connect the existing website

Copy **`frontend-client.ts`** into your frontend. It has typed helpers for upload, job polling, incident lists, evidence, related incidents, Q&A, and analyst feedback. It uses browser `fetch` and requires no additional frontend packages.

```ts
import { BlueTeamAPI } from './frontend-client';

const api = new BlueTeamAPI('http://localhost:8000');

// Ready-to-use demo queue:
const queue = await api.incidents('demo', { limit: 20 });
const detail = await api.incident('demo', queue.items[0].id);
console.log(detail.explanation.answer);
console.log(detail.explanation.claims); // each claim includes evidence_ids

// Real ingestion from a file picker:
const job = await api.upload(file);
await api.waitForJob(job.id);
const incidents = await api.incidents(job.id);

// Incident-specific Q&A; local mode by default:
const answer = await api.ask(job.id, incidents.items[0].id,
  'Why is this ranked highly?');
```

The local backend allows `http://localhost:3000` and `http://localhost:5173`. To connect your Netlify website, copy `.env.example` to `.env` and set the exact frontend origin:

```dotenv
CORS_ORIGINS=https://your-team.netlify.app,http://localhost:5173
```

Restart the backend after changing `.env`. Configure your frontend's API base URL to the backend's public **HTTPS** URL when you deploy it. For Vite, a public `VITE_API_BASE_URL` is appropriate; it contains the service URL, not an API key.

Long imports and SQLite storage expect a persistent backend process and writable disk. Run this API as a separate service and let the Netlify frontend call it. This package does not change or deploy your existing website.

Suggested UI: an incident table displaying priority, source/host, alert count, detector names, stage indicators and analyst status; an incident drawer displaying summary, score breakdown, timeline, citations and related suggestions; an incident chat box; and a review action to mark investigating, resolved, or dismissed. Render descriptions, raw logs, and model output as plain text, not raw HTML.

## API routes

All data routes are under `/api/v1`. IDs are scoped to their job; evidence IDs must be used with the same job and incident.

| Method | Route | Purpose |
|---|---|---|
| GET | `/health` | Health, model tooling and LLM availability |
| GET | `/jobs` | Available datasets and processing jobs |
| POST | `/jobs` | Multipart file upload and asynchronous processing |
| POST | `/jobs/batch` | JSON batch of up to 50,000 records |
| GET | `/jobs/{job}` | State, phase, accepted/rejected counts and errors |
| GET | `/jobs/{job}/stats` | Incident counts by scenario, priority and analyst state |
| GET | `/jobs/{job}/incidents` | Ranked, paginated investigation queue |
| GET | `/jobs/{job}/incidents/{id}` | Incident details, automatic LLM explanation when enabled, and representative original records |
| GET | `/jobs/{job}/incidents/{id}/evidence` | All member records, paginated and ordered by event time |
| GET | `/jobs/{job}/incidents/{id}/related` | TF-IDF related-incident suggestions with entity/time support |
| POST | `/jobs/{job}/incidents/{id}/ask` | Incident-specific questions or explanation; local or opt-in LLM |
| PATCH | `/jobs/{job}/incidents/{id}/feedback` | Persist analyst status, disposition and review note |

Queue query parameters: `limit` (1–200), `offset`, `scenario`, `band` (`high`, `medium`, `low`), `status`, `search` (IP/host/description), `min_priority`, and `include_dismissed`. The default queue excludes dismissed incidents. Individual incident/evidence routes retain access to dismissed records. Related suggestions are contextual and can include reviewed incidents; they do not automatically merge groups or confirm a shared attacker.

Upload options, as multipart fields or JSON batch fields:

| Field | Default | Meaning |
|---|---:|---|
| `scenario` | all | Read filenames matching one AIT scenario |
| `gap_minutes` | 15 | Maximum idle time in a group |
| `max_span_minutes` | 60 | Maximum group duration |
| `syslog_year` | 2022 | Year for yearless syslog timestamps |
| `limit` | 0 | Explicit input-prefix limit; 0 reads all |

A prefix-limited run is flagged as `partial_input` and computes ML/ranking only from that prefix. It is not equivalent to analyzing the complete dataset.

Example Q&A body:

```json
{"question": "Could this be a false positive?", "use_llm": false}
```

Example analyst feedback body:

```json
{"status": "dismissed", "disposition": "benign", "note": "Matched an authorized scan."}
```

Allowed statuses: `new`, `investigating`, `resolved`, `dismissed`. Dispositions: `unreviewed`, `suspicious`, `benign`, `confirmed`. Feedback is stored with an audit history. It does not retrain the unsupervised model or alter the original evidence. Queue reduction comes from grouping and explicit analyst dismissal; measured false-positive reduction is not claimed.

## Supported inputs

- AIT-ADS ZIP files and extracted JSONL files: Wazuh, embedded Suricata, and AMiner.
- Elasticsearch-style `_source` wrappers.
- Canonical custom JSONL records or JSON batch records:

```json
{
  "timestamp": "2022-01-21T03:00:00Z",
  "source_ip": "10.0.0.5",
  "destination_ip": "10.0.0.9",
  "host": "web-server-1",
  "sensor": "endpoint",
  "severity": 12,
  "rule_id": "remote-execution",
  "description": "Remote command execution detected",
  "raw_log": "Original log evidence"
}
```

`timestamp` must be parseable; `severity` is normalized on a 0–15 scale. Use IP addresses in source/destination fields and put hostnames in `host`. Canonical input must have `description`. Include enough host/source identity to support correlation. A JSONL file contains one JSON object per line; JSON arrays, arbitrary text reports, PDF and CSV are not accepted. AIT's `.json` files are JSONL despite their extension.

Malformed records are counted and written to the job's `rejected.jsonl`. A job with no accepted records fails. Records over 8 MB, more than `MAX_ALERTS`, encrypted archives, or oversized expanded archives fail the job instead of silently dropping the remainder. ZIP entries are streamed, never extracted to user-controlled paths. Default upload limit: 150 MB; expanded archive limit: 6 GiB; alert limit: 3 million. There is one processing worker and at most four queued/running jobs. Upload request bodies are bounded before multipart parsing, including chunked requests.

CLI tools:

```sh
# Run the raw included scenario without HTTP:
python -m backend.cli analyze demo/raw-alerts.zip

# Process the user-provided full dataset archive:
python -m backend.cli analyze /path/to/ait_ads.zip

# Analyze only one scenario:
python -m backend.cli analyze /path/to/ait_ads.zip --scenario fox

# Reuse an output folder produced by the previous Alert Investigator:
python -m backend.cli import-results /path/to/alert-investigator/full-run
```

Dataset download: [AIT Alert Data Set on Zenodo](https://zenodo.org/records/8263181). The full archive is approximately 96 MB; database outputs require several GB of disk space. The demo's ZIP repackages the retained original record payloads of one complete scenario, rather than preserving the byte formatting of the upstream archive.

## How the AI pipeline works

**Normalize and correlate.** Prefer event timestamps over collection times, preserve each original record, and isolate scenarios. Group alerts by source IP and event-time sessions. For records without a source IP, use host plus signature; fall back to signature alone if both are unavailable. Source IPs can be extracted from structured fields, Apache access logs or a `from IP` phrase. Default idle gap is 15 minutes and maximum session duration is one hour. A shared anchor/time window is a correlation hypothesis, not evidence of causality.

**Transparent baseline.** The original 0–100 rule score combines maximum detector severity (40 points), description-stage diversity (20), detector diversity (10), signature rarity (15), alert volume (10) and structured destination breadth (5). Stage indicators are pattern matches against descriptions; they do not establish attack success. Wazuh levels are clamped to 0–15; Suricata priorities 1/2/3 map to 12/8/4; AMiner uses level 3 by default. Repeated alerts are preserved, including multiple detectors reporting one event.

**Local ML.** Train a deterministic [Isolation Forest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html) separately within each scenario, with 150 trees and random seed 42. Features are alert count, maximum severity, distinct stages, sensors, hosts, destinations, duration, signature count, signature rarity and alert rate. Count, duration and rate are log transformed before fitting. No attack labels are used. Convert anomaly scores to within-scenario percentiles using mid-ranks for ties. Fewer than 20 groups means rule-only ranking. Scores and metadata persist; each new batch fits its own model rather than using an independently trained benign baseline.

```text
priority = 0.8 × rule_score + 0.2 × anomaly_percentile
high: >=70      medium: >=40 and <70      low: <40
```

The UI receives both contributions and the underlying rule components. ML feature context compares observed values to batch medians; it is descriptive context, not a causal attribution to the forest. A high anomaly percentile means unusual relative to the uploaded scenario, not malicious. Percentiles from different datasets are not directly calibrated.

**Text similarity.** TF-IDF with word unigrams/bigrams and cosine similarity finds other incidents with similar alert descriptions. Suggestions must also share an anchor, host, or destination, stay within the same scenario, and have at most a one-hour gap. They remain separate groups for analyst review. This is NLP-assisted retrieval, not learned attack-chain clustering.

**Explain and review.** Local mode produces factual group summaries, ranking explanations, timeline bounds, recommended checks, and false-positive review guidance with record IDs. It has limited question intents and abstains on unsupported questions. Counts/score statistics describe all group members; selected citations are representative. Complete membership is available through the evidence endpoint. No automatic containment or remediation is performed.

The model and correlation rules are a hackathon baseline. Shared NAT/proxy IPs can merge unrelated activity, changed IPs or long pauses can split an attack, missing identities weaken relationships, and benign high-volume/rare events can rank highly. Attack detection accuracy and false-positive reduction need separate held-out evaluation before claiming those results.

## Optional LLM integration

For broader incident questions and more fluent explanations, put an **OpenAI API key in the backend's `.env`**:

```dotenv
LLM_ENABLED=true
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o-mini
```

Restart the backend. Opening an incident now automatically requests an LLM explanation when `LLM_ENABLED=true`. Successful detail explanations are cached in memory for 10 minutes (up to 128 entries); changed incident/evidence inputs invalidate the cache. Generation is on demand, never across the whole queue. Each `benign_explanations` item contains `text`, `evidence_ids`, and `verification`; `benign_assessment` states uncertainty. An empty list is permitted when no defensible alternative is supported.

The Q&A endpoint still requires `use_llm: true`, for example:

```ts
const answer = await api.ask(jobId, incidentId,
  'Explain the suspicious activity and what evidence is still missing.', true);
```

The provider uses the [OpenAI Responses API with Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses). It sends the group statistics and up to 12 selected, bounded evidence excerpts. Raw records are treated as untrusted data; common credential assignments are redacted from excerpts, but this is not exhaustive secret detection. The complete dataset is never sent. `store` is set to `false`. Citation IDs are schema-constrained and checked against the supplied evidence; this verifies citation membership, not factual entailment of every statement. Analyst review remains necessary.

Missing keys, provider errors, incomplete responses and invalid citations fall back to local explanations with an explicit `fallback_reason`. Detail requests follow the server LLM setting; Q&A requires request opt-in as well. **Never put this API key in Netlify frontend environment variables, browser code, or Git.** Regression tests use mocked provider responses, including invalid benign-hypothesis citations and rate limits.

## Deployment and storage

A Dockerfile is included; Docker was not installed in the development environment, so the image build was not exercised.

```sh
docker build -t blue-team-backend .
docker run --rm -p 8000:8000 --env-file .env -v blue-team-data:/data blue-team-backend
# In another terminal, seed the running container using its container ID:
docker exec CONTAINER_ID python -m backend.cli demo
```

Run **one Uvicorn process**. The in-process queue is deliberately a prototype, not a distributed task queue. Restarting the service marks unfinished imports as failed; upload again. Completed jobs and analyst feedback survive restarts. Mount persistent storage for `DATA_DIR`; ephemeral/serverless disks do not preserve the queue or evidence database. Use a public HTTPS endpoint for your hosted frontend. `.env` and runtime databases are excluded from Docker's build context and should not be committed.

For a private team demo, set `API_TOKEN` and send `Authorization: Bearer TOKEN` on data routes. CORS is an origin policy, not authentication. The shared token is a demo gate; do not hard-code a long-lived shared token into a public frontend build. Public multi-user hosting needs user authentication/authorization, retention and a durable background queue, which are not implemented here.

## Verification

```sh
pip install -r requirements-dev.txt
python -m pytest -q
```

Nine tests cover API ingestion and evidence retrieval, original-record preservation, malformed records, scenario isolation, persisted review feedback, auth/CORS and body limits, reproducible anomaly scoring/tie handling, TF-IDF entity/time constraints, and optional LLM citation validation/fallback.

The live API was checked with the complete scenario's **45,544 raw records**, producing **1,825 incidents with zero rejected records**, and with the earlier full dataset's **2,655,821 original records and 26,757 groups** imported for ML ranking across all eight scenarios. Actual HTTP requests exercised ranking, detail, evidence-backed Q&A, and related suggestions. The TypeScript client passed strict compilation. These validate implementation and data handling, not attack-detection accuracy.

## Files

- `backend/app.py`: HTTP routes, authentication, CORS, limits, processing queue.
- `backend/pipeline.py` and `backend/legacy_pipeline.py`: ingestion, normalization and evidence-preserving grouping.
- `backend/ml.py`: Isolation Forest ranking and TF-IDF retrieval.
- `backend/explain.py`: local explanations and opt-in LLM synthesis.
- `backend/store.py`: jobs, incident index, evidence access and review history.
- `frontend-client.ts`: typed frontend integration helper.
- `demo/`: complete real scenario evidence, groups and upload ZIP.
- `.env.example`, `Dockerfile`, `openapi.json`: configuration, deployment and API contract.

Dataset attribution: Max Landauer, Florian Skopik and Markus Wurzenberger, *AIT Alert Data Set*, Zenodo, DOI [10.5281/zenodo.8263181](https://doi.org/10.5281/zenodo.8263181). See the [authors' repository](https://github.com/ait-aecid/alert-data-set) for the dataset's original analysis methodology.
