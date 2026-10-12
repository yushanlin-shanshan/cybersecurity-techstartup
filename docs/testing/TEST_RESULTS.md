# Test execution results

Date: 2026-10-12. Machine Python: 3.12.3. Machine Node: v22.14.0. Neither is wired to a project in this repository.

## Counts

| Bucket | Count | Meaning |
| --- | --- | --- |
| Passed | 11 | Unit tests of the metric calculator only |
| Failed | 0 | No product test failed |
| Skipped | 0 | Nothing was skipped inside the unit file |
| Blocked | 6 command groups | Could not run because the application, its manifest, or a labeled detector file is missing |

Blocked is not a pass.

## Passed

Command:

```bash
python3 testing/test_detection_metrics.py -v
```

Result: `Ran 11 tests` then `OK`. Exit code 0. A second run produced the same pass count and exit code.

| Test | Result |
| --- | --- |
| `test_cli_scores_a_caller_supplied_file` | passed |
| `test_cli_self_check_json` | passed |
| `test_cli_without_input_is_blocked` | passed |
| `test_category_split` | passed |
| `test_f1_undefined_when_precision_and_recall_are_zero` | passed |
| `test_mixed_fixture_matches_hand_calculation` | passed |
| `test_precision_undefined_when_nothing_is_flagged` | passed |
| `test_recall_and_fpr_undefined_when_no_positives_or_negatives` | passed |
| `test_duplicate_event_id_is_rejected` | passed |
| `test_missing_file_and_missing_columns` | passed |
| `test_unknown_label_is_rejected` | passed |

Command:

```bash
python3 testing/detection_metrics.py --self-check
```

Exit code 0. Synthetic fixture only: evaluated 4, TP 1, FP 1, TN 1, FN 1, precision 0.5, recall 0.5, F1 0.5, false-positive rate 0.5.

## Blocked

| Command | Exit | Classification |
| --- | --- | --- |
| `test -f package.json` | 1 | Missing project file |
| `test -f pyproject.toml` | 1 | Missing project file |
| `test -f requirements.txt` | 1 | Missing project file |
| `pytest -q` | 127 | `pytest` is not installed, and there is no product suite |
| `python3 -m pytest -q` | 1 | `No module named pytest` |
| `npm test` | 254 | `ENOENT` opening `/workspace/package.json` |
| `ruff check .` | 127 | `ruff` is not installed; no Python app to lint |
| `bandit -r .` | 127 | `bandit` is not installed; no Python app to scan |
| TypeScript `tsc --noEmit` | not a project check | No `tsconfig.json` and TypeScript is not a dependency. `npx tsc` resolved to an unrelated deprecated npm package named `tsc`, not the TypeScript compiler. That output was discarded. |
| `python3 testing/detection_metrics.py` | 2 | Expected refusal: no labeled CSV, so detector metrics were not computed |

`pip-audit`, Semgrep, ESLint, and Playwright were not run. There is no dependency manifest and no UI.

## Not claimed

- No ingestion, API, dashboard, rule, or model test ran.
- No dependency CVE count is available.
- The synthetic F1 of 0.5 is not detection performance.
