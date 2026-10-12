# Permanent sigsig deployment

The Netlify site already serves v2.0. Its `/app-config.json` currently selects the published snapshot, so uploads and review writes are disabled. The missing component is the hosted Python service.

## Backend

Use the repository-root `render.yaml` as a Render Blueprint. It prepares one Docker web service, one worker process, and a persistent 1 GB disk at `/data`. The first start imports the bundled default dataset. Later starts preserve the database. This configuration uses paid Starter compute; review the price displayed by Render before creating resources. Memory requirements for larger datasets may require a larger compute plan.

The backend generates a private API token. Keep this value in hosting environment settings only. Never put it in browser JavaScript or commit it to Git.

Wait for `/health` to return HTTP 200. Record the actual public HTTPS service URL shown by Render. Do not infer the assigned subdomain from the service name.

## Netlify owner setup

Add the following environment variables with Functions scope, then redeploy:

- `BACKEND_URL`: the actual Render service HTTPS URL
- `BACKEND_API_TOKEN`: the generated Render `API_TOKEN`
- `SIGNALDESK_JOB_ID`: `demo`
- `ENABLE_DATASET_UPLOADS`: `true`
- `ENABLE_REVIEW_WRITES`: `true`

After deployment, `/app-config.json` must return `can_upload: true` and no `results_url`. The initial dataset should show 45,544 alerts and 1,825 events. Upload `frontend_duoyao/examples/upload-demo.jsonl` with AI unchecked, confirm 3 alerts / 2 events, update a review, refresh, and switch back to the default dataset.

All visitors with site access share datasets and review state. Use synthetic public demonstration data or restrict site access before uploading company logs.

## Optional AI

The blueprint starts with `LLM_ENABLED=false` so initial deployment verification does not send data to a model provider or generate API charges. To enable AI, add `OPENAI_API_KEY` as a secret on Render, set `LLM_ENABLED=true`, and set `OPENAI_MODEL` to the model approved for the project. Uploads still require per-dataset AI consent. Secrets belong on Render, never on the frontend or in this document.

## Limits

This starter deployment accepts 4 MB uploads with at most 64 MB expanded ZIP content and 100,000 alerts. Netlify's gateway also caps files at 4 MB. Uploads and reviews persist on the attached disk. Monitor disk usage and resource usage as datasets accumulate.

References: https://render.com/docs/blueprint-spec and https://render.com/docs/disks
