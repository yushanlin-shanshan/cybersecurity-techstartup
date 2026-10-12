# Independent validation

Date: 2026-10-12. Scope: approved MVP contract for `backend/detection.py` and `backend/preprocessing.py`.

Production detection logic was not changed. `testing/reference_rule.py` and existing assertions were not changed. These synthetic tests do not show production accuracy, and they are not a security review of a deployed application.

## Approved contract

1. “Later” means a later position in the input list. A conflicting timestamp does not change the decision.
2. No time window. Five failures may span multiple days.
3. Each valid input record counts. This task does not deduplicate.
4. Leading and trailing whitespace on usernames is stripped. Matching stays case-sensitive. There is no extra Unicode normalization.
5. Only canonical action names count, including `login_failed` and `login_success`. Unknown values are not lowercased.
6. Timestamps do not order events. Invalid or missing timestamps must not change the decision when the rest of the record is valid. Timestamp checks are recorded separately below.
7. Duplicate event ids may appear in evidence. Every evidence id must come from an input record that supports the matched pattern.

Password spraying, unfamiliar-source detection, time-window detection, and deduplication stay out of scope.

## Tests added

File: `testing/test_detector_adversarial.py`. It calls the product functions directly and does not import the reference oracle. It does not use the original eight scenario ids.

| Test | Expected outcome |
| --- | --- |
| `test_list_order_flags_when_timestamps_agree` | flagged; evidence is the five failure ids and the success id |
| `test_conflicting_timestamps_do_not_change_list_order` | still flagged; same evidence as the time-aligned list |
| `test_success_before_failures_stays_benign` | benign; empty evidence |
| `test_failures_may_span_multiple_days` | flagged |
| `test_duplicate_ids_count_as_separate_records` | flagged; the repeated id appears five times |
| `test_identical_duplicate_rows_are_not_collapsed` | flagged; duplicate id count is five |
| `test_conflicting_duplicate_rows_are_counted_separately` | benign; four failures for one user do not borrow the fifth row’s other user |
| `test_interleaved_users_only_the_matching_user_is_evidence` | flagged for one user; the other user’s ids are absent |
| `test_two_interleaved_users_can_both_match` | flagged; both users’ pattern ids are evidence |
| `test_source_address_is_not_a_requirement_of_this_rule` | flagged when sources differ |
| `test_whitespace_is_stripped_and_case_is_preserved` | padded name matches; `Ada` does not match `ada` |
| `test_unicode_composed_and_decomposed_users_stay_distinct` | benign |
| `test_uppercase_action_is_not_silently_normalized` | `LOGIN_FAILED` is skipped; result stays benign |
| `test_logout_does_not_count_as_a_failure` | benign, with an unsupported-action warning |
| `test_invalid_timestamps_do_not_change_a_valid_pattern` | flagged; no timestamp warning |
| `test_extra_fields_and_hostile_text_do_not_change_or_leak` | burst stays flagged; a hostile success alone stays benign; message text is absent from the summary |
| `test_repeated_execution_is_identical` | two calls return equal dictionaries |
| `test_evidence_ids_are_backed_by_input_rows` | evidence ids are a sub-multiset of input ids; an unrelated success is excluded |
| `test_empty_and_benign_shapes` | empty list, four failures then success, failures without success, and successes only are benign |
| `test_non_list_is_not_assessed` | `assessment` is `not_assessed` and evidence is empty |

## Timestamp behavior, recorded separately

Invalid, missing, empty, impossible, and offset timestamps do not change a list-order match. The current preprocessor does not emit a timestamp warning. That matches decision 6: the decision stays the same. It also means bad timestamps are accepted silently. That is observed behavior, not a failed assertion under the approved contract.

## Commands and results

```bash
python3 testing/test_detector_adversarial.py -v
```

`Ran 20 tests` … `OK`. Exit 0.

```bash
python3 testing/run_workflow.py
```

Exit 0. The workflow runs `test_detection_metrics.py` (11), `test_workflow.py` (14), `test_detector.py` (17), and `test_detector_adversarial.py` (20), then scores the original eight scenarios.

```text
测试流程: 通过（检测器与合成场景一致）
detector: ready (detect() found)
scenarios: 8
secrets: 0
  P1-01 [pass] expected flagged predicted flagged
  P1-02 [pass] expected benign predicted benign
  P1-03 [pass] expected benign predicted benign
  P1-04 [pass] expected benign predicted benign
  P1-05 [pass] expected benign predicted benign
  P3-04 [pass] expected flagged predicted flagged
  P1-07 [pass] expected benign predicted benign
  P1-08 [pass] expected flagged predicted flagged
synthetic metrics: evaluated 8 tp 3 fp 0 tn 5 fn 0 precision 1.0 recall 1.0 f1 1.0 fpr 0.0
```

Counts for this pass: **20 new tests passed, 0 failed, 0 skipped.** Original eight scenarios: **8 pass, 0 fail, 0 blocked.** No discrepancy with an approved decision, so production code was not modified.

The eight-row metrics are a synthetic contract score. They are not real-world accuracy.

## Confirmed defects

None against the approved MVP contract.

## Remaining limitations

- The rule still cannot see password spraying, an unfamiliar source, or a time window. Those were left out on purpose.
- Duplicate rows are counted separately, including identical retries. A later dedup rule would be a new contract.
- `Ada` and `ada`, and composed versus decomposed Unicode, stay different users.
- `LOGIN_FAILED` is ignored. Only the exact canonical strings count.
- Bad timestamps are stored as text or dropped to an empty string and do not warn.
- Evidence may repeat an id once per counted input row. It does not include users who did not complete the pattern.
- There is still no API, file parser, dashboard, or model. Hostile text is ignored by this rule only. That is not a test of an LLM prompt boundary.
