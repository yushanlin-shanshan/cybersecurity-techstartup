# Test execution results

Date: 2026-10-12. Machine Python: 3.12.3. Machine Node: v22.14.0. Neither is wired to a project in this repository.

## Counts

| Bucket | Count | Meaning |
| --- | --- | --- |
| Passed | 25 | 11 metric-calculator tests + 14 workflow tests |
| Failed | 0 | No unit test failed |
| Skipped | 0 | Nothing was skipped inside the unit files |
| Blocked | 8 scenarios | `backend/detection.py` is empty, so the product was not scored |

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

## Workflow command

```bash
python3 testing/run_workflow.py
```

Exit 0. Detector state `not_implemented`. Eight scenarios `blocked`. Secret findings 0. The command also runs the 11 + 14 unit tests and fails the process if either file fails.

`python3 testing/test_workflow.py -v` result: `Ran 14 tests`, `OK`, exit 0.

| Test | Result |
| --- | --- |
| `test_duplicate_id_is_rejected` | passed |
| `test_default_loader_targets_the_product_module` | passed |
| `test_empty_product_module_is_not_implemented` | passed |
| `test_ready_module_is_loaded_from_detector_module_name` | passed |
| `test_detector_exception_is_recorded` | passed |
| `test_flag_everything_detector_is_a_mismatch` | passed |
| `test_overclaim_and_missing_evidence_fail_the_contract` | passed |
| `test_prompt_injection_scenario_stays_flagged` | passed |
| `test_shipped_scenarios_match_the_reference_rule` | passed |
| `test_threshold_boundary` | passed |
| `test_current_repository_report_is_coherent` | passed |
| `test_exit_code_policy` | passed |
| `test_repository_has_no_high_confidence_secrets` | passed |
| `test_secret_assignment_is_found_and_plain_words_are_not` | passed |

## Not claimed

- The product detector was not scored. Those 8 rows are blocked, not passes.
- No dependency CVE count is available.
- The calculator fixture F1 of 0.5 and the reference-rule F1 of 1.0 are synthetic harness checks, not product accuracy.
