# Detection evaluation

Date: 2026-10-12.

## Result

**Application detection accuracy was not measured.**

The repository has no detector, no telemetry, and no ground-truth labels. Precision, recall, F1, and false-positive rate for NonprofitShield AI, or for any other detector, are unknown.

The numbers below are a calculator self-check on four synthetic rows that live in `testing/detection_metrics.py`. They prove the arithmetic. They are not a detection score.

## What was executed

```bash
python3 testing/test_detection_metrics.py -v
python3 testing/detection_metrics.py
python3 testing/detection_metrics.py --self-check
```

`python3 testing/detection_metrics.py` with no CSV exited **2** and printed:

```text
evaluation blocked: no labeled CSV provided; detection metrics were not computed.
```

`python3 testing/detection_metrics.py --self-check` exited **0** and printed:

```text
source: in-memory synthetic calculator fixture
claim: Synthetic calculator self-check only. This is not detection performance of the application.
[overall]
  evaluated: 4
  positive_labels: 2
  negative_labels: 2
  tp: 1  fp: 1  tn: 1  fn: 1
  precision: 0.5000
  recall: 0.5000
  f1: 0.5000
  false_positive_rate: 0.5000
self_check: passed
```

Class balance of that fixture: 2 flagged labels and 2 benign labels. The labels were written by the test, not by an analyst and not by a model. Label quality for real events: **not applicable**. There is no held-out product dataset and no train/test split, so data leakage does not arise. There is also no baseline detector to compare.

## Hand calculation for the fixture

| event | ground_truth | predicted | cell |
| --- | --- | --- | --- |
| s1 | flagged | flagged | TP |
| s2 | positive | negative | FN |
| s3 | benign | suspicious (alias of flagged) | FP |
| s4 | not flagged | benign | TN |

- Precision = 1 / (1 + 1) = 0.5
- Recall = 1 / (1 + 1) = 0.5
- F1 = 2 × 0.5 × 0.5 / (0.5 + 0.5) = 0.5
- False-positive rate = 1 / (1 + 1) = 0.5

## Zero denominators

| Situation | Metric | Calculator result |
| --- | --- | --- |
| No predicted positives (TP + FP = 0) | Precision, and F1 | undefined |
| No positive labels (TP + FN = 0) | Recall, and F1 | undefined |
| No negative labels (FP + TN = 0) | False-positive rate | undefined |
| Precision and recall both 0 | F1 | undefined, because the denominator is 0 |

Unit tests cover these cases. See `testing/test_detection_metrics.py`.

## How to score the real detector later

1. Run the frozen detector on events it was not tuned on.
2. Write UTF-8 CSV with `ground_truth` and `predicted`. Optional: `event_id`, `category`.
3. Positive labels mean “should be flagged”. Accepted words include `flagged`, `suspicious`, `1`, `true`. Negative words include `benign`, `not_flagged`, `0`, `false`. Unknown words fail the run.
4. Duplicate `event_id` values fail the run so a double-counted alert cannot silently change the score.
5. `python3 testing/detection_metrics.py heldout.csv`
6. Quote the output in `TESTING_REPORT.md` and name the file that produced it.

Map categories only if the file has a `category` column. Do not invent per-scenario scores.

Suspicious activity and confirmed compromise stay different claims. This script scores the flag decision only.
