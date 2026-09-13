"""Info.confirmed status: waiting, accept, reject."""

from __future__ import annotations

from typing import Any

WAITING = "waiting"
ACCEPT = "accept"
REJECT = "reject"

CHOICES = [
    (WAITING, "Waiting"),
    (ACCEPT, "Accept"),
    (REJECT, "Reject"),
]

ALL_VALUES = frozenset({WAITING, ACCEPT, REJECT})


def is_accept(status: str | None) -> bool:
    return status == ACCEPT


def is_reject(status: str | None) -> bool:
    return status == REJECT


def is_waiting(status: str | None) -> bool:
    return status in (None, "", WAITING)


def normalize_status(value: Any, *, default: str = WAITING) -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return ACCEPT if value else REJECT
    raw = str(value).strip().lower()
    if raw in ("true", "1", "yes", "accept", "approved", "confirm"):
        return ACCEPT
    if raw in ("false", "0", "no", "reject", "rejected"):
        return REJECT
    if raw in ("wait", "waiting", "pending"):
        return WAITING
    if raw in ALL_VALUES:
        return raw
    return default


def status_from_request(data: dict, *, default: str = ACCEPT) -> str:
    """Parse `status` or legacy `confirmed` from request body."""
    if "status" in data:
        return normalize_status(data.get("status"), default=default)
    if "confirmed" in data:
        return normalize_status(data.get("confirmed"), default=default)
    return default


def next_toggle_status(current: str | None) -> str:
    """Cycle: waiting → accept → reject → waiting."""
    if is_waiting(current):
        return ACCEPT
    if is_accept(current):
        return REJECT
    return WAITING
