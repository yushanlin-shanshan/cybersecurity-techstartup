"""Unit tests for the detection-metric calculator.

These tests do not claim the application detects anything. They check the
arithmetic and the refusal path used when no labeled detector output exists.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import detection_metrics as dm


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(__file__).resolve().parent / "detection_metrics.py"


class ConfusionTests(unittest.TestCase):
    def test_mixed_fixture_matches_hand_calculation(self) -> None:
        result = dm.self_check()
        overall = result["overall"]
        self.assertEqual(overall["tp"], 1)
        self.assertEqual(overall["fp"], 1)
        self.assertEqual(overall["tn"], 1)
        self.assertEqual(overall["fn"], 1)
        self.assertEqual(overall["evaluated"], 4)
        self.assertEqual(overall["positive_labels"], 2)
        self.assertEqual(overall["negative_labels"], 2)
        self.assertEqual(overall["precision"], 0.5)
        self.assertEqual(overall["recall"], 0.5)
        self.assertEqual(overall["f1"], 0.5)
        self.assertEqual(overall["false_positive_rate"], 0.5)
        self.assertEqual(result["self_check"], "passed")
        self.assertIn("not detection performance", result["claim"])

    def test_precision_undefined_when_nothing_is_flagged(self) -> None:
        rows = [
            {"ground_truth": "flagged", "predicted": "benign"},
            {"ground_truth": "benign", "predicted": "benign"},
        ]
        overall = dm.score_rows(rows)["overall"]
        self.assertEqual(overall["tp"], 0)
        self.assertEqual(overall["fn"], 1)
        self.assertEqual(overall["tn"], 1)
        self.assertEqual(overall["fp"], 0)
        self.assertIsNone(overall["precision"])
        self.assertIn("no predicted positives", overall["precision_note"])
        self.assertEqual(overall["recall"], 0.0)
        self.assertIsNone(overall["f1"])
        self.assertEqual(overall["false_positive_rate"], 0.0)

    def test_recall_and_fpr_undefined_when_no_positives_or_negatives(self) -> None:
        only_flags = [
            {"ground_truth": "flagged", "predicted": "flagged"},
            {"ground_truth": "suspicious", "predicted": "attack"},
        ]
        flagged = dm.score_rows(only_flags)["overall"]
        self.assertEqual(flagged["recall"], 1.0)
        self.assertEqual(flagged["precision"], 1.0)
        self.assertEqual(flagged["f1"], 1.0)
        self.assertIsNone(flagged["false_positive_rate"])
        self.assertIn("no negative ground-truth", flagged["false_positive_rate_note"])

        only_benign_missed_as_flags = [
            {"ground_truth": "benign", "predicted": "flagged"},
        ]
        benign = dm.score_rows(only_benign_missed_as_flags)["overall"]
        self.assertEqual(benign["precision"], 0.0)
        self.assertIsNone(benign["recall"])
        self.assertIn("no positive ground-truth", benign["recall_note"])
        self.assertIsNone(benign["f1"])
        self.assertEqual(benign["false_positive_rate"], 1.0)

    def test_f1_undefined_when_precision_and_recall_are_zero(self) -> None:
        # TP=0, FP=1, FN=1. Precision and recall are both 0, so the F1
        # denominator (precision + recall) is 0 and F1 is undefined.
        rows = [
            {"ground_truth": "flagged", "predicted": "benign"},
            {"ground_truth": "benign", "predicted": "flagged"},
        ]
        overall = dm.score_rows(rows)["overall"]
        self.assertEqual(overall["precision"], 0.0)
        self.assertEqual(overall["recall"], 0.0)
        self.assertIsNone(overall["f1"])
        self.assertIn("both zero", overall["f1_note"])

    def test_category_split(self) -> None:
        rows = [
            {"ground_truth": "flagged", "predicted": "flagged", "category": "failed_login"},
            {"ground_truth": "benign", "predicted": "benign", "category": "failed_login"},
            {"ground_truth": "flagged", "predicted": "benign", "category": "unusual_source"},
        ]
        result = dm.score_rows(rows)
        self.assertEqual(result["by_category"]["failed_login"]["tp"], 1)
        self.assertEqual(result["by_category"]["failed_login"]["tn"], 1)
        self.assertEqual(result["by_category"]["unusual_source"]["fn"], 1)
        self.assertIsNone(result["by_category"]["unusual_source"]["false_positive_rate"])


class InputValidationTests(unittest.TestCase):
    def test_unknown_label_is_rejected(self) -> None:
        with self.assertRaises(dm.EvaluationError):
            dm.parse_binary("maybe", row_number=2, column="ground_truth")

    def test_duplicate_event_id_is_rejected(self) -> None:
        rows = [
            {"event_id": "e1", "ground_truth": "flagged", "predicted": "flagged"},
            {"event_id": "e1", "ground_truth": "benign", "predicted": "benign"},
        ]
        with self.assertRaises(dm.EvaluationError) as caught:
            dm.score_rows(rows)
        self.assertIn("duplicate event_id", str(caught.exception))

    def test_missing_file_and_missing_columns(self) -> None:
        with self.assertRaises(dm.EvaluationError):
            dm.evaluate_csv("/tmp/does-not-exist-nonprofitshield-labels.csv")

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            path.write_text("event_id,message\n1,hello\n", encoding="utf-8")
            with self.assertRaises(dm.EvaluationError) as caught:
                dm.evaluate_csv(str(path))
            self.assertIn("missing required columns", str(caught.exception))

            empty = Path(directory) / "empty.csv"
            empty.write_text("", encoding="utf-8")
            with self.assertRaises(dm.EvaluationError):
                dm.evaluate_csv(str(empty))

            header_only = Path(directory) / "header.csv"
            header_only.write_text("ground_truth,predicted\n", encoding="utf-8")
            with self.assertRaises(dm.EvaluationError) as caught:
                dm.evaluate_csv(str(header_only))
            self.assertIn("no evaluable rows", str(caught.exception))


class CliTests(unittest.TestCase):
    def test_cli_without_input_is_blocked(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("not computed", completed.stderr)
        self.assertEqual(completed.stdout, "")

    def test_cli_self_check_json(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--self-check", "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["self_check"], "passed")
        self.assertEqual(payload["overall"]["f1"], 0.5)
        self.assertIn("not detection performance", payload["claim"])

    def test_cli_scores_a_caller_supplied_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "heldout.csv"
            path.write_text(
                "event_id,ground_truth,predicted\n"
                "a,flagged,flagged\n"
                "b,flagged,benign\n"
                "c,benign,benign\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), "--json"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["overall"]["tp"], 1)
        self.assertEqual(payload["overall"]["fn"], 1)
        self.assertEqual(payload["overall"]["tn"], 1)
        self.assertEqual(payload["overall"]["fp"], 0)
        self.assertEqual(payload["overall"]["precision"], 1.0)
        self.assertEqual(payload["overall"]["recall"], 0.5)
        self.assertEqual(payload["overall"]["evaluated"], 3)


if __name__ == "__main__":
    unittest.main()
