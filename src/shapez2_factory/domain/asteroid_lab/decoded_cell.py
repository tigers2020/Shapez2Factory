"""``DecodedCellDTO`` — one top-level ``BP.Entries`` decoded cell row (A5).

Pure structural DTO (no Django). Moved to core in PR-CLI-2c so the pure reconstruction / cleanup /
merge pipeline can consume it without dragging the Django ``services`` package. ``services/dto.py``
re-exports this name for backward compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class DecodedCellDTO:
    """One top-level ``BP.Entries`` cell row (A5); nested ``B.Entries`` are summary-only."""

    x: int
    y: int
    layer: int | None
    rotation: int
    tile_type: str
    cell_kind: str
    transport_kind: str
    has_nested_blueprint: bool
    nested_entry_count: int
    nested_type_counts_json: dict[str, int]
    raw_entry_json: dict[str, Any]


__all__ = ["DecodedCellDTO"]
