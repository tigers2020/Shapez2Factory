"""Enums for genetic sample gene templates (admin / fixtures; not solver runtime)."""

from __future__ import annotations

from enum import StrEnum


class Direction(StrEnum):
    """Cardinal direction on the raw island grid."""

    N = "n"
    E = "e"
    S = "s"
    W = "w"


__all__ = ["Direction"]
