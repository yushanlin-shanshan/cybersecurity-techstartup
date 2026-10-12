"""Deterministic failed-login detector.

The published rule is:

- Flag when one user has at least five login_failed events and a later
  login_success for that same user.
- Fewer failures, or failures with no later success, stay benign.
- Message text is not evidence and cannot change the decision.
- A flag means suspicious activity. It does not mean confirmed compromise.

List order is the sequence. Timestamps are kept for analysts and are not
compared. Source address is not part of the rule. Repeated event ids are
counted once per list item because the contract does not define deduplication.

This module does not import the testing package or call a model.
"""

from __future__ import annotations

try:
    from backend.preprocessing import prepare_events
except ImportError:  # pragma: no cover - direct script execution
    from preprocessing import prepare_events

MIN_FAILURES = 5
RULE_NAME = "failed_logins_then_success"


def detect(events: list[dict]) -> dict:
    prepared = prepare_events(events)
    if not prepared["ok"]:
        return _result(
            predicted="benign",
            assessment="not_assessed",
            summary="input rejected; events must be a list",
            evidence=[],
            warnings=prepared["warnings"],
            matched_users=0,
        )
    matched = _match(prepared["events"])
    evidence = [event_id for ids in matched.values() for event_id in ids]
    if matched:
        noun = "user" if len(matched) == 1 else "users"
        summary = (
            f"suspicious: {len(matched)} {noun} had at least {MIN_FAILURES} "
            "failed logins followed by a later success"
        )
        return _result(
            predicted="flagged",
            assessment="suspicious",
            summary=summary,
            evidence=evidence,
            warnings=prepared["warnings"],
            matched_users=len(matched),
        )
    return _result(
        predicted="benign",
        assessment="no_matching_pattern",
        summary="no matching failed-login-then-success pattern",
        evidence=[],
        warnings=prepared["warnings"],
        matched_users=0,
    )


def _match(events: list[dict]) -> dict[str, list[str]]:
    failures: dict[str, list[str]] = {}
    matched: dict[str, list[str]] = {}
    for event in events:
        user = event["user"]
        event_id = event["event_id"]
        if event["action"] == "login_failed":
            failures.setdefault(user, []).append(event_id)
            continue
        if event["action"] != "login_success" or user in matched:
            continue
        prior_failures = failures.get(user, [])
        if len(prior_failures) >= MIN_FAILURES:
            matched[user] = [*prior_failures, event_id]
    return matched


def _result(
    *,
    predicted: str,
    assessment: str,
    summary: str,
    evidence: list[str],
    warnings: list[str],
    matched_users: int,
) -> dict:
    return {
        "predicted": predicted,
        "assessment": assessment,
        "summary": summary,
        "evidence": evidence,
        "warnings": list(warnings),
        "rule": RULE_NAME,
        "threshold": MIN_FAILURES,
        "matched_users": matched_users,
    }
