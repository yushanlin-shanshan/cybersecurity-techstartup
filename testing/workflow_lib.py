"""Runnable testing workflow that does not require the product detector.

Exit policy for the CLI:
- 0 when the harness is healthy and the product detector is missing, or when
  an implemented detector matches every synthetic scenario.
- 1 when the harness finds a secret, a scenario file is invalid, unit tests
  fail, or an implemented detector disagrees with the scenario contract.
"""

from __future__ import annotations

import importlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Callable

import detection_metrics as metrics

ROOT = Path(__file__).resolve().parents[1]
SCENARIO_FILE = Path(__file__).resolve().parent / "scenarios" / "auth_scenarios.json"
DEFAULT_MODULE = "backend.detection"

SECRET_PATTERNS = (
    ("private_key", re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_pat", re.compile(r"\bghp_[A-Za-z0-9]{36}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b")),
    ("openai_style_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    (
        "assigned_secret",
        re.compile(
            r"(?i)\b(?:api[_-]?key|secret|token|password)\b\s*[=:]\s*['\"][^'\"]{8,}['\"]"
        ),
    ),
)

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "output"}
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pyc", ".ds_store"}
MAX_SCAN_BYTES = 512_000


def load_scenarios(path: Path = SCENARIO_FILE) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise metrics.EvaluationError(f"scenario file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise metrics.EvaluationError(f"scenario file is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("scenarios"), list):
        raise metrics.EvaluationError("scenario file must contain a scenarios list")
    if not payload["scenarios"]:
        raise metrics.EvaluationError("scenario file has no scenarios")
    seen: set[str] = set()
    for index, scenario in enumerate(payload["scenarios"], start=1):
        if not isinstance(scenario, dict):
            raise metrics.EvaluationError(f"scenario {index} is not an object")
        scenario_id = str(scenario.get("id", "")).strip()
        if not scenario_id:
            raise metrics.EvaluationError(f"scenario {index} is missing id")
        if scenario_id in seen:
            raise metrics.EvaluationError(f"duplicate scenario id {scenario_id}")
        seen.add(scenario_id)
        metrics.parse_binary(
            str(scenario.get("ground_truth", "")),
            row_number=index,
            column="ground_truth",
        )
        events = scenario.get("events")
        if not isinstance(events, list):
            raise metrics.EvaluationError(f"{scenario_id}: events must be a list")
        for event in events:
            if not isinstance(event, dict) or not str(event.get("event_id", "")).strip():
                raise metrics.EvaluationError(f"{scenario_id}: each event needs an event_id")
    contract = payload.get("contract") or {}
    if contract.get("min_failures") != 5 or contract.get("requires_later_success") is not True:
        raise metrics.EvaluationError("scenario contract drifted from the documented 5-then-success rule")
    return payload


def load_detector(root: Path = ROOT, module_name: str | None = None) -> dict:
    """Find the product detect() function. Never falls back to the reference rule."""
    name = module_name or os.environ.get("DETECTOR_MODULE") or DEFAULT_MODULE
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    file_path = _module_file(root, name)
    if name == DEFAULT_MODULE and file_path is not None and not file_path.exists():
        return _detector_state("missing", name, f"{_display_path(root, file_path)} does not exist")
    if file_path is not None and file_path.exists() and file_path.stat().st_size == 0:
        return _detector_state("not_implemented", name, f"{_display_path(root, file_path)} is empty")
    _purge_module(name)
    try:
        module = importlib.import_module(name)
    except ModuleNotFoundError as exc:
        return _detector_state("missing", name, str(exc))
    except Exception as exc:
        return _detector_state("error", name, f"{type(exc).__name__}: {exc}")
    detect = getattr(module, "detect", None)
    if not callable(detect):
        return _detector_state("not_implemented", name, f"{name}.detect is not defined")
    state = _detector_state("ready", name, "detect() found")
    state["detect"] = detect
    return state


def run_detector(detect: Callable, scenarios: list[dict]) -> dict:
    rows: list[dict] = []
    case_results: list[dict] = []
    contract_failures: list[dict] = []
    for scenario in scenarios:
        scenario_id = scenario["id"]
        try:
            raw = detect(scenario["events"])
        except Exception as exc:
            case_results.append(
                {
                    "id": scenario_id,
                    "status": "error",
                    "ground_truth": scenario["ground_truth"],
                    "detail": f"{type(exc).__name__}: {exc}",
                }
            )
            continue
        try:
            predicted, summary, evidence = _validate_output(raw, scenario_id)
        except metrics.EvaluationError as exc:
            case_results.append(
                {
                    "id": scenario_id,
                    "status": "error",
                    "ground_truth": scenario["ground_truth"],
                    "detail": str(exc),
                }
            )
            continue
        expected_positive = metrics.parse_binary(
            scenario["ground_truth"], row_number=1, column="ground_truth"
        )
        actual_positive = metrics.parse_binary(predicted, row_number=1, column="predicted")
        status = "pass" if expected_positive == actual_positive else "fail"
        case_results.append(
            {
                "id": scenario_id,
                "title": scenario.get("title", ""),
                "category": scenario.get("category", ""),
                "status": status,
                "ground_truth": scenario["ground_truth"],
                "predicted": predicted,
                "summary": summary,
            }
        )
        if "confirmed compromise" in summary.lower():
            contract_failures.append(
                {
                    "id": scenario_id,
                    "detail": "summary calls the case confirmed compromise",
                }
            )
        if actual_positive and not evidence:
            contract_failures.append(
                {
                    "id": scenario_id,
                    "detail": "flagged result has no evidence",
                }
            )
        rows.append(
            {
                "event_id": scenario_id,
                "ground_truth": scenario["ground_truth"],
                "predicted": predicted,
                "category": scenario.get("category", ""),
            }
        )
    errors = [item for item in case_results if item["status"] == "error"]
    mismatches = [item for item in case_results if item["status"] == "fail"]
    scored = None
    if rows and not errors:
        scored = metrics.score_rows(rows)
    return {
        "cases": case_results,
        "mismatches": mismatches,
        "errors": errors,
        "contract_failures": contract_failures,
        "metrics": scored,
    }


def inventory(root: Path = ROOT) -> dict:
    def describe(relative: str) -> dict:
        path = root / relative
        if not path.exists():
            return {"path": relative, "state": "missing"}
        size = path.stat().st_size
        if size == 0:
            return {"path": relative, "state": "empty", "bytes": 0}
        return {"path": relative, "state": "present", "bytes": size}

    return {
        "detection_module": describe("backend/detection.py"),
        "preprocessing_module": describe("backend/preprocessing.py"),
        "frontend_manifest": describe("package.json"),
        "python_manifest": describe("pyproject.toml"),
        "requirements": describe("requirements.txt"),
    }


def scan_secrets(root: Path) -> list[dict]:
    findings: list[dict] = []
    for path in _iter_text_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for name, pattern in SECRET_PATTERNS:
            match = pattern.search(text)
            if not match:
                continue
            line_number = text.count("\n", 0, match.start()) + 1
            findings.append(
                {
                    "path": str(path.relative_to(root)),
                    "line": line_number,
                    "pattern": name,
                }
            )
    return findings


def build_report(root: Path = ROOT, module_name: str | None = None) -> dict:
    scenario_payload = load_scenarios()
    detector = load_detector(root, module_name=module_name)
    detect = detector.pop("detect", None)
    scenario_list = scenario_payload["scenarios"]
    if detector["state"] == "ready" and detect is not None:
        outcome = run_detector(detect, scenario_list)
        detector_section = {
            **detector,
            "cases": outcome["cases"],
            "mismatches": outcome["mismatches"],
            "errors": outcome["errors"],
            "contract_failures": outcome["contract_failures"],
            "metrics": outcome["metrics"],
            "metrics_claim": (
                "Synthetic scenario contract only. "
                "This is not measured accuracy on real telemetry."
            ),
        }
    else:
        detector_section = {
            **detector,
            "cases": [
                {
                    "id": scenario["id"],
                    "title": scenario.get("title", ""),
                    "status": "blocked",
                    "ground_truth": scenario["ground_truth"],
                }
                for scenario in scenario_list
            ],
            "mismatches": [],
            "errors": [],
            "contract_failures": [],
            "metrics": None,
            "metrics_claim": "Detector is not implemented, so no detection metrics were computed.",
        }
    secrets = scan_secrets(root)
    return {
        "inventory": inventory(root),
        "secrets": {"count": len(secrets), "findings": secrets},
        "scenarios": {
            "file": str(SCENARIO_FILE.relative_to(root)),
            "count": len(scenario_list),
            "ids": [scenario["id"] for scenario in scenario_list],
            "contract": scenario_payload.get("contract"),
        },
        "detector": detector_section,
    }


def exit_code(report: dict, unit_tests_passed: bool = True) -> int:
    if not unit_tests_passed:
        return 1
    if report["secrets"]["count"]:
        return 1
    detector = report["detector"]
    if detector["state"] in {"missing", "not_implemented"}:
        return 0
    if detector["state"] == "error":
        return 1
    if detector["errors"] or detector["mismatches"] or detector["contract_failures"]:
        return 1
    return 0


def format_summary(report: dict, code: int) -> str:
    detector = report["detector"]
    if code == 0 and detector["state"] in {"missing", "not_implemented"}:
        headline = "测试流程: 通过（检测器还没实现，场景已装载但未计分）"
    elif code == 0:
        headline = "测试流程: 通过（检测器与合成场景一致）"
    else:
        headline = "测试流程: 失败"
    lines = [
        headline,
        f"exit: {code}",
        f"detector: {detector['state']} ({detector['message']})",
        f"scenarios: {report['scenarios']['count']}",
        f"secrets: {report['secrets']['count']}",
        f"claim: {detector['metrics_claim']}",
    ]
    for case in detector["cases"]:
        extra = ""
        if case["status"] in {"pass", "fail"}:
            extra = f" expected {case['ground_truth']} predicted {case.get('predicted')}"
        elif case["status"] == "blocked":
            extra = f" expected {case['ground_truth']}"
        elif case["status"] == "error":
            extra = f" {case.get('detail', '')}"
        lines.append(f"  {case['id']} [{case['status']}]{extra}")
    metrics_block = detector.get("metrics")
    if metrics_block is not None:
        overall = metrics_block["overall"]
        lines.append(
            "synthetic metrics: "
            f"evaluated {overall['evaluated']} "
            f"tp {overall['tp']} fp {overall['fp']} tn {overall['tn']} fn {overall['fn']} "
            f"precision {overall['precision']} recall {overall['recall']} "
            f"f1 {overall['f1']} fpr {overall['false_positive_rate']}"
        )
    return "\n".join(lines)


def _validate_output(raw: object, scenario_id: str) -> tuple[str, str, list[str]]:
    if not isinstance(raw, dict):
        raise metrics.EvaluationError(f"{scenario_id}: detect() must return an object")
    predicted = str(raw.get("predicted", ""))
    metrics.parse_binary(predicted, row_number=1, column="predicted")
    summary = raw.get("summary", "")
    if not isinstance(summary, str):
        raise metrics.EvaluationError(f"{scenario_id}: summary must be a string")
    evidence = raw.get("evidence", [])
    if not isinstance(evidence, list) or not all(isinstance(item, str) for item in evidence):
        raise metrics.EvaluationError(f"{scenario_id}: evidence must be a list of strings")
    return predicted, summary, evidence


def _display_path(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _purge_module(name: str) -> None:
    parts = name.split(".")
    for index in range(len(parts), 0, -1):
        sys.modules.pop(".".join(parts[:index]), None)


def _detector_state(state: str, module_name: str, message: str) -> dict:
    return {"state": state, "module": module_name, "message": message}


def _module_file(root: Path, module_name: str) -> Path | None:
    if not module_name or module_name.startswith("."):
        return None
    return root.joinpath(*module_name.split(".")).with_suffix(".py")


def _iter_text_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS and not name.startswith(".")]
        for filename in filenames:
            path = Path(dirpath) / filename
            if path.suffix.lower() in SKIP_SUFFIXES or filename == ".DS_Store":
                continue
            try:
                if path.stat().st_size > MAX_SCAN_BYTES or path.stat().st_size == 0:
                    continue
            except OSError:
                continue
            yield path
