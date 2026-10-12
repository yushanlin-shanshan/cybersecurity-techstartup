# Testing report

SCU AIC × CrowdStrike hackathon, Track 2 (Detect). Working name in the brief: NonprofitShield AI.

Report date: 2026-10-12. Repository: [yushanlin-shanshan/cybersecurity-techstartup](https://github.com/yushanlin-shanshan/cybersecurity-techstartup). Base commit inspected: `03c2599` (`Initial commit`, 2026-10-12, author Yushan Lin).

## Short version

The product detector is still empty. `backend/detection.py` and `backend/preprocessing.py` were added on `main` as 0-byte placeholders (`757958f`). There is still no API, dashboard, or explanation model.

The testing workflow runs anyway:

```bash
python3 testing/run_workflow.py
```

Latest observed result: exit 0, headline `测试流程: 通过（检测器还没实现，场景已装载但未计分）`. Eight synthetic scenarios are loaded and marked blocked. No product precision, recall, or F1 was computed.

A reference rule inside the test suite scores those same eight scenarios at F1 1.0. That number checks the harness. It is not the product.

## Architecture as it exists

| Component | State |
| --- | --- |
| Frontend | Absent. No `package.json`. |
| API server | Absent. |
| `backend/preprocessing.py` | Present, 0 bytes. |
| `backend/detection.py` | Present, 0 bytes. The workflow looks here for `detect()`. |
| LLM explanations | Absent. |
| Database | Absent. |
| Synthetic scenario contract | `testing/scenarios/auth_scenarios.json`, 8 cases. |
| Product ground-truth telemetry | None. |
| Testing entry point | `python3 testing/run_workflow.py` |
| CI | `.github/workflows/test.yml` runs that command. |

Python 3.12.3 is enough. The workflow uses the standard library only.

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

### Workflow command

```bash
python3 testing/run_workflow.py
```

Observed exit 0:

```text
测试流程: 通过（检测器还没实现，场景已装载但未计分）
exit: 0
detector: not_implemented (backend/detection.py is empty)
scenarios: 8
secrets: 0
claim: Detector is not implemented, so no detection metrics were computed.
  P1-01 [blocked] expected flagged
  P1-02 [blocked] expected benign
  P1-03 [blocked] expected benign
  P1-04 [blocked] expected benign
  P1-05 [blocked] expected benign
  P3-04 [blocked] expected flagged
  P1-07 [blocked] expected benign
  P1-08 [blocked] expected flagged
report: testing/output/workflow_report.json
```

### Unit tests executed by that command

```bash
python3 testing/test_detection_metrics.py
python3 testing/test_workflow.py
```

`test_detection_metrics.py`: 11 tests, `OK`, exit 0.

`test_workflow.py`: 14 tests, `OK`, exit 0.

The workflow tests include a plug-in check: pointing the loader at `testing/reference_rule.py` scores the 8 synthetic scenarios as TP 3, FP 0, TN 5, FN 0, precision 1, recall 1, F1 1, false-positive rate 0. Class balance: 3 flagged labels, 5 benign labels. **Synthetic harness check only.**

```bash
python3 testing/detection_metrics.py --self-check
```

Exit 0. Separate four-row calculator fixture: TP 1, FP 1, TN 1, FN 1, precision 0.5, recall 0.5, F1 0.5, false-positive rate 0.5. **This is not application performance.**

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

Counts for the latest workflow run: **25 unit tests passed, 0 failed, 0 skipped, 8 product scenarios blocked.** Detail is in `docs/testing/TEST_RESULTS.md`.

## Detection metrics

| Question | Answer |
| --- | --- |
| Product detector decisions scored | 0 (module empty, scenarios blocked) |
| Synthetic contract scenarios loaded | 8 |
| Reference-rule score on that contract | F1 1.0, harness only |
| Real telemetry labels | None |
| Held-out product test set | None |
| Train/test leakage | Not applicable; nothing is trained |
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

1. Implement `detect()` in `backend/detection.py` so `python3 testing/run_workflow.py` changes the eight blocked rows into passes. The contract is in `docs/testing/WORKFLOW.md`.
2. Keep summaries free of the phrase “confirmed compromise”.
3. Only then attach an explanation model, with a fallback when the provider errors. Scenario `P3-04` already requires the decision to ignore hostile log text.
4. Do not quote the reference-rule F1 of 1.0 as product accuracy.

## What remains untested

Everything in the product brief except the metric arithmetic: ingestion edge cases, detection quality, API status codes, dashboard states, LLM failure and prompt injection, dependency vulnerabilities, and browser behavior.

## Artifacts

- This report.
- `docs/testing/TEST_PLAN.md`
- `docs/testing/SECURITY_CHECKLIST.md`
- `docs/testing/BUG_REGISTER.md`
- `docs/testing/DETECTION_EVALUATION.md`
- `docs/testing/TEST_RESULTS.md`
- `docs/testing/WORKFLOW.md`
- `testing/run_workflow.py`
- `testing/workflow_lib.py`
- `testing/reference_rule.py`
- `testing/scenarios/auth_scenarios.json`
- `testing/detection_metrics.py`
- `testing/test_detection_metrics.py`
- `testing/test_workflow.py`
- `.github/workflows/test.yml`
