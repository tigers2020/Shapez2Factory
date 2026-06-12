"""Replay cell semantic read policy — unit contract."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.replay.replay_cell_semantics import (
    NORMALIZED_TRANSPORT_KINDS,
    is_route_tile,
    normalize_project_transport_kind,
    occupant_kind_from_cell,
    resolve_route_transport_kind,
    simulation_for_tile_id,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("none", "none"),
        ("", "none"),
        ("shape_belt", "space_belt"),
        ("belt", "space_belt"),
        ("shape", "space_belt"),
        ("space_belt", "space_belt"),
        ("fluid_pipe", "space_pipe"),
        ("pipe", "space_pipe"),
        ("fluid", "space_pipe"),
        ("space_pipe", "space_pipe"),
        ("unknown_token", "none"),
    ],
)
def test_normalize_project_transport_kind_legacy_and_unknown(raw: str, expected: str) -> None:
    assert normalize_project_transport_kind(raw) == expected
    assert normalize_project_transport_kind(raw) in NORMALIZED_TRANSPORT_KINDS


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        ("shape_miner", "committed_miner"),
        ("fluid_miner", "committed_miner"),
        ("miner", "committed_miner"),
        ("shape_miner_extension", "extension"),
        ("fluid_miner_extension", "extension"),
        ("extension", "extension"),
        ("candidate_miner", "candidate_miner"),
        ("building", "building"),
        ("space_belt", None),
        ("", None),
        ("not_a_kind", None),
    ],
)
def test_occupant_kind_from_cell(kind: str, expected: str | None) -> None:
    assert occupant_kind_from_cell(kind) == expected


@pytest.mark.parametrize(
    ("tile_type", "kind", "is_route"),
    [
        ("SpaceBelt_Forward", "unknown", True),
        ("SpacePipe_Forward", "unknown", True),
        ("", "space_belt", True),
        ("", "space_pipe", True),
        ("PlainTile", "fluid_miner", False),
    ],
)
def test_is_route_tile(tile_type: str, kind: str, is_route: bool) -> None:
    assert is_route_tile(tile_type, kind) is is_route


@pytest.mark.parametrize(
    ("tile_type", "kind", "transport_raw", "expected"),
    [
        ("SpaceBelt_Forward", "", "", "space_belt"),
        ("SpacePipe_Forward", "", "", "space_pipe"),
        ("", "space_belt", "", "space_belt"),
        ("", "space_pipe", "", "space_pipe"),
        ("", "shape_belt", "", "space_belt"),
        ("", "fluid_pipe", "", "space_pipe"),
        ("PlainTile", "unknown", "garbage", "none"),
    ],
)
def test_resolve_route_transport_kind(
    tile_type: str, kind: str, transport_raw: str, expected: str
) -> None:
    result = resolve_route_transport_kind(tile_type, kind, transport_raw)
    assert result == expected
    assert result in NORMALIZED_TRANSPORT_KINDS


def test_simulation_for_tile_id_merger_splitter_and_conveyor() -> None:
    assert simulation_for_tile_id("SpaceBelt_Merger") == "SpaceMergerSimulation"
    assert simulation_for_tile_id("SpacePipe_Splitter") == "SpaceSplitterSimulation"
    assert simulation_for_tile_id("SpaceBelt_Forward") == "SpaceConveyorSimulation"
    assert simulation_for_tile_id(None) is None
    assert simulation_for_tile_id("") is None
