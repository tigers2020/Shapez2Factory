"""EffectiveCellView merge adapter contract."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.replay.effective_cell_view import (
    merge_effective_cell_view,
    normalize_project_transport_kind,
    simulation_for_tile_id,
)
from django_apps.asteroid_lab.replay.effective_cell_wire import effective_cell_to_wire


def test_normalize_maps_legacy_shape_belt_to_space_belt() -> None:
    assert normalize_project_transport_kind("shape_belt") == "space_belt"
    assert normalize_project_transport_kind("fluid_pipe") == "space_pipe"


def test_merge_candidate_miner_new_wire_uses_output_transport_kind() -> None:
    view = merge_effective_cell_view(
        x=9,
        y=7,
        frame_index=38,
        full_cell={
            "x": 9,
            "y": 7,
            "kind": "asteroid_shape_field",
            "transport": "none",
            "layer": 0,
        },
        overlay_cells=[
            {
                "x": 9,
                "y": 7,
                "kind": "candidate_miner",
                "transport": "none",
                "output_transport_kind": "space_belt",
                "rotation": 0,
                "layer": 0,
            }
        ],
    )
    assert view is not None
    assert view.transport_kind == "none"
    assert view.output_transport_kind == "space_belt"
    wire = effective_cell_to_wire(view)
    assert wire["output"]["transport_kind"] == "space_belt"
    assert wire["transport"]["kind"] == "none"


def test_merge_candidate_miner_overlay_does_not_claim_transport_tile() -> None:
    view = merge_effective_cell_view(
        x=9,
        y=7,
        frame_index=38,
        full_cell={
            "x": 9,
            "y": 7,
            "kind": "asteroid_shape_field",
            "transport": "none",
            "layer": 0,
        },
        overlay_cells=[
            {
                "x": 9,
                "y": 7,
                "kind": "candidate_miner",
                "transport": "shape_belt",
                "rotation": 0,
                "layer": 0,
            }
        ],
    )
    assert view is not None
    assert view.terrain_kind == "asteroid_shape_field"
    assert view.occupant_kind == "candidate_miner"
    assert view.transport_kind == "none"
    assert view.transport_tile_id is None
    assert view.simulation is None
    assert view.output_transport_kind == "space_belt"
    assert view.occupant_rotation == 0


def test_merge_routed_space_belt_tile() -> None:
    view = merge_effective_cell_view(
        x=3,
        y=4,
        overlay_cells=[
            {
                "x": 3,
                "y": 4,
                "kind": "space_belt",
                "tile_type": "SpaceBelt_LeftTurn",
                "transport": "space_belt",
                "rotation": 1,
            }
        ],
    )
    assert view is not None
    assert view.transport_kind == "space_belt"
    assert view.transport_tile_id == "SpaceBelt_LeftTurn"
    assert view.simulation == "SpaceConveyorSimulation"


@pytest.mark.parametrize(
    ("tile_id", "expected_sim"),
    [
        ("SpaceBelt_LeftFwdMerger", "SpaceMergerSimulation"),
        ("SpacePipe_YSplitter", "SpaceSplitterSimulation"),
    ],
)
def test_merge_simulation_family_for_merger_splitter(tile_id: str, expected_sim: str) -> None:
    assert simulation_for_tile_id(tile_id) == expected_sim
    view = merge_effective_cell_view(
        x=1,
        y=1,
        overlay_cells=[
            {
                "x": 1,
                "y": 1,
                "kind": "space_belt" if tile_id.startswith("SpaceBelt") else "space_pipe",
                "tile_type": tile_id,
            }
        ],
    )
    assert view is not None
    assert view.simulation == expected_sim
