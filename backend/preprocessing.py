"""Normalize auth events before detection.

The locked scenario contract passes a list of objects with event_id, user,
action, and optional timestamp, source, and message. This module checks that
shape. It does not read files, start processes, or interpret message text.
"""

from __future__ import annotations

KNOWN_ACTIONS = frozenset({"login_failed", "login_success"})


def prepare_events(events: object) -> dict:
    """Return normalized events plus warnings.

    ``ok`` is false only when the top-level value is not a list. Individual
    bad records are skipped so one invalid row does not hide the rest.
    """
    if not isinstance(events, list):
        return {
            "ok": False,
            "events": [],
            "warnings": ["events must be a list"],
        }
    normalized: list[dict] = []
    warnings: list[str] = []
    for index, raw in enumerate(events):
        record, warning = _normalize_record(index, raw)
        if warning:
            warnings.append(warning)
        if record is not None:
            normalized.append(record)
    return {"ok": True, "events": normalized, "warnings": warnings}


def _normalize_record(index: int, raw: object) -> tuple[dict | None, str | None]:
    if not isinstance(raw, dict):
        return None, f"row {index}: skipped non-object"
    event_id = _text(raw.get("event_id"))
    user = _text(raw.get("user"))
    action = _text(raw.get("action"))
    if not event_id or not user or not action:
        return None, f"row {index}: skipped record missing event_id, user, or action"
    if action not in KNOWN_ACTIONS:
        return None, f"row {index}: skipped unsupported action"
    record = {
        "event_id": event_id,
        "user": user,
        "action": action,
        "timestamp": _text(raw.get("timestamp")),
        "source": _text(raw.get("source")),
        "message": raw.get("message") if isinstance(raw.get("message"), str) else "",
    }
    return record, None


def _text(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    return ""
