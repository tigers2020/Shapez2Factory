"""Layer 03 rim anchor scan — solver-frame anchor enumeration (spec R1 / D1)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.rim_anchor_scan import (  # noqa: E501
    RimAnchor,
    scan_rim_anchors,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import golden_5x5_complete_map

# golden_5x5_complete_map: solid 5x5 shape field block at x,y in [2, 6].
_FIELD_ORIGIN = 2
_FIELD_SIZE = 5
_FIELD_MAX = _FIELD_ORIGIN + _FIELD_SIZE - 1  # 6


def _expected_perimeter_coords() -> set[tuple[int, int]]:
    """Independent geometric oracle: a solid block's rim is its perimeter ring."""

    perimeter: set[tuple[int, int]] = set()
    for x in range(_FIELD_ORIGIN, _FIELD_ORIGIN + _FIELD_SIZE):
        for y in range(_FIELD_ORIGIN, _FIELD_ORIGIN + _FIELD_SIZE):
            if x in (_FIELD_ORIGIN, _FIELD_MAX) or y in (_FIELD_ORIGIN, _FIELD_MAX):
                perimeter.add((x, y))
    return perimeter


def _interior_coords() -> set[tuple[int, int]]:
    return {
        (x, y)
        for x in range(_FIELD_ORIGIN + 1, _FIELD_MAX)
        for y in range(_FIELD_ORIGIN + 1, _FIELD_MAX)
    }


def test_anchors_are_field_cells_facing_void() -> None:
    complete_map = golden_5x5_complete_map()
    anchors = scan_rim_anchors(complete_map)

    assert anchors, "expected at least one rim anchor"
    for anchor in anchors:
        assert isinstance(anchor, RimAnchor)
        assert anchor.coord in complete_map.field_cells
        assert anchor.void_dirs, f"anchor {anchor.coord} has no void-facing direction"


def test_anchor_coords_equal_block_perimeter() -> None:
    anchors = scan_rim_anchors(golden_5x5_complete_map())
    anchor_coords = {anchor.coord for anchor in anchors}
    assert anchor_coords == _expected_perimeter_coords()


def test_interior_cells_are_not_anchors() -> None:
    anchors = scan_rim_anchors(golden_5x5_complete_map())
    anchor_coords = {anchor.coord for anchor in anchors}
    for interior in _interior_coords():
        assert interior not in anchor_coords


def test_anchors_sorted_by_coord() -> None:
    anchors = scan_rim_anchors(golden_5x5_complete_map())
    coords = [anchor.coord for anchor in anchors]
    assert coords == sorted(coords, key=lambda c: (c[0], c[1]))


def test_void_dirs_sorted_by_cardinal_rank_and_correct() -> None:
    anchors = scan_rim_anchors(golden_5x5_complete_map())
    by_coord = {anchor.coord: anchor for anchor in anchors}

    nesw_rank = {
        CardinalEdge.NORTH.value: 0,
        CardinalEdge.EAST.value: 1,
        CardinalEdge.SOUTH.value: 2,
        CardinalEdge.WEST.value: 3,
    }
    for anchor in anchors:
        ranks = [nesw_rank[d] for d in anchor.void_dirs]
        assert ranks == sorted(ranks), f"{anchor.coord} void_dirs not in NESW rank order"

    # North-west corner (2, 2): faces void to the north (2, 1) and west (1, 2) only.
    nw_corner = by_coord[(_FIELD_ORIGIN, _FIELD_ORIGIN)]
    assert nw_corner.void_dirs == (CardinalEdge.NORTH.value, CardinalEdge.WEST.value)

    # West-edge mid cell (2, 4): faces void only to the west (1, 4).
    west_mid = by_coord[(_FIELD_ORIGIN, 4)]
    assert west_mid.void_dirs == (CardinalEdge.WEST.value,)


def test_field_kind_is_shape_for_shape_only_fixture() -> None:
    complete_map = golden_5x5_complete_map()
    assert complete_map.fluid_field_cell_count == 0
    anchors = scan_rim_anchors(complete_map)
    assert all(anchor.field_kind == "shape" for anchor in anchors)
