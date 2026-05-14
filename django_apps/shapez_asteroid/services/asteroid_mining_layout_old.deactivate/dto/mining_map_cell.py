"""Shared mining-map row DTO types.

The live solver still mutates plain dict rows. ``MiningMapCell`` documents the
known wire keys while ``MutableMiningMapCell`` preserves the current mutable
runtime contract.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord

type MiningMapRole = Literal["inferred", "occupied", "belt", "pipe"]


class MiningMapCell(TypedDict, total=False):
    """Known JSON keys for one ``mining_map`` row."""

    x: int
    y: int
    role: MiningMapRole | str
    kind: str
    layout_kind: str
    r: int
    fixed_output_stub: bool
    pass12_fixed_output_stub: bool
    placement_state: str
    placement_commit_state: str


# 현재 write 경로는 dict row를 직접 수정하므로 mutable 별칭을 별도로 유지한다.
type MutableMiningMapCell = dict[str, Any]
type MiningMapRows = list[MutableMiningMapCell]
type MiningMapCellsByCoord = dict[Coord, MutableMiningMapCell]

__all__ = [
    "MiningMapCell",
    "MiningMapCellsByCoord",
    "MiningMapRole",
    "MiningMapRows",
    "MutableMiningMapCell",
]
