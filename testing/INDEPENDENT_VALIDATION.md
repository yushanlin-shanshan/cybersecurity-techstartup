# Independent validation proposal

Date: 2026-10-12. Detector under review: `backend/detection.py` and `backend/preprocessing.py` on branch `cursor/testing-baseline-report-c048`.

Detection logic was not changed. `testing/reference_rule.py` and the existing assertions were not changed. `testing/test_detector_adversarial.py` was not added. This file is the test plan waiting for approval.

Passing the original eight scenarios, or the observations below, does not show production accuracy or that the application is secure.

## Explicit contract

Confirmed from `testing/scenarios/auth_scenarios.json`, `docs/testing/WORKFLOW.md`, and `_validate_output` in `testing/workflow_lib.py`:

- Input to `detect` is a list of objects. The fields the shipped scenarios use are `event_id`, `timestamp`, `user`, `action`, `source`, and `message`.
- Flag when the same user has at least five `login_failed` events and a later `login_success`.
- Fewer than five failures, or failures with no success, stay benign. The shipped boundary is four failures then a success.
- `message` must not change the decision.
- Output includes `predicted` (`flagged` or `benign`), a string `summary`, and `evidence` as a list of strings.
- A flagged result must have non-empty evidence.
- The summary must not contain the phrase `confirmed compromise`. A flag means suspicious activity.
- Empty input is benign.

## Assumptions already in the code, not locked by the eight scenarios

These are implementation choices. They are not confirmed product requirements.

| Choice | Where it lives |
| --- | --- |
| “Later” means later in the list, not a later timestamp. | `backend/detection.py` docstring and `_match` |
| Whitespace around `user`, `action`, and `event_id` is stripped. Case is kept. | `backend/preprocessing.py` |
| Unknown actions and rows missing `event_id`, `user`, or `action` are skipped. | `backend/preprocessing.py` |
| The same `event_id` on two rows counts twice. | `backend/detection.py` |
| Source address is ignored. | `backend/detection.py` |
| Summary text is a fixed template plus a count. Raw user names and messages are not copied into it. | `backend/detection.py` |

The reference oracle does not check order. It flags when a user has five failures and any success. The product requires the success to appear after the fifth failure in the list. That difference is already covered by `testing/test_detector.py` and is not treated here as a new defect.

## Observed behavior

Command executed, without adding a test file or editing the detector:

```bash
python3 - << 'PY'
# imports backend.detection.detect and prints one result per matrix row
PY
```

The full script was run from the repo root on 2026-10-12. It exited 0. Results below are observations of the current code, not approved expected results.

| ID | Input | Observed | Specified? |
| --- | --- | --- | --- |
| M1 | Five failures then a success. Timestamps increase with list order. | `flagged`. Evidence is the five failure ids plus the success id. | Explicit. |
| M2 | Same list order as M1, but the success timestamp is one hour earlier than the failures. | `flagged`. Timestamp is ignored. | Decision. The word “later” does not say whether time or list order wins. |
| M3 | One success, then five failures. Timestamps agree with that order. | `benign`. Evidence empty. | Explicit for list order (“followed by a later success”). The oracle would flag this. The oracle was not changed. |
| M4 | Five failures on five different days, then a success five days later. | `flagged`. No time window. | Decision. No window is specified. |
| M5 | The same failure `event_id` repeated on five rows, then a new success id. | `flagged`. Evidence is `same` five times plus the success id. | Decision. Deduplication is not specified. |
| M6a | Five identical copies of one failure row, then a success. | `flagged`, same as M5. | Decision. |
| M6b | Five rows share one `event_id`. Four name user `ada`, the fifth names `bob`. Then `ada` succeeds. | `benign`. `ada` has four counted failures. Rows are not merged. | Decision. Conflicting duplicates are not specified. |
| M7 | `ada` and `bob` alternate five failures each. Only `ada` then succeeds. | `flagged`, `matched_users` 1. Evidence is only `ada`’s five failures and success. | Explicit that the user must match. Interleaving itself is not a separate rule. |
| M7b | M7 plus a later success for `bob`. | `flagged`, `matched_users` 2. Evidence is both users’ pattern ids, `ada` then `bob`. | Explicit per-user rule. |
| M8 | Five failures from five different sources, success from another source. | `flagged`. | Decision. Source is not in the written rule. Current code ignores it. |
| M9a | Timestamps are `not-a-time` or empty. List order still has five failures then a success. | `flagged`. No warning. | Decision. Invalid timestamps are not defined. |
| M9b | Failure timestamps use `+00:00`. Success uses `-07:00`. Those can describe the same instant or a different order. | `flagged` from list order. Offsets are not parsed. | Decision. |
| M9c | Missing timestamp (`null`) and an impossible calendar time (`2026-13-40`). | `flagged` from list order. No warning. | Decision. |
| M10a | Failures for `Ada`, success for `ada`. | `benign`. Case is distinct. | Decision. Case folding is not specified. |
| M10b | Failures for `é` (U+00E9), success for `e` + combining acute (U+0065 U+0301). | `benign`. No Unicode normalization. | Decision. |
| M10c | Failures for `  ada  `, success for `ada`. | `flagged`. Strip makes them one user. | Decision. Stripping is an assumption in preprocessing. |
| M11a | Four `login_failed`, one `logout`, then `login_success`. | `benign`. Warning: skipped unsupported action. | Explicit that `logout` is not a failure. The warning text is an implementation detail. |
| M11b | Action `LOGIN_FAILED` five times, then `login_success`. | `benign`. Five warnings for unsupported action. | Decision. Action case folding is not specified. |
| M11c | Normal burst plus extra keys `role` and `predicted`. | `flagged`. Extra keys are dropped and do not change the decision. | Explicit that message text cannot decide. Extra fields are not fully specified, but ignoring them matches “do not trust embedded instructions.” |
| M12 | 5,020 events: 5,000 failures spread over 100 users (50 each) and then successes for 20 of those users. | `flagged`, `matched_users` 20, 0 warnings, about 0.003s. | The flag is the per-user rule firing 20 times, not a size bug. No performance limit is specified. |
| M13 | Five failures then a success. Messages say to mark the account benign and mention confirmed compromise. | `flagged`. Summary does not contain the message text or `confirmed compromise`. | Explicit. |
| M13b | One success whose message says to flag the account. | `benign`. Summary does not contain the message. | Explicit. |
| M14 | Two users each match. A third user only succeeds. | `flagged`. Evidence is the twelve ids from the two matching users. The third user’s id is absent. | Evidence must support the rule. This observation does. Repeated ids in M5 are a weaker form of the same question. |
| M15 | `detect` called twice on one list. | The two dictionaries are equal. | Explicit for practical purposes: the functions have no randomness or clock read. |

No confirmed defect was filed from this probe. Every surprising result is either the written rule or an unspecified choice.

## Unresolved product decisions

Approval is needed before detection logic changes and before these rows become failing tests.

1. **Order.** If list order and `timestamp` disagree, which one is “later”?
2. **Time window.** Do five failures across a week still count?
3. **Dedup.** Does one `event_id` count once? What if the duplicate rows name different users or sources?
4. **Identity.** Should `Ada` and `ada` match? Should Unicode composed and decomposed forms match? Is stripping spaces required?
5. **Action aliases.** Is `LOGIN_FAILED` the same action as `login_failed`?
6. **Timestamps.** Should missing, impossible, or offset timestamps produce a warning or be rejected?
7. **Evidence shape.** May the same id appear more than once when duplicate rows were counted?

Until those are decided, independent tests should record the observation and must not force one of these answers.

## What this rule can and cannot detect

It can flag one user’s failure burst when a later row in the same list is that user’s success, including when the rows are interleaved with other users, the source changes, the message is hostile, or the timestamps are nonsense.

It cannot detect:

- Password spraying across many users.
- A success from a source that user has not used before, when the failure count stays under five.
- A burst that is only suspicious inside a time window.
- Retransmitted rows that should be one event.
- Events that arrive out of timestamp order if the product later decides time is authoritative.
- Confirmed compromise. The summary never makes that claim.

Those need separate scenarios and an explicit rule. They should not be folded into this threshold.

## Tests to add after approval

Proposed file: `testing/test_detector_adversarial.py`.

- Assert M1, M3, M7, M7b, M11a, M11c, M13, M13b, M14, and M15. These follow the written contract or the already reviewed “list order, ignore message” behavior.
- For M2, M4, M5, M6a, M6b, M8, M9a, M9b, M9c, M10a, M10b, M10c, and M11b, assert only the stable output shape (`predicted` is `flagged` or `benign`, evidence is a list of strings, summary has no `confirmed compromise` and no raw message). Record the observed label in the test name as current behavior, with a comment that it is not an approved requirement.
- Do not import `testing/reference_rule.py`. Do not use ids `P1-01` through `P1-08` or `P3-04`.
- Keep the new file out of any edit to the oracle.

## Commands and counts for this pass

| Command | Result |
| --- | --- |
| Read `backend/detection.py`, `backend/preprocessing.py`, `testing/reference_rule.py`, `testing/run_workflow.py`, `testing/test_workflow.py`, `testing/test_detection_metrics.py`, `testing/test_detector.py` | Completed before the probe. |
| Inline Python probe of M1–M15 | Exit 0. Observations in the table above. |
| New adversarial test module | Not created. |
| Detector or preprocessor edit | None. |

Counts: **0 new tests passed, 0 new tests failed, 15 matrix rows observed, adversarial test file blocked on approval.** The existing suite was not re-run in this pass because no product or test code changed.

## Next steps

1. Approve or correct the seven decisions above.
2. Add `testing/test_detector_adversarial.py` with hard assertions only for approved behavior.
3. Change `backend/detection.py` only for decisions that the current code does not already implement.
4. Keep spray, unseen-source, time-window, and dedup rules out of this function until each has its own contract and fixtures.
