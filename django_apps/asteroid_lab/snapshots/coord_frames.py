"""Shim: relocated to ``shapez2_factory.domain.asteroid_lab.coord_frames`` (PR-CLI-2a).

Re-exports the pure core coordinate frames so existing ``django_apps`` imports keep working.
Import the core module directly in new code.
"""

from __future__ import annotations

from shapez2_factory.domain.asteroid_lab.coord_frames import (
    CoordFrame,
    IslandRawCoord,
    WorldRawCoord,
    island_to_tuple,
    neighbors4_island,
)

__all__ = [
    "CoordFrame",
    "IslandRawCoord",
    "WorldRawCoord",
    "island_to_tuple",
    "neighbors4_island",
]
