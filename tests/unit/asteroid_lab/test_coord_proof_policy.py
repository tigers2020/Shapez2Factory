"""G3 proof policy — island-paste vs world-equivalence tracks."""

from __future__ import annotations

from django_apps.asteroid_lab.snapshots.coord_proof_policy import (
    THREE_EXT_MINER_BELT_PROOF,
    FixtureCoordProof,
    island_raw_promotion_allowed,
)


def test_three_ext_fixture_is_island_paste_only() -> None:
    assert THREE_EXT_MINER_BELT_PROOF == FixtureCoordProof.ISLAND_PASTE_ONLY


def test_island_paste_only_allows_island_raw_promotion_without_world_adapter() -> None:
    assert island_raw_promotion_allowed(FixtureCoordProof.ISLAND_PASTE_ONLY)


def test_world_equivalence_track_does_not_allow_island_raw_shortcut() -> None:
    assert not island_raw_promotion_allowed(
        FixtureCoordProof.REQUIRES_ISLAND_WORLD_EQUIVALENCE
    )
