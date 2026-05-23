"""Tagged map coordinate frames (island copy, world evidence, deprecated server dense).

Normative spec: ``docs/superpowers/specs/2026-05-23-coordinate-tagged-frames-design.md``.

During migration, ``grid_contract.Coord`` remains ``tuple[int, int]`` with **ServerCoord**
semantics until PR-E/F. New boundaries should use the frozen dataclasses below.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

_MSG_WORLD_NO_X0 = "Shapez2 world grid has no x == 0 coordinate"


class CoordFrame(StrEnum):
    """Reserved for ``OptimizationInput.coord_frame`` (PR-E). Document-only until then."""

    SERVER_DENSE = "server_dense"
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


@dataclass(frozen=True, slots=True)
class ServerCoord:
    """Deprecated dense bbox ``server_x`` / ``server_y`` until PR-F."""

    x: int
    y: int


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


def server_coord_to_tuple(c: ServerCoord) -> tuple[int, int]:
    return (c.x, c.y)


__all__ = [
    "CoordFrame",
    "IslandRawCoord",
    "ServerCoord",
    "WorldRawCoord",
    "island_to_tuple",
    "neighbors4_island",
    "server_coord_to_tuple",
]
