"""Fixture-level coordinate proof policy (G3 gate tracks).

``ISLAND_PASTE_ONLY`` fixtures may promote to ``CoordFrame.ISLAND_RAW`` without a full
``island_to_world`` equivalence proof. ``REQUIRES_ISLAND_WORLD_EQUIVALENCE`` fixtures
must pass ``test_coordinate_frame_equivalence`` (world topology match) before PR-E2
uses ``CoordFrame.WORLD_RAW``.
"""

from __future__ import annotations

from enum import StrEnum


class FixtureCoordProof(StrEnum):
    ISLAND_PASTE_ONLY = "island_paste_only"
    REQUIRES_ISLAND_WORLD_EQUIVALENCE = "requires_island_world_equivalence"


# In-game paste fixture (see test_copy_json_island_local_coords).
THREE_EXT_MINER_BELT_PROOF = FixtureCoordProof.ISLAND_PASTE_ONLY


def island_raw_promotion_allowed(proof: FixtureCoordProof) -> bool:
    """Whether PR-E2 may set ``CoordFrame.ISLAND_RAW`` without world equivalence."""

    return proof == FixtureCoordProof.ISLAND_PASTE_ONLY


__all__ = [
    "FixtureCoordProof",
    "THREE_EXT_MINER_BELT_PROOF",
    "island_raw_promotion_allowed",
]
