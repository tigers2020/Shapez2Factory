"""Tagged map coordinate frames (island copy, world evidence).

Normative spec: ``documents/superpowers/specs/2026-05-23-coordinate-tagged-frames-design.md``.

New boundaries should use the frozen dataclasses below.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

_MSG_WORLD_NO_X0 = "Shapez2 world grid has no x == 0 coordinate"


class CoordFrame(StrEnum):
    """Reserved for ``OptimizationInput.coord_frame`` (PR-E). Document-only until then."""

    ISLAND_RAW = "island_raw"
    WORLD_RAW = "world_raw"


@dataclass(frozen=True, slots=True)
class IslandRawCoord:
    """Copy JSON / paste-local ``X``, ``Y`` (``X == 0`` valid)."""

    x: int
    y: int


@dataclass(frozen=True, slots=True)
class WorldRawCoord:
    """Asteroid / lab world evidence (no ``x == 0`` column)."""

    x: int
    y: int

    def __post_init__(self) -> None:
        if self.x == 0:
            raise ValueError(_MSG_WORLD_NO_X0)


def neighbors4_island(
    c: IslandRawCoord,
) -> tuple[IslandRawCoord, IslandRawCoord, IslandRawCoord, IslandRawCoord]:
    """Standard 4-neighbors on island-local integer grid."""

    x, y = c.x, c.y
    return (
        IslandRawCoord(x - 1, y),
        IslandRawCoord(x + 1, y),
        IslandRawCoord(x, y - 1),
        IslandRawCoord(x, y + 1),
    )


def island_to_tuple(c: IslandRawCoord) -> tuple[int, int]:
    return (c.x, c.y)


__all__ = [
    "CoordFrame",
    "IslandRawCoord",
    "WorldRawCoord",
    "island_to_tuple",
    "neighbors4_island",
]
