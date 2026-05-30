"""Island vs world topology equivalence — proof gate G3 (PR-D).

Gate closed until an explicit ``island_to_world`` adapter is proven and this module's
xfail markers are removed.
"""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.snapshots.coord_frames import IslandRawCoord
from django_apps.asteroid_lab.snapshots.copy_json_coords import (
    entry_island_raw_coord,
    iter_entry_dicts,
)
from django_apps.shapez_core.services.shapez_copy_decode import decode_shapez2_copy

# fmt: off
_THREE_EXT_MINER_BELT_COPY = (  # noqa: E501
    "SHAPEZ2-4-H4sIAJmKEWoA/5SQwQrCMBBE/2XwGA+1ByFHsUJBQaqIIiJLGzEQ05KkaCn5d9PmInqShYVl38zA9DiAJ0k6Z1hswXtMXNcIcORWka7AkJe1Hh5LcgR+hgw33ypyt9o8LJhulYoL9k6N4EUbBxfPkGlnpLBB2OMIPp0xnEIgwz5krKmrW3fdDbKN1MJkLye0lSHQs8gnf/D/GAewAE8jvmuoFAuh3HVVmyeZ6oM6fbE/1vCX0J3UZLqDMGPGWKj3bwEGAPvbCnpcAQAA"
)
# fmt: on


def _island_coords_from_copy(copy: str) -> frozenset[IslandRawCoord]:
    root = decode_shapez2_copy(copy)
    return frozenset(entry_island_raw_coord(e) for e in iter_entry_dicts(root))


@pytest.mark.xfail(
    reason="G3 gate closed: no island_to_world adapter; world topology not compared yet",
    strict=True,
)
def test_three_ext_copy_island_coords_match_world_evidence_topology() -> None:
    """When proven, island paste coords and world reconstruction mineable sets align."""

    island = _island_coords_from_copy(_THREE_EXT_MINER_BELT_COPY)
    assert len(island) == 5
    pytest.fail("island_to_world adapter not implemented — remove xfail when G3 is green")


def test_equivalence_gate_documents_island_fixture() -> None:
    """Always-on: copy fixture island set is stable (G1 dependency for future G3)."""

    island = _island_coords_from_copy(_THREE_EXT_MINER_BELT_COPY)
    assert island == frozenset(
        {
            IslandRawCoord(-2, 1),
            IslandRawCoord(-1, 1),
            IslandRawCoord(0, 1),
            IslandRawCoord(1, 0),
            IslandRawCoord(1, 1),
        }
    )


def test_island_paste_only_track_does_not_require_world_xfail_test() -> None:
    """G3 partial gate: island paste fixtures use coord_proof_policy, not world adapter."""

    from django_apps.asteroid_lab.snapshots.coord_proof_policy import (
        THREE_EXT_MINER_BELT_PROOF,
        island_raw_promotion_allowed,
    )

    assert island_raw_promotion_allowed(THREE_EXT_MINER_BELT_PROOF)
