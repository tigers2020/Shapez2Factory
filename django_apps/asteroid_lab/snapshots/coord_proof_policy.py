"""Fixture-level coordinate proof policy (G3 gate tracks).

``ISLAND_PASTE_ONLY`` fixtures may promote to ``CoordFrame.ISLAND_RAW`` without a full
``island_to_world`` equivalence proof. ``REQUIRES_ISLAND_WORLD_EQUIVALENCE`` fixtures
must pass ``test_coordinate_frame_equivalence`` (world topology match) before PR-E2
uses ``CoordFrame.WORLD_RAW``.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame


class FixtureCoordProof(StrEnum):
    ISLAND_PASTE_ONLY = "island_paste_only"
    REQUIRES_ISLAND_WORLD_EQUIVALENCE = "requires_island_world_equivalence"


# In-game paste fixture (see test_copy_json_island_local_coords).
THREE_EXT_MINER_BELT_PROOF = FixtureCoordProof.ISLAND_PASTE_ONLY


def island_raw_promotion_allowed(proof: FixtureCoordProof) -> bool:
    """Whether PR-E2 may set ``CoordFrame.ISLAND_RAW`` without world equivalence."""

    return proof == FixtureCoordProof.ISLAND_PASTE_ONLY


def lab_solver_optimization_coord_frame(run_config: dict[str, Any] | None) -> CoordFrame:
    """Default RTTP lab solver optimization frame (PR-F: island-local, not server dense).

    ``run_config["coord_frame"]`` may be ``CoordFrame`` value strings. Use
    ``"server_dense"`` only for explicit legacy / regression comparison.
    """

    if run_config is None:
        return CoordFrame.ISLAND_RAW
    raw = run_config.get("coord_frame")
    if raw in (CoordFrame.SERVER_DENSE.value, "server_dense"):
        return CoordFrame.SERVER_DENSE
    if raw in (CoordFrame.WORLD_RAW.value, "world_raw"):
        return CoordFrame.WORLD_RAW
    if raw in (CoordFrame.ISLAND_RAW.value, "island_raw"):
        return CoordFrame.ISLAND_RAW
    return CoordFrame.ISLAND_RAW


__all__ = [
    "FixtureCoordProof",
    "THREE_EXT_MINER_BELT_PROOF",
    "island_raw_promotion_allowed",
    "lab_solver_optimization_coord_frame",
]
