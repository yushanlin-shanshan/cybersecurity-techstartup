# Bug and vulnerability register

Inspection date: 2026-10-12. Commit inspected: `03c2599` on `main`.

Severity is about the hackathon demo and the safety of the software that exists, not about a production SOC deployment.

## Confirmed

### BUG-001 — No application is implemented

| Field | Value |
| --- | --- |
| Severity | Critical for the demo |
| Type | Missing functionality. Not a regression in existing behavior. |
| Status | Open |
| Component | Entire product |

**Evidence**

- `git ls-tree -r HEAD` at `03c2599` lists only `README.md`.
- `README.md` is the single line `# cybersecurity-techstartup`.
- No `package.json`, `pyproject.toml`, `requirements.txt`, Python application modules, TypeScript, CSV, or JSON telemetry.
- GitHub issues and pull requests: none. Only branch: `main`.
- `npm test` exits because `package.json` is missing (exit 254).
- `python3 -m pytest -q` exits 1 with `No module named pytest`. There is also no test suite for `pytest` to collect.

**Impact**

There is no ingestion, detector, API, dashboard, or explanation path to demonstrate. Detection precision, recall, and F1 cannot be measured.

**Safe reproduction**

```bash
git clone https://github.com/yushanlin-shanshan/cybersecurity-techstartup
cd cybersecurity-techstartup
git checkout 03c2599
git ls-tree -r HEAD
```

**Remediation**

Land a small vertical slice before more test authoring: one synthetic auth-event format, one deterministic rule, one way to run it locally, and one fixture each for “should flag” and “should not flag”. Then automate P0 and P1 in `docs/testing/TEST_PLAN.md`.

This register does not prescribe Next.js or FastAPI. Those were proposals in the brief, not dependencies of this repository.

### OBS-001 — No credentials in the tracked tree

| Field | Value |
| --- | --- |
| Severity | Info |
| Type | Observation, not a vulnerability |
| Status | Checked on 2026-10-12 |
| Component | Repository contents |

A ripgrep scan of the worktree excluding `.git` found no API keys, private keys, passwords, or token strings. The absence of a secret is not a security review of a future app.

## Not confirmed

These are risks to test when the matching code appears. They are not findings.

| ID | Risk | Why it is not a finding yet |
| --- | --- | --- |
| RISK-01 | Upload endpoint without a size limit | No endpoint. |
| RISK-02 | CSV formula injection on export | No export. |
| RISK-03 | Prompt injection via log text | No LLM client. |
| RISK-04 | Model-written HTML or explanations treated as evidence | No explanation path. |
| RISK-05 | Dependency CVEs | No dependency manifest. |
| RISK-06 | Missing authentication | No server and no claim of multi-user access. Revisit if the demo is exposed beyond localhost. |

## Product defects found by tests

None. The only executed tests are the metric-calculator tests in `testing/test_detection_metrics.py`. They passed. They do not exercise a detector.
