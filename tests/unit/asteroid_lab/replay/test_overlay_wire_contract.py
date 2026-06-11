"""Replay overlay wire contract: occupancy transport vs output_transport_kind."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.replay.effective_cell_view import merge_effective_cell_view
from django_apps.asteroid_lab.replay.layer03_overlay_cells import overlay_for_probed
from django_apps.asteroid_lab.replay.overlay_wire_contract import (
    assert_candidate_overlay_wire_contract,
    build_routed_transport_overlay_cell,
    overlay_cell_to_wire_dict,
    profile_to_output_transport_kind,
)
from django_apps.asteroid_lab.replay.runtime_frame_finalize import transient_overlay_cells_to_wire
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import succeeded_probe_at


def test_candidate_miner_overlay_wire_forbids_transport_space_belt() -> None:
    entry = succeeded_probe_at((9, 7))
    wire_rows = transient_overlay_cells_to_wire(overlay_for_probed(entry))
    miner_rows = [row for row in wire_rows if row.get("kind") == "candidate_miner"]
    assert miner_rows, "expected candidate_miner overlay rows"
    for row in miner_rows:
        assert row["transport"] == "none"
        assert row["transport_kind"] == "none"
        assert row["transport"] != "space_belt"
        assert_candidate_overlay_wire_contract(row)


def test_candidate_miner_overlay_wire_allows_output_transport_kind_space_belt() -> None:
    entry = succeeded_probe_at((9, 7))
    wire_rows = transient_overlay_cells_to_wire(overlay_for_probed(entry))
    miner_rows = [row for row in wire_rows if row.get("kind") == "candidate_miner"]
    assert miner_rows
    for row in miner_rows:
        assert row["output_transport_kind"] == "space_belt"


def test_routed_space_belt_tile_keeps_transport_kind_and_tile_id() -> None:
    cell = build_routed_transport_overlay_cell(
        x=3,
        y=4,
        transport_kind="space_belt",
        tile_id="SpaceBelt_LeftTurn",
        rotation=1,
    )
    row = overlay_cell_to_wire_dict(cell)
    assert row["kind"] == "space_belt"
    assert row["transport"] == "space_belt"
    assert row["transport_kind"] == "space_belt"
    assert row["tile_type"] == "SpaceBelt_LeftTurn"
    assert row["output_transport_kind"] == "none"
    assert row["simulation"] == "SpaceConveyorSimulation"


def test_effective_cell_view_merges_legacy_and_new_wire_same_result() -> None:
    full_cell = {
        "x": 9,
        "y": 7,
        "kind": "asteroid_shape_field",
        "transport": "none",
        "layer": 0,
    }
    legacy_overlay = {
        "x": 9,
        "y": 7,
        "kind": "candidate_miner",
        "transport": "shape_belt",
        "rotation": 0,
        "layer": 0,
    }
    new_overlay = {
        "x": 9,
        "y": 7,
        "kind": "candidate_miner",
        "transport": "none",
        "transport_kind": "none",
        "output_transport_kind": "space_belt",
        "rotation": 0,
        "layer": 0,
    }
    legacy_view = merge_effective_cell_view(
        x=9,
        y=7,
        frame_index=38,
        full_cell=full_cell,
        overlay_cells=[legacy_overlay],
    )
    new_view = merge_effective_cell_view(
        x=9,
        y=7,
        frame_index=38,
        full_cell=full_cell,
        overlay_cells=[new_overlay],
    )
    assert legacy_view is not None
    assert new_view is not None
    assert legacy_view.transport_kind == new_view.transport_kind == "none"
    assert legacy_view.output_transport_kind == new_view.output_transport_kind == "space_belt"
    assert legacy_view.occupant_kind == new_view.occupant_kind == "candidate_miner"

    legacy_wire = legacy_view.to_wire()
    new_wire = new_view.to_wire()
    assert legacy_wire["output"] == new_wire["output"]
    assert legacy_wire["transport"] == new_wire["transport"]
    assert "shape_belt" not in str(new_wire)


@pytest.mark.parametrize("legacy_profile", ["shape_belt", "fluid_pipe", "belt", "pipe"])
def test_profile_to_output_transport_kind_rejects_legacy_tokens(legacy_profile: str) -> None:
    with pytest.raises(ValueError, match="legacy tokens must not reach overlay builders"):
        profile_to_output_transport_kind(legacy_profile)


@pytest.mark.parametrize(
    "bad_transport",
    ["space_belt", "space_pipe", "shape_belt", "fluid_pipe"],
)
def test_assert_candidate_overlay_rejects_occupancy_transport(bad_transport: str) -> None:
    with pytest.raises(AssertionError, match="output_transport_kind"):
        assert_candidate_overlay_wire_contract(
            {"kind": "candidate_miner", "transport": bad_transport}
        )
