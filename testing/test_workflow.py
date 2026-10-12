"""Tests for the workflow harness.

The live product detector is allowed to be missing. A reference rule is used
only inside this file to prove scoring works before that function exists.
"""

from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import reference_rule
import workflow_lib


ROOT = workflow_lib.ROOT


class ScenarioTests(unittest.TestCase):
    def test_shipped_scenarios_match_the_reference_rule(self) -> None:
        payload = workflow_lib.load_scenarios()
        self.assertEqual(payload["contract"]["min_failures"], reference_rule.MIN_FAILURES)
        outcome = workflow_lib.run_detector(reference_rule.detect, payload["scenarios"])
        self.assertEqual(outcome["errors"], [])
        self.assertEqual(outcome["mismatches"], [])
        self.assertEqual(outcome["contract_failures"], [])
        overall = outcome["metrics"]["overall"]
        self.assertEqual(overall["evaluated"], 8)
        self.assertEqual(overall["tp"], 3)
        self.assertEqual(overall["fp"], 0)
        self.assertEqual(overall["tn"], 5)
        self.assertEqual(overall["fn"], 0)
        self.assertEqual(overall["precision"], 1.0)
        self.assertEqual(overall["recall"], 1.0)
        self.assertEqual(overall["f1"], 1.0)
        self.assertEqual(overall["false_positive_rate"], 0.0)
        plugged_in = workflow_lib.build_report(ROOT, module_name="reference_rule")
        self.assertEqual(plugged_in["detector"]["state"], "ready")
        self.assertEqual(plugged_in["detector"]["metrics"]["overall"]["f1"], 1.0)
        self.assertIn("not measured accuracy", plugged_in["detector"]["metrics_claim"])
        self.assertEqual(workflow_lib.exit_code(plugged_in), 0)

    def test_prompt_injection_scenario_stays_flagged(self) -> None:
        payload = workflow_lib.load_scenarios()
        scenario = next(item for item in payload["scenarios"] if item["id"] == "P3-04")
        self.assertEqual(scenario["ground_truth"], "flagged")
        self.assertIn("Ignore previous instructions", scenario["events"][0]["message"])
        result = reference_rule.detect(scenario["events"])
        self.assertEqual(result["predicted"], "flagged")

    def test_threshold_boundary(self) -> None:
        payload = workflow_lib.load_scenarios()
        by_id = {item["id"]: item for item in payload["scenarios"]}
        self.assertEqual(reference_rule.detect(by_id["P1-01"]["events"])["predicted"], "flagged")
        self.assertEqual(reference_rule.detect(by_id["P1-03"]["events"])["predicted"], "benign")
        self.assertEqual(reference_rule.detect(by_id["P1-04"]["events"])["predicted"], "benign")

    def test_flag_everything_detector_is_a_mismatch(self) -> None:
        payload = workflow_lib.load_scenarios()

        def flag_everything(_events):
            return {"predicted": "flagged", "summary": "flagged", "evidence": ["x"]}

        outcome = workflow_lib.run_detector(flag_everything, payload["scenarios"])
        self.assertEqual(len(outcome["mismatches"]), 5)
        self.assertEqual(outcome["metrics"]["overall"]["fp"], 5)
        self.assertEqual(outcome["metrics"]["overall"]["precision"], 0.375)

    def test_overclaim_and_missing_evidence_fail_the_contract(self) -> None:
        payload = workflow_lib.load_scenarios()
        only = [payload["scenarios"][0]]

        def overclaim(_events):
            return {
                "predicted": "flagged",
                "summary": "confirmed compromise of the clinic account",
                "evidence": [],
            }

        outcome = workflow_lib.run_detector(overclaim, only)
        self.assertEqual(outcome["mismatches"], [])
        self.assertEqual(len(outcome["contract_failures"]), 2)

    def test_detector_exception_is_recorded(self) -> None:
        payload = workflow_lib.load_scenarios()

        def explode(_events):
            raise RuntimeError("backend blew up")

        outcome = workflow_lib.run_detector(explode, payload["scenarios"][:1])
        self.assertEqual(outcome["errors"][0]["status"], "error")
        self.assertIn("backend blew up", outcome["errors"][0]["detail"])
        self.assertIsNone(outcome["metrics"])


class LoaderTests(unittest.TestCase):
    def test_empty_product_module_is_not_implemented(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            backend = root / "backend"
            backend.mkdir()
            (backend / "detection.py").write_text("", encoding="utf-8")
            loaded = workflow_lib.load_detector(root, module_name="backend.detection")
            self.assertEqual(loaded["state"], "not_implemented")
            self.assertNotIn("detect", loaded)

    def test_ready_module_is_loaded_from_detector_module_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            module_name = "synthetic_detector_for_test"
            (root / f"{module_name}.py").write_text(
                textwrap.dedent(
                    """
                    def detect(events):
                        return {"predicted": "benign", "summary": "ok", "evidence": []}
                    """
                ),
                encoding="utf-8",
            )
            loaded = workflow_lib.load_detector(root, module_name=module_name)
            self.assertEqual(loaded["state"], "ready")
            self.assertEqual(loaded["detect"]([])["predicted"], "benign")
            sys.modules.pop(module_name, None)

    def test_default_loader_targets_the_product_module(self) -> None:
        loaded = workflow_lib.load_detector(ROOT)
        self.assertEqual(loaded["module"], "backend.detection")
        if loaded["state"] == "ready":
            self.assertIsNot(loaded["detect"], reference_rule.detect)


class SecretAndExitTests(unittest.TestCase):
    def test_secret_assignment_is_found_and_plain_words_are_not(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "notes.md").write_text(
                "We document the word api_key without a value.\n",
                encoding="utf-8",
            )
            (root / "config.py").write_text(
                "api_key = 'ghp_" + ("a" * 36) + "'\n",
                encoding="utf-8",
            )
            findings = workflow_lib.scan_secrets(root)
            self.assertTrue(any(item["pattern"] == "github_pat" for item in findings))
            self.assertTrue(all("notes.md" not in item["path"] for item in findings))

    def test_repository_has_no_high_confidence_secrets(self) -> None:
        self.assertEqual(workflow_lib.scan_secrets(ROOT), [])

    def test_exit_code_policy(self) -> None:
        blocked = {
            "secrets": {"count": 0},
            "detector": {
                "state": "not_implemented",
                "errors": [],
                "mismatches": [],
                "contract_failures": [],
            },
        }
        self.assertEqual(workflow_lib.exit_code(blocked), 0)
        leaked = {
            "secrets": {"count": 1},
            "detector": {
                "state": "not_implemented",
                "errors": [],
                "mismatches": [],
                "contract_failures": [],
            },
        }
        self.assertEqual(workflow_lib.exit_code(leaked), 1)
        mismatch = {
            "secrets": {"count": 0},
            "detector": {
                "state": "ready",
                "errors": [],
                "mismatches": [{"id": "P1-02"}],
                "contract_failures": [],
            },
        }
        self.assertEqual(workflow_lib.exit_code(mismatch), 1)

    def test_current_repository_report_is_coherent(self) -> None:
        report = workflow_lib.build_report(ROOT)
        self.assertEqual(report["secrets"]["count"], 0)
        self.assertEqual(report["scenarios"]["count"], 8)
        code = workflow_lib.exit_code(report)
        text = workflow_lib.format_summary(report, code)
        if report["detector"]["state"] in {"missing", "not_implemented"}:
            self.assertIsNone(report["detector"]["metrics"])
            self.assertTrue(all(case["status"] == "blocked" for case in report["detector"]["cases"]))
            self.assertEqual(code, 0)
            self.assertIn("未计分", text)
        elif report["detector"]["state"] == "ready":
            self.assertEqual(code, 0, report["detector"]["mismatches"])
        else:
            self.fail(report["detector"]["message"])
        self.assertIn("测试流程: 通过", text)


class BadScenarioTests(unittest.TestCase):
    def test_duplicate_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text(
                json.dumps(
                    {
                        "contract": {"min_failures": 5, "requires_later_success": True},
                        "scenarios": [
                            {"id": "A", "ground_truth": "benign", "events": []},
                            {"id": "A", "ground_truth": "benign", "events": []},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(workflow_lib.metrics.EvaluationError):
                workflow_lib.load_scenarios(path)


if __name__ == "__main__":
    unittest.main()
