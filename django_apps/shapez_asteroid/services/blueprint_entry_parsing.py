"""Small helpers for decoded blueprint entry fields (X, Y, R, etc.)."""

from __future__ import annotations

from typing import Any


def int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
