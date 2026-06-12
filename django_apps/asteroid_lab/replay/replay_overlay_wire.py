"""Replay overlay cell wire shapes (JSON projection authority only)."""

from __future__ import annotations

from typing import NotRequired, TypedDict


class ReplayOverlayCellWire(TypedDict):
    """One overlay cell row in replay timeline / transient overlay wire."""

    x: int
    y: int
    kind: str
    transport: str
    transport_kind: str
    output_transport_kind: str
    tile_type: str
    rotation: int
    layer: NotRequired[int]
    simulation: NotRequired[str]


__all__ = ["ReplayOverlayCellWire"]
