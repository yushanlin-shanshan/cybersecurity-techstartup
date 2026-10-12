# Bug and vulnerability register

Inspection date: 2026-10-12. Updated after `main` commit `757958f` added empty placeholders.

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

- At `03c2599` the tree was only `README.md`.
- At `757958f` the detection owner added `backend/detection.py` and `backend/preprocessing.py`. Both files are 0 bytes. `notebooks/` was added with no notebook.
- `python3 testing/run_workflow.py` exits 0 and reports `detector: not_implemented (backend/detection.py is empty)`. All 8 scenarios are `blocked`. Metrics are null.
- No `package.json`, API module, or dashboard exists.

**Impact**

The testing workflow can run, but the demo still cannot show a product decision, an API, or a dashboard. Product precision, recall, and F1 remain unmeasured.

**Remediation**

Implement `detect()` in `backend/detection.py` using the contract in `docs/testing/WORKFLOW.md`. Re-run `python3 testing/run_workflow.py`. A correct function turns the blocked rows into passes.

**Safe reproduction**

```bash
python3 testing/run_workflow.py
```

Exit 0 and `backend/detection.py is empty` reproduce the current gap. The testing workflow is healthy; the product function is absent.

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
| RISK-03 | Prompt injection via an LLM explanation | No LLM client. Scenario P3-04 already locks the rule decision against hostile log text, and the reference rule keeps it flagged. The product function has not run. |
| RISK-04 | Model-written HTML or explanations treated as evidence | No explanation path. |
| RISK-05 | Dependency CVEs | No dependency manifest. |
| RISK-06 | Missing authentication | No server and no claim of multi-user access. Revisit if the demo is exposed beyond localhost. |

## Product defects found by tests

None in the product. `backend/detection.py` is empty, so the workflow does not call it. The 25 unit tests passed. They exercise the harness and a reference rule, not the product detector.
