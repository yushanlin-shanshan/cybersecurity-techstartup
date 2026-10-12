# Deploy sigsig on Netlify

The website uses two services:

```text
Browser → Netlify (frontend + upload/investigation/review function) → Hosted Python backend → Stored event data / OpenAI
```

Publishing `dist` alone uploads the visual interface. It does not run `serve.py`, FastAPI, the SQLite database, or the LLM integration. On the initial deployment, both `/app-config.json` and `/api/v1/jobs/demo` returned 404.

## 1. Put the Python backend online

Use a service that supports the included Dockerfile or a long-running Python process. Set the service root to `blue-team-backend`. Run one process and mount a persistent disk at `/data`.

Set these backend environment variables in the hosting dashboard:

| Variable | Value |
| --- | --- |
| `DATA_DIR` | `/data` (the persistent disk path) |
| `API_TOKEN` | A newly generated random secret shared only with the Netlify function |
| `LLM_ENABLED` | `true` for AI explanations; `false` to validate data loading first |
| `OPENAI_API_KEY` | Your existing key, only on the Python backend |
| `OPENAI_MODEL` | `gpt-4o-mini`, or your configured supported model |

Use this startup command from the backend directory; for Docker hosting, set it as the command override:

```sh
sh -c 'python -m backend.cli demo && exec uvicorn backend.app:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1'
```

The CLI loads the bundled real russellmitchell scenario if the `demo` job does not exist. It preserves an existing job. Initialization takes longer on the first start. The expected dataset has 45,544 alerts and 1,825 incidents. Wait for initialization and the service health check before using the frontend.

Obtain the service's public HTTPS URL. It must not be `localhost`, `127.0.0.1`, or a path on the Netlify frontend. Verify `<backend-url>/health` responds. Ensure the service has the latest backend changes for LLM benign explanations.

## 2. Configure Netlify

Deploy from the team's Git repository, including the functions. A manual drag-and-drop of `dist` is not sufficient for this setup.

For a deployment from the repository root, use the root `netlify.toml`:

| Setting | Value |
| --- | --- |
| Base directory | Repository root (leave blank) |
| Build command | None; this frontend is already plain HTML/CSS/JS |
| Publish directory | `frontend_duoyao/dist` |
| Functions directory | `frontend_duoyao/netlify/functions` |

If your Netlify base directory is intentionally `frontend_duoyao`, use the `netlify.toml` inside that folder instead, with `dist` and `netlify/functions` relative paths. Do not combine settings from the two layouts.

Add these environment variables in Netlify's UI and make them available to **Functions**, then redeploy:

| Variable | Value |
| --- | --- |
| `BACKEND_URL` | The public HTTPS URL from step 1 |
| `BACKEND_API_TOKEN` | Exactly the same secret as the backend's `API_TOKEN` |
| `SIGNALDESK_JOB_ID` | `demo` (legacy setting name, still supported) |
| `ENABLE_DATASET_UPLOADS` | `true` enables uploads and the shared dataset catalog; omitted/`false` disables uploads |
| `ENABLE_REVIEW_WRITES` | `true` to let site users edit shared reviews; omitted/`false` keeps the deployment review editing disabled |

Do not put either API key or the backend token in `dist`, frontend JavaScript, `app-config.json`, or Git. This function adds the backend token server-side. The browser continues to use its own website origin, so a browser CORS change is not needed for this gateway setup.

## 3. Verify the deployed site

1. Confirm Netlify lists the `backend-gateway` function in the deployed site's functions.
2. Open `https://sigsquared.netlify.app/app-config.json`. Expect a JSON object with `job_id: "demo"` and `can_review` matching your editing setting.
3. Open `https://sigsquared.netlify.app/api/v1/jobs/demo`. Expect a JSON job with `status: "ready"`.
4. Open the homepage. Expect 45,544 alerts and 1,825 events.
5. Select an event. Open **Why this matters** to see AI hypotheses when LLM mode is enabled.

If either route is 404, the function was not deployed or the wrong base/functions directory was used. A 503 names missing function settings. A 401 means the two backend tokens do not match. A backend 404 usually means the dataset was not seeded. A 502 can mean a stopped/sleeping backend or a request that exceeded the gateway timeout.

## Hosting boundaries

The gateway exposes investigation reads for the configured dataset and, when `ENABLE_REVIEW_WRITES=true`, validated PATCH requests to its feedback endpoint. With `ENABLE_DATASET_UPLOADS=true`, it also exposes multipart uploads and investigation reads for every dataset on this backend. It does not expose arbitrary Q&A. A secret backend token protects direct backend access; it does not authenticate visitors to the Netlify site. Anyone with access to the site can read exposed datasets and trigger permitted on-demand LLM explanations. If review editing is enabled, they can also modify the shared statuses, assessments, and notes. Configure site access appropriately before enabling writes; the application has no individual reviewer accounts. For a private team demo, configure hosting access protection before sharing; otherwise only serve the intended public synthetic dataset and account for API usage. No new public deployment or credential changes were made while preparing these files.

Netlify functions currently have a 60-second synchronous limit. The gateway stops waiting for the backend at 50 seconds. Ordinary Netlify proxy rewrites have a shorter 26-second limit, which is why this setup uses a function for LLM-backed event details. Persistent SQLite storage and dataset processing stay on the Python service.

References: [Function configuration](https://docs.netlify.com/build/functions/configuration/), [function environment variables](https://docs.netlify.com/build/functions/environment-variables/), [proxy limits](https://docs.netlify.com/manage/routing/redirects/rewrites-proxies/).

## Upload deployment checklist

- Deploy the updated Python backend, including the per-dataset `allow_llm` permission, before enabling uploads.
- Set `ENABLE_DATASET_UPLOADS=true` in Netlify Functions environment, then redeploy. `/app-config.json` should include `can_upload: true` and `max_upload_bytes: 4194304`.
- Upload `examples/upload-demo.jsonl` with AI unchecked. Confirm 3 alerts / 2 events, then switch back to the original dataset.
- The gateway accepts files up to **4 MB** to leave room for multipart encoding within the function request limit. The local app defaults to **150 MB**. Larger cloud uploads need a separate direct/object-storage upload flow, which is not implemented.
- Analysis continues on the Python service after the upload returns, and the browser polls progress. Use persistent backend storage.
- The team's `dist/app-config.json` + `api-static/results.json` export remains supported for static-only previews. That mode has no Upload dataset or review writes. With no backend settings or enabled write flags, the function returns the bundled read-only snapshot configuration. Once backend settings are provided, the function serves live configuration (Netlify custom function routes take precedence over static files by default). Enabling uploads without backend settings produces a setup error.
