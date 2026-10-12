"""Reference rule used only to prove the testing harness can score a detector.

This is not the product detector. backend/detection.py is the teammate's module.
The workflow does not call this file unless DETECTOR_MODULE points at it.
"""

from __future__ import annotations

MIN_FAILURES = 5


def detect(events: list[dict]) -> dict:
    if not isinstance(events, list):
        raise TypeError("events must be a list")
    failures_by_user: dict[str, int] = {}
    success_by_user: dict[str, bool] = {}
    evidence: list[str] = []
    for event in events:
        if not isinstance(event, dict):
            raise TypeError("each event must be an object")
        user = str(event.get("user", ""))
        action = str(event.get("action", ""))
        event_id = str(event.get("event_id", ""))
        if action == "login_failed":
            failures_by_user[user] = failures_by_user.get(user, 0) + 1
            if event_id:
                evidence.append(event_id)
        elif action == "login_success":
            success_by_user[user] = True
            if event_id:
                evidence.append(event_id)
    flagged_users = [
        user
        for user, count in failures_by_user.items()
        if count >= MIN_FAILURES and success_by_user.get(user, False)
    ]
    if flagged_users:
        return {
            "predicted": "flagged",
            "summary": "suspicious: repeated failed logins followed by a success",
            "evidence": evidence,
        }
    return {
        "predicted": "benign",
        "summary": "no failed-login-then-success pattern",
        "evidence": evidence,
    }
