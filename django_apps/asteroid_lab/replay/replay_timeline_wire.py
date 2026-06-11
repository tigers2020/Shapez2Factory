"""Replay timeline wire shapes (JSON projection authority only)."""

from __future__ import annotations

from typing import TypedDict


class ReplayBBoxWire(TypedDict):
    """Inclusive map bounding box in replay timeline wire."""

    min_x: int
    min_y: int
    max_x: int
    max_y: int


__all__ = ["ReplayBBoxWire"]
