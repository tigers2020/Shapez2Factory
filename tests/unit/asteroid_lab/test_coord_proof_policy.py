"""G3 proof policy ??island-paste vs world-equivalence tracks."""

from __future__ import annotations

from django_apps.asteroid_lab.reconstruction.acceptance_topology import infer_topology_coord_frame
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.coord_proof_policy import (
    THREE_EXT_MINER_BELT_PROOF,
    FixtureCoordProof,
    island_raw_promotion_allowed,
    lab_solver_optimization_coord_frame,
)


def test_three_ext_fixture_is_island_paste_only() -> None:
    assert THREE_EXT_MINER_BELT_PROOF == FixtureCoordProof.ISLAND_PASTE_ONLY


def test_island_paste_only_allows_island_raw_promotion_without_world_adapter() -> None:
    assert island_raw_promotion_allowed(FixtureCoordProof.ISLAND_PASTE_ONLY)


def test_world_equivalence_track_does_not_allow_island_raw_shortcut() -> None:
    assert not island_raw_promotion_allowed(FixtureCoordProof.REQUIRES_ISLAND_WORLD_EQUIVALENCE)


def test_lab_solver_defaults_to_island_raw_frame() -> None:
    assert lab_solver_optimization_coord_frame(None) == CoordFrame.ISLAND_RAW
    assert lab_solver_optimization_coord_frame({}) == CoordFrame.ISLAND_RAW


def test_lab_solver_honors_explicit_world_raw_override() -> None:
    assert lab_solver_optimization_coord_frame({"coord_frame": "world_raw"}) == CoordFrame.WORLD_RAW


def test_infer_topology_coord_frame_is_island_for_cells() -> None:
    cells = (
        DecodedCellDTO(
            x=1,
            y=2,
            layer=None,
            rotation=0,
            tile_type="",
            cell_kind="asteroid_shape_field",
            transport_kind="none",
            has_nested_blueprint=False,
            nested_entry_count=0,
            nested_type_counts_json={},
            raw_entry_json={},
        ),
    )
    assert infer_topology_coord_frame(cells) == CoordFrame.ISLAND_RAW
