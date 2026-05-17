"""Unit tests for ``django_apps.asteroid_lab.reconstruction.island``."""

from __future__ import annotations

from django_apps.asteroid_lab.reconstruction.island import stamp_islands_uniform
from django_apps.asteroid_lab.services.dto import DecodedCellDTO


def _cell(
    x: int,
    y: int,
    *,
    tile_type: str = "",
    cell_kind: str = "unknown",
    transport_kind: str = "none",
    raw_entry_json: dict | None = None,
) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=x,
        y=y,
        layer=None,
        rotation=0,
        tile_type=tile_type,
        cell_kind=cell_kind,
        transport_kind=transport_kind,
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json=dict(raw_entry_json or {}),
    )


def test_adjacent_conflicting_original_field_evidence_splits_islands() -> None:
    """Graph drops 4-neighbor edge when endpoints carry conflicting ``asteroid_*`` evidence."""

    shape = _cell(0, 0, cell_kind="asteroid_shape_field")
    fluid = _cell(1, 0, cell_kind="asteroid_fluid_field")
    out = stamp_islands_uniform(
        (shape, fluid),
        original_cells=(shape, fluid),
        removed_building_cells=(),
    )
    by_xy = {(c.x, c.y): c for c in out}
    assert by_xy[(0, 0)].cell_kind == "asteroid_shape_field"
    assert by_xy[(1, 0)].cell_kind == "asteroid_fluid_field"


def test_transport_cells_are_not_stamped_as_asteroid_field() -> None:
    """Transport tiles are excluded from the non-transport island graph."""

    belt = _cell(0, 0, cell_kind="space_belt", transport_kind="shape_belt")
    field = _cell(1, 0, cell_kind="asteroid_shape_field")
    out = stamp_islands_uniform(
        (belt, field),
        original_cells=(belt, field),
        removed_building_cells=(),
    )
    by_xy = {(c.x, c.y): c for c in out}
    assert by_xy[(0, 0)].cell_kind == "space_belt"
    assert by_xy[(1, 0)].cell_kind == "asteroid_shape_field"


def test_disconnected_components_resolve_field_kind_independently() -> None:
    """A transport column prevents 4-connectivity; each side picks its own island kind."""

    left_shape = _cell(0, 1, cell_kind="asteroid_shape_field")
    pipe = _cell(1, 1, cell_kind="space_pipe", transport_kind="fluid_pipe")
    right_fluid_a = _cell(2, 1, cell_kind="asteroid_fluid_field")
    right_fluid_b = _cell(3, 1, cell_kind="asteroid_fluid_field")
    out = stamp_islands_uniform(
        (left_shape, pipe, right_fluid_a, right_fluid_b),
        original_cells=(left_shape, pipe, right_fluid_a, right_fluid_b),
        removed_building_cells=(),
    )
    by_xy = {(c.x, c.y): c for c in out}
    assert by_xy[(0, 1)].cell_kind == "asteroid_shape_field"
    assert by_xy[(1, 1)].cell_kind == "space_pipe"
    assert by_xy[(2, 1)].cell_kind == "asteroid_fluid_field"
    assert by_xy[(3, 1)].cell_kind == "asteroid_fluid_field"


def test_stamp_islands_uniform_preserves_cell_count_and_keys() -> None:
    """Island stamp is a cell_kind overlay; input length and (x,y,layer) keys are unchanged."""

    belt = _cell(0, 0, cell_kind="space_belt", transport_kind="shape_belt")
    ring = _cell(1, 0, cell_kind="asteroid_shape_field")
    fill = _cell(
        2,
        0,
        cell_kind="asteroid_shape_field",
        raw_entry_json={"_replay_synthetic": True, "_reconstruction": "topology_fill"},
    )
    before = (belt, ring, fill)
    after = stamp_islands_uniform(
        before,
        original_cells=(ring,),
        removed_building_cells=(),
    )
    assert len(after) == len(before)
    assert {(c.x, c.y, c.layer) for c in after} == {(c.x, c.y, c.layer) for c in before}


def test_neighbor_vote_includes_four_neighbors_of_island_cells() -> None:
    """Original evidence on a wall-only neighbor coordinate still counts for an interior hole."""

    hole = _cell(1, 1, cell_kind="asteroid_shape_field", tile_type="SynthHole")
    fluid_wall = _cell(1, 0, cell_kind="asteroid_fluid_field")
    out = stamp_islands_uniform(
        (fluid_wall, hole),
        original_cells=(fluid_wall,),
        removed_building_cells=(),
    )
    h = next(c for c in out if c.x == 1 and c.y == 1)
    assert h.cell_kind == "asteroid_fluid_field"
