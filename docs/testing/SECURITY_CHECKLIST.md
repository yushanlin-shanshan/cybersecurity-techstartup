# Security test checklist

Inspection date: 2026-10-12. Commit: `03c2599`.

A row is **Checked** only when the command was run and the result was read. **Not testable** means the relevant code does not exist, so the row is not a pass and not a confirmed vulnerability.

No application vulnerability was confirmed. The only completed security check is the secret scan of the tracked tree.

## Secrets and supply chain

| ID | Check | Status | Evidence |
| --- | --- | --- | --- |
| SEC-01 | Tracked files do not contain API keys, private keys, or tokens | Checked, none found | `rg` over the worktree excluding `.git` for `api_key`, `secret`, `password`, `token`, private-key headers, `sk-`, `AIza`, `ghp_`, and Slack-style tokens. No matches. The only tracked file at inspection was `README.md`. |
| SEC-02 | Frontend bundle does not embed provider keys | Not testable | No frontend, no build output. |
| SEC-03 | `.env` is gitignored before secrets are added | Partial | `.gitignore` now ignores `.env` and `.env.*` except `.env.example`. No `.env` file exists. |
| SEC-04 | `pip-audit` / `npm audit` | Not testable | No `requirements.txt`, `pyproject.toml`, `package.json`, or lockfile. |
| SEC-05 | Bandit, Semgrep, Ruff, ESLint | Not run as a product scan | `bandit` and `ruff` are not installed. There is no Python application to scan. Installing them to scan an empty tree would not show that the app is secure. |
| SEC-06 | Debug mode or default credentials | Not testable | No server configuration. |

## Input handling

| ID | Check | Status | Notes for when code exists |
| --- | --- | --- | --- |
| INP-01 | Malformed CSV and JSON rejected | Not testable | No parser. |
| INP-02 | Unexpected fields and types rejected or ignored | Not testable | No schema. |
| INP-03 | Oversized payload limit | Not testable | No endpoint. Add a limit before the demo if uploads are public. |
| INP-04 | Invalid ids and timestamps | Not testable | No parser. |
| INP-05 | CSV formula injection on export | Not testable | No export. Treat as required before any “download alerts” button. |
| INP-06 | Path traversal on saved uploads | Not testable | No file storage. |

## API and backend

| ID | Check | Status | Notes |
| --- | --- | --- | --- |
| API-01 | Authentication and authorization | Not testable | No accounts. A local hackathon demo can omit login if the README says it is single-user and local. Do not describe that as a multi-tenant control. |
| API-02 | Cross-tenant data access | Not testable | No tenant id. |
| API-03 | SQL injection | Not testable | No database and no SQL strings. |
| API-04 | Command injection | Not testable | No `subprocess`, `os.system`, or shell calls in the repository. The metric script uses `subprocess` only inside its own unit test to launch itself. |
| API-05 | Sensitive data in errors | Not testable | No API. |
| API-06 | Rate limits | Not testable | No endpoint. Low priority for a local demo. |
| API-07 | CORS and debug configuration | Not testable | No server. |
| API-08 | Unsafe file handling | Not testable | No uploads. |

## LLM and untrusted telemetry

| ID | Check | Status | Notes |
| --- | --- | --- | --- |
| LLM-01 | Prompt injection in a log line | Not testable | No model client. |
| LLM-02 | Attempts to extract secrets or other records | Not testable | No model client and no secret store. |
| LLM-03 | Malformed model output rejected | Not testable | No parser for model output. |
| LLM-04 | Model cannot change the server-side risk decision | Not testable | No risk decision. |
| LLM-05 | Model evidence must be a subset of the telemetry | Not testable | No explanation path. |
| LLM-06 | Model text is not executed as code, shell, SQL, or HTML | Not testable | No rendering and no tool runner. |
| LLM-07 | Agent tool misuse or self-granted permissions | Not applicable | No agent tools. Do not file a tool-use finding. |
| LLM-08 | Graceful behavior when the provider is down | Not testable | No provider call. |

## Confirmed findings

None in application code. See `BUG_REGISTER.md` for the demo blocker (no application) and the secret-scan observation.
