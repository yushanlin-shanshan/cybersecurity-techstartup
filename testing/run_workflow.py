#!/usr/bin/env python3
"""Run the testing workflow with one command.

    python3 testing/run_workflow.py

Exit 0 means the workflow itself is healthy. If backend/detection.py does not
define detect() yet, scenarios stay blocked and no detection score is printed.
Exit 1 means a secret was found, the harness failed, or a real detect()
disagreed with the synthetic scenario contract.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import workflow_lib

ROOT = workflow_lib.ROOT
UNIT_TESTS = (
    ROOT / "testing" / "test_detection_metrics.py",
    ROOT / "testing" / "test_workflow.py",
)
REPORT_PATH = ROOT / "testing" / "output" / "workflow_report.json"


def run_unit_tests() -> dict:
    results = []
    for path in UNIT_TESTS:
        completed = subprocess.run(
            [sys.executable, str(path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        results.append(
            {
                "file": str(path.relative_to(ROOT)),
                "exit_code": completed.returncode,
                "stdout_tail": "\n".join(completed.stdout.splitlines()[-8:]),
                "stderr_tail": "\n".join(completed.stderr.splitlines()[-8:]),
            }
        )
    return {
        "passed": all(item["exit_code"] == 0 for item in results),
        "results": results,
    }


def main() -> int:
    unit = run_unit_tests()
    report = workflow_lib.build_report(ROOT)
    report["unit_tests"] = unit
    code = workflow_lib.exit_code(report, unit_tests_passed=unit["passed"])
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(workflow_lib.format_summary(report, code))
    print(f"report: {REPORT_PATH.relative_to(ROOT)}")
    if not unit["passed"]:
        print("unit tests failed:")
        for item in unit["results"]:
            if item["exit_code"] != 0:
                print(f"  {item['file']} exit {item['exit_code']}")
                if item["stderr_tail"]:
                    print(item["stderr_tail"])
                if item["stdout_tail"]:
                    print(item["stdout_tail"])
    return code


if __name__ == "__main__":
    sys.exit(main())
