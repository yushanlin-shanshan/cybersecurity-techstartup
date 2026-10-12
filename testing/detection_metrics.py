#!/usr/bin/env python3
"""Score already-produced detection predictions against caller-supplied labels.

This module does not detect threats and does not ship a dataset. It only
computes precision, recall, F1, and false-positive rate from a CSV that
already contains ground truth and predictions.

Positive class means the detector flagged the event. That is not the same
thing as confirmed account compromise.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence, TextIO


POSITIVE = {
    "1",
    "true",
    "yes",
    "positive",
    "flagged",
    "malicious",
    "suspicious",
    "attack",
}
NEGATIVE = {
    "0",
    "false",
    "no",
    "negative",
    "benign",
    "legitimate",
    "not_flagged",
    "clean",
}

REQUIRED_COLUMNS = ("ground_truth", "predicted")


class EvaluationError(Exception):
    """The evaluation input cannot be scored."""


@dataclass(frozen=True)
class Confusion:
    tp: int = 0
    fp: int = 0
    tn: int = 0
    fn: int = 0

    @property
    def evaluated(self) -> int:
        return self.tp + self.fp + self.tn + self.fn

    def as_dict(self) -> dict[str, int | float | None | str]:
        precision, precision_note = _ratio(self.tp, self.tp + self.fp, "no predicted positives")
        recall, recall_note = _ratio(self.tp, self.tp + self.fn, "no positive ground-truth labels")
        fpr, fpr_note = _ratio(self.fp, self.fp + self.tn, "no negative ground-truth labels")
        f1, f1_note = _f1(precision, recall, precision_note, recall_note)
        return {
            "evaluated": self.evaluated,
            "tp": self.tp,
            "fp": self.fp,
            "tn": self.tn,
            "fn": self.fn,
            "positive_labels": self.tp + self.fn,
            "negative_labels": self.tn + self.fp,
            "precision": precision,
            "precision_note": precision_note,
            "recall": recall,
            "recall_note": recall_note,
            "f1": f1,
            "f1_note": f1_note,
            "false_positive_rate": fpr,
            "false_positive_rate_note": fpr_note,
        }


def parse_binary(value: str, *, row_number: int, column: str) -> bool:
    normalized = value.strip().lower()
    if normalized in POSITIVE:
        return True
    if normalized in NEGATIVE:
        return False
    raise EvaluationError(
        f"row {row_number}: {column}={value!r} is not a recognized binary label"
    )


def confusion_from_pairs(pairs: Iterable[tuple[bool, bool]]) -> Confusion:
    tp = fp = tn = fn = 0
    for truth, predicted in pairs:
        if truth and predicted:
            tp += 1
        elif truth and not predicted:
            fn += 1
        elif not truth and predicted:
            fp += 1
        else:
            tn += 1
    return Confusion(tp=tp, fp=fp, tn=tn, fn=fn)


def load_rows(handle: TextIO) -> list[dict[str, str]]:
    reader = csv.DictReader(handle)
    if reader.fieldnames is None:
        raise EvaluationError("CSV has no header row")
    missing = [name for name in REQUIRED_COLUMNS if name not in reader.fieldnames]
    if missing:
        raise EvaluationError(
            "CSV is missing required columns: " + ", ".join(missing)
        )
    rows: list[dict[str, str]] = []
    for raw in reader:
        if raw is None:
            continue
        if all((value is None or str(value).strip() == "") for value in raw.values()):
            continue
        rows.append({key: "" if value is None else value for key, value in raw.items()})
    if not rows:
        raise EvaluationError("CSV has a header but no evaluable rows")
    return rows


def score_rows(rows: Sequence[Mapping[str, str]]) -> dict:
    seen_ids: dict[str, int] = {}
    overall_pairs: list[tuple[bool, bool]] = []
    by_category: dict[str, list[tuple[bool, bool]]] = defaultdict(list)
    has_category = any("category" in row and row["category"].strip() for row in rows)

    for offset, row in enumerate(rows, start=2):
        event_id = row.get("event_id", "").strip()
        if event_id:
            if event_id in seen_ids:
                raise EvaluationError(
                    f"row {offset}: duplicate event_id {event_id!r} "
                    f"(first seen on row {seen_ids[event_id]})"
                )
            seen_ids[event_id] = offset
        truth = parse_binary(row.get("ground_truth", ""), row_number=offset, column="ground_truth")
        predicted = parse_binary(row.get("predicted", ""), row_number=offset, column="predicted")
        overall_pairs.append((truth, predicted))
        if has_category:
            category = row.get("category", "").strip() or "(uncategorized)"
            by_category[category].append((truth, predicted))

    result = {
        "source": "caller-supplied labels",
        "claim": (
            "These figures score the supplied predictions. "
            "They are not measured accuracy of an application detector "
            "unless the caller passed that detector's held-out output."
        ),
        "positive_class": "flagged",
        "label_aliases": {
            "positive": sorted(POSITIVE),
            "negative": sorted(NEGATIVE),
        },
        "overall": confusion_from_pairs(overall_pairs).as_dict(),
    }
    if has_category:
        result["by_category"] = {
            name: confusion_from_pairs(pairs).as_dict()
            for name, pairs in sorted(by_category.items())
        }
    return result


def evaluate_csv(path: str) -> dict:
    try:
        with open(path, newline="", encoding="utf-8") as handle:
            rows = load_rows(handle)
    except FileNotFoundError as exc:
        raise EvaluationError(f"labeled CSV not found: {path}") from exc
    except UnicodeDecodeError as exc:
        raise EvaluationError(f"CSV is not valid UTF-8: {path}") from exc
    result = score_rows(rows)
    result["path"] = path
    return result


def self_check() -> dict:
    """Score an in-memory fixture to verify the formulas. Not product accuracy."""
    rows = [
        {"event_id": "s1", "ground_truth": "flagged", "predicted": "flagged", "category": "demo"},
        {"event_id": "s2", "ground_truth": "1", "predicted": "0", "category": "demo"},
        {"event_id": "s3", "ground_truth": "benign", "predicted": "suspicious", "category": "demo"},
        {"event_id": "s4", "ground_truth": "not_flagged", "predicted": "benign", "category": "demo"},
    ]
    result = score_rows(rows)
    result["source"] = "in-memory synthetic calculator fixture"
    result["claim"] = (
        "Synthetic calculator self-check only. "
        "This is not detection performance of the application."
    )
    expected = {"tp": 1, "fp": 1, "tn": 1, "fn": 1, "precision": 0.5, "recall": 0.5, "f1": 0.5}
    overall = result["overall"]
    mismatches = {
        key: {"expected": value, "actual": overall[key]}
        for key, value in expected.items()
        if overall[key] != value
    }
    if mismatches:
        raise EvaluationError(f"self-check mismatch: {mismatches}")
    result["self_check"] = "passed"
    return result


def format_report(result: dict) -> str:
    lines = [
        f"source: {result['source']}",
        f"claim: {result['claim']}",
        _format_block("overall", result["overall"]),
    ]
    for name, block in result.get("by_category", {}).items():
        lines.append(_format_block(f"category {name}", block))
    if result.get("self_check"):
        lines.append(f"self_check: {result['self_check']}")
    return "\n".join(lines)


def _format_block(title: str, block: Mapping) -> str:
    def cell(key: str) -> str:
        value = block[key]
        note = block.get(f"{key}_note")
        if value is None:
            return f"undefined ({note})"
        if isinstance(value, float):
            rendered = f"{value:.4f}"
            if note:
                return f"{rendered} ({note})"
            return rendered
        return str(value)

    return "\n".join(
        [
            f"[{title}]",
            f"  evaluated: {block['evaluated']}",
            f"  positive_labels: {block['positive_labels']}",
            f"  negative_labels: {block['negative_labels']}",
            f"  tp: {block['tp']}  fp: {block['fp']}  tn: {block['tn']}  fn: {block['fn']}",
            f"  precision: {cell('precision')}",
            f"  recall: {cell('recall')}",
            f"  f1: {cell('f1')}",
            f"  false_positive_rate: {cell('false_positive_rate')}",
        ]
    )


def _ratio(numerator: int, denominator: int, undefined_reason: str) -> tuple[float | None, str]:
    if denominator == 0:
        return None, undefined_reason
    return numerator / denominator, ""


def _f1(
    precision: float | None,
    recall: float | None,
    precision_note: str,
    recall_note: str,
) -> tuple[float | None, str]:
    if precision is None or recall is None:
        missing = []
        if precision is None:
            missing.append(f"precision undefined ({precision_note})")
        if recall is None:
            missing.append(f"recall undefined ({recall_note})")
        return None, "; ".join(missing)
    if precision + recall == 0:
        return None, "precision and recall are both zero"
    return (2 * precision * recall) / (precision + recall), ""


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compute TP, FP, TN, FN, precision, recall, F1, and false-positive "
            "rate from a CSV with ground_truth and predicted columns. "
            "Does not invent labels or score a missing detector."
        )
    )
    parser.add_argument(
        "csv_path",
        nargs="?",
        help="UTF-8 CSV with ground_truth and predicted columns",
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="Score a built-in 4-row synthetic fixture and exit",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text")
    args = parser.parse_args(argv)

    try:
        if args.self_check:
            result = self_check()
        elif not args.csv_path:
            raise EvaluationError(
                "no labeled CSV provided; detection metrics were not computed. "
                "Pass a CSV with ground_truth and predicted columns, or --self-check "
                "to verify the calculator only."
            )
        else:
            result = evaluate_csv(args.csv_path)
    except EvaluationError as exc:
        print(f"evaluation blocked: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(format_report(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
