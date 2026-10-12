# Testing baseline

Date: 2026-10-12. Inspection scope: workspace branch `cursor/testing-baseline-report-c048` at `586133a`, compared with `origin/main` at `757958f`. No application code was changed for this report.

Labels used below:

- **Confirmed:** observed from a file, command, or HTTP response in this pass.
- **Potential:** a risk that depends on code which is not in the tree yet.
- **Assumption:** not established by the repository.

## Repository architecture

There is no running application. `origin/main` and this branch both contain `backend/detection.py` and `backend/preprocessing.py` as 0-byte files. This branch adds a Python testing harness around those empty files.

| Area | Confirmed state |
| --- | --- |
| Frontend | No `package.json`, `tsconfig.json`, React, or Next.js app. |
| Backend API | No server module, no FastAPI/Flask code, no route. |
| Detection logic | `backend/detection.py` is empty. `testing/reference_rule.py` is a harness oracle with `detect()`, not the product. The workflow does not call it unless `DETECTOR_MODULE` is set. |
| Data ingestion | `backend/preprocessing.py` is empty. No CSV/JSON loader in the product. |
| LLM integration | No provider client. A repo search found no Gemini, Groq, OpenAI, or Anthropic SDK usage. The string `sk-` appears only as a secret-scan regex. |
| Configuration | No `.env`, no dependency manifest, no documented app start command. `.github/workflows/test.yml` runs the test command on Python 3.12. |
| Tests | `testing/test_detection_metrics.py` (11 tests) and `testing/test_workflow.py` (14 tests). |
| Data | `testing/scenarios/auth_scenarios.json` only. |

`origin/main` (`757958f`, author Shrey-Sriram) contains only `README.md` (the single line `# cybersecurity-techstartup`), the two empty Python files, and `backend/.DS_Store` plus `notebooks/.DS_Store` (6148 bytes each). This branch deletes those `.DS_Store` files. Their contents were not parsed.

**Assumption:** the hackathon brief’s Next.js and FastAPI list is a proposal. It is not the stack in git.

## How to run the app and existing tests

**App:** no start command exists. Confirmed by the absence of a server entry point and of a package manifest.

**Tests, from the repo root. Python 3.12.3 is enough. No install step.**

```bash
python3 testing/test_detection_metrics.py -q
python3 testing/test_workflow.py -q
python3 testing/run_workflow.py
python3 testing/detection_metrics.py --self-check
python3 testing/detection_metrics.py
```

GitHub Actions runs `python3 testing/run_workflow.py` on push and pull request.

## Baseline test results

Local commands from this pass:

| Command | Exit | Result |
| --- | --- | --- |
| `python3 testing/test_detection_metrics.py -q` | 0 | `Ran 11 tests` … `OK` |
| `python3 testing/test_workflow.py -q` | 0 | `Ran 14 tests` … `OK` |
| `python3 testing/run_workflow.py` | 0 | `测试流程: 通过（检测器还没实现，场景已装载但未计分）`. Detector `not_implemented (backend/detection.py is empty)`. 8 scenarios `blocked`. `secrets: 0`. |
| `python3 testing/detection_metrics.py --self-check` | 0 | Synthetic 4-row calculator check: TP 1, FP 1, TN 1, FN 1, precision 0.5, recall 0.5, F1 0.5, false-positive rate 0.5. |
| `python3 testing/detection_metrics.py` | 2 | Refused: no labeled CSV, metrics not computed. |
| `python3 -m pytest -q` | 1 | `No module named pytest`. Not installed. No `pytest` config in the repo. |
| `npm test` | 254 | `ENOENT` for `/workspace/package.json`. |
| `ruff check .` | 127 | `ruff: command not found`. |
| `bandit -r .` | 127 | `bandit: command not found`. |

Counts: **25 passed, 0 failed, 0 skipped, 8 product scenarios blocked.** Blocked is not a pass of the product.

GitHub Actions on this branch, confirmed via `gh run list`: run `38281746211` (pull request) and run `38281745690` (push), both `testing-workflow`, conclusion success, about 10–11s, 2026-10-12T17:04:07Z. That success matches the local blocked-detector result. It is not a product test pass.

Netlify deploy preview `https://deploy-preview-1--cybersecurity-techstartup.netlify.app` returned **HTTP 404** with a “Page not found” document (curl, 2026-10-12). No app is being served.

Environment limits: Node v22.14.0 is installed and unused. Pytest, Ruff, Bandit, ESLint, and a TypeScript project check were not run as product scans because the tools or the project files are absent. Dependencies were not installed.

## Critical functional risks

**Confirmed**

1. The demo path does not exist. Empty `detection.py` and `preprocessing.py` cannot flag an event, ingest a file, or explain an alert.
2. The eight synthetic scenarios are loaded and then marked blocked. The workflow exit code 0 means the harness is healthy, not that detection worked.
3. There is no API or UI to show risk, time, evidence, or an empty state.

**Potential**

- The only locked rule is “5 or more `login_failed` events for one user, then a `login_success` for that user.” Unfamiliar source, password spray, and duplicate-event behavior have no product implementation and no scenario. A later `detect()` can pass this suite and still miss those cases.

## Critical security risks

**Confirmed**

- No product trust boundary is implemented: no listener, upload handler, database, shell call fed by telemetry, or model call.
- High-confidence secret scan inside `python3 testing/run_workflow.py` reported `secrets: 0` on this tree.
- `testing/run_workflow.py` and `testing/test_detection_metrics.py` call `subprocess` only with a fixed argument list (the interpreter plus a test file, or the metrics CLI). Telemetry text is not passed to a shell.
- The Netlify preview 404 means this PR is not exposing an application.

**Potential, not findings**

- When `backend/detection.py` is non-empty, the harness imports it in-process. A broken or hostile `detect()` would run with the tester’s privileges. That matters for local test runs, not for a deployed service that does not exist.
- Upload size limits, CSV formula injection, path traversal, SQL injection, prompt injection against a live model, and authentication are untestable until those features exist. Missing login is not a vulnerability of a server that is not there.
- `origin/main` tracks two `.DS_Store` files. Usual macOS metadata, not inspected as archives. Low hygiene issue, not a confirmed data leak.

**Assumption:** a future public demo would need an explicit decision about authentication. The repo does not claim multi-user access today.

## Detection evaluation readiness

Not ready to claim product accuracy.

| Item | Confirmed state |
| --- | --- |
| Product decisions scored | 0 |
| Ground-truth telemetry files | None |
| Synthetic contract | 8 scenarios in `testing/scenarios/auth_scenarios.json`: 3 `flagged` (P1-01, P3-04, P1-08), 5 `benign`. Labels were written as the test contract. They are not analyst labels from a real log. |
| Held-out split / leakage | Not applicable. Nothing is trained. |
| Calculator | `testing/detection_metrics.py` computes TP, FP, TN, FN, precision, recall, F1, and false-positive rate, and leaves zero denominators undefined. Unit-tested. |
| What the 25 passing tests prove | Metric arithmetic, scenario-file validation, secret-scan regex behavior, and that `testing/reference_rule.py` matches the 8 labels (unit test reports F1 1.0 on that contract). |
| What they do not prove | Behavior of `backend/detection.py`. |

The self-check F1 of 0.5 and the reference-rule F1 of 1.0 are harness checks. Do not put them on a slide as detection performance.

## Missing tests, by priority

1. **P0.** Call the product `detect()` on P1-01 through P1-08 and require pass, not blocked. The runner already does this once the function exists. Today it is blocked.
2. **P0.** Preprocessing: valid CSV, valid JSON, empty file, missing columns, bad timestamps, duplicates, extra fields, malformed JSON, unicode. No parser exists, so these tests do not exist.
3. **P1.** API status codes, schema, and safe errors, after an API exists.
4. **P1.** Dashboard empty, success, and backend-down states, after a UI exists.
5. **P1.** LLM timeout, malformed model output, disagreement with the rule score, and prompt injection. P3-04 is only a labeled scenario. No model client runs it.
6. **P2.** More detection families (unfamiliar source, spray, duplicate suppression) if the team adopts them. They are unspecified in code, not failing tests.
7. **P2.** Evidence ids must be a subset of the input event ids. The current contract checks that flagged results have some evidence and that the summary does not say “confirmed compromise.” It does not check evidence membership.
8. **P2.** `pip-audit` / `npm audit` / Bandit / Semgrep after a manifest and real modules exist. Running them on this tree would not show that a future app is safe.

## Recommended next actions

1. Treat this file as the baseline and review it before adding tests for code that is not in the repo.
2. Keep using `python3 testing/run_workflow.py` as the gate. When `detect()` appears, the same command should change the eight rows from `blocked` to `pass` or fail the run.
3. Do not publish precision, recall, or F1 until that command prints metrics from `backend.detection` and the report says they came from that module.
4. Add ingestion tests only after `backend/preprocessing.py` has a function signature to call.
5. Leave lint, typecheck, and dependency audit blocked until the product stack is actually committed. Do not install those tools just to scan empty files.
