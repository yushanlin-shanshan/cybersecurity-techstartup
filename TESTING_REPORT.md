# Testing report

SCU AIC × CrowdStrike hackathon, Track 2 (Detect). Working name in the brief: NonprofitShield AI.

Report date: 2026-10-12. Repository: [yushanlin-shanshan/cybersecurity-techstartup](https://github.com/yushanlin-shanshan/cybersecurity-techstartup). Base commit inspected: `03c2599` (`Initial commit`, 2026-10-12, author Yushan Lin).

## Short version

The repository does not contain an application. There is nothing to ingest telemetry, flag suspicious logins, explain an alert, or show a dashboard. Detection accuracy is **not** established. One new tool was added and tested: a metric calculator that refuses to invent scores when no labeled file is provided. Its 11 unit tests passed.

Judges should not be told that this project has measured precision, recall, or F1 for a detector.

## Architecture as it exists

| Component | State |
| --- | --- |
| Frontend (Next.js, React, dashboard) | Not in the repo |
| Backend (FastAPI or any other API) | Not in the repo |
| Telemetry ingestion | Not in the repo |
| Detection rules or model | Not in the repo |
| LLM explanations | Not in the repo |
| Database | Not in the repo |
| Datasets and ground-truth labels | None |
| Tests that shipped with the repo | None |
| Package manager / lockfile | None. No `package.json`, `pyproject.toml`, or `requirements.txt` |
| Environment variables | None documented, none committed |
| Local run command | None |

`README.md` on `main` is only `# cybersecurity-techstartup`.

Python 3.12.3 and Node v22.14.0 are installed on the inspection machine. The repository does not use them yet.

The brief’s technology list is a proposal. It was not used as a reason to add a framework.

## What was inspected

```bash
git status
git log --all --oneline
git branch -a
git show --stat HEAD
git ls-tree -r HEAD
gh repo view yushanlin-shanshan/cybersecurity-techstartup
gh issue list --repo yushanlin-shanshan/cybersecurity-techstartup --state all
gh pr list --repo yushanlin-shanshan/cybersecurity-techstartup --state all
```

Results that matter:

- One commit, one branch (`main`), working tree clean before this testing change.
- Tracked files: `README.md` only.
- GitHub: public repo created 2026-10-12, empty description, no issues, no pull requests.
- Secret-pattern search of the worktree (excluding `.git`) printed no matches.

## Existing tests

None on `03c2599`.

## Tests added in this pass

| File | Role |
| --- | --- |
| `testing/detection_metrics.py` | Scores a caller-supplied CSV. Exits 2 when no labels are provided. |
| `testing/test_detection_metrics.py` | Unit tests for the formulas, zero denominators, bad labels, and the CLI. |
| `docs/testing/TEST_PLAN.md` | Prioritized cases. Product cases are marked blocked. |
| `docs/testing/SECURITY_CHECKLIST.md` | Checklist with one completed secret scan. |
| `docs/testing/BUG_REGISTER.md` | Confirmed gap and risks that are not yet findings. |
| `docs/testing/DETECTION_EVALUATION.md` | Why no detector score is claimed, plus the synthetic self-check. |
| `docs/testing/TEST_RESULTS.md` | Pass, fail, skip, and blocked counts. |

## Commands and results

### Executed and passed

```bash
python3 testing/test_detection_metrics.py -v
```

`Ran 11 tests`, `OK`, exit 0. The same result was observed on a second run.

```bash
python3 testing/detection_metrics.py --self-check
```

Exit 0. Synthetic four-row fixture: TP 1, FP 1, TN 1, FN 1, precision 0.5, recall 0.5, F1 0.5, false-positive rate 0.5. Class balance: 2 positive labels, 2 negative labels. **This is not application performance.**

### Executed and blocked

```bash
python3 testing/detection_metrics.py
```

Exit 2. Message: labeled CSV not provided, metrics not computed. This is the correct outcome for the current repo.

### Not able to run a product suite

| Command | Exit | Why |
| --- | --- | --- |
| `pytest -q` | 127 | Command not found |
| `python3 -m pytest -q` | 1 | Module not installed; no product tests either |
| `npm test` | 254 | No `package.json` |
| `ruff check .` | 127 | Not installed; no app to lint |
| `bandit -r .` | 127 | Not installed; no app to scan |

ESLint, `tsc --noEmit` against a project, `npm audit`, `pip-audit`, Semgrep, and Playwright were not run. There is no JS project, no Python dependency list, and no UI. A clean scan was not invented.

Counts: **11 passed, 0 failed, 0 skipped, product suites blocked.** Detail is in `docs/testing/TEST_RESULTS.md`.

## Detection metrics

| Question | Answer |
| --- | --- |
| Events evaluated by a detector | 0 |
| Ground-truth labels in the repo | 0 |
| Held-out test set | None |
| Train/test leakage | Not applicable; nothing is trained |
| Baseline comparison | None |
| Precision, recall, F1 of the product | Not measured |

Per-category product metrics were not produced. The calculator can split by a `category` column later. That feature was unit-tested with in-memory rows, not with security telemetry.

## Security

Confirmed vulnerabilities: **none**. There is no application surface.

Completed check: tracked files do not contain credential material (OBS-001).

Not tested, because the code is absent: input validation, formula injection, path traversal, authentication, SQL injection, command injection, CORS, rate limits, dependency CVEs, prompt injection, hallucinated evidence, and tool use. Tool-use attacks do not apply; there are no agent tools.

Missing authentication is not filed as a vulnerability of a server that does not exist. If a later build is reachable beyond localhost, authentication has to be revisited on purpose.

## Highest-priority risks

1. **BUG-001 (Critical, open).** The demo cannot show detection, evidence, or a dashboard. This is missing software, not a flaky test.
2. **No labeled data.** Even after a detector lands, accuracy claims need a fixture the rules were not tuned on. The calculator is ready for that file and will not score a missing file.
3. **Future upload and LLM surfaces are untested.** They are listed as risks in the bug register, not as confirmed bugs.

## Highest-priority work before a live demo

1. Add the smallest runnable slice: load a synthetic auth log, apply one documented rule (failed logins followed by a success is the clearest first rule), print the evidence.
2. Add two fixtures and automated assertions: one that must flag, one that must not. Keep the “not confirmed compromise” wording in the assertion.
3. Add a malformed-input case that returns a controlled error.
4. Only then attach an explanation model, behind a fallback when the provider errors, and with a test that a hostile log line cannot change the rule decision.
5. Score `testing/detection_metrics.py` on a held-out CSV and paste the output into this report. Until that paste exists, do not quote precision or recall on a slide.

## What remains untested

Everything in the product brief except the metric arithmetic: ingestion edge cases, detection quality, API status codes, dashboard states, LLM failure and prompt injection, dependency vulnerabilities, and browser behavior.

## Artifacts

- This report.
- `docs/testing/TEST_PLAN.md`
- `docs/testing/SECURITY_CHECKLIST.md`
- `docs/testing/BUG_REGISTER.md`
- `docs/testing/DETECTION_EVALUATION.md`
- `docs/testing/TEST_RESULTS.md`
- `testing/detection_metrics.py`
- `testing/test_detection_metrics.py`
