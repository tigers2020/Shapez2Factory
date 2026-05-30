"""Rim anchor boundary traversal (Task 4 golden)."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.rim_anchors import (
    DEGRADED_BOUNDARY_ORDER_SEGMENT,
    build_ordered_outer_rim_anchors,
)
from tests.unit.asteroid_lab.layers.fixtures.rim_anchor_walk_map import (
    rim_walk_full_5x5_complete_map,
    rim_walk_pocket_complete_map,
)

# CW boundary walk from top-left-ish start (max y, min x) on full 5×5 block.
GOLDEN_FULL_5X5_ORDER: tuple[tuple[int, int], ...] = (
    (2, 6),
    (3, 6),
    (4, 6),
    (5, 6),
    (6, 6),
    (6, 5),
    (6, 4),
    (6, 3),
    (6, 2),
    (5, 2),
    (4, 2),
    (3, 2),
    (2, 2),
    (2, 3),
    (2, 4),
    (2, 5),
)

GOLDEN_FULL_5X5_CORNER_VOID_DIRS: dict[tuple[int, int], tuple[str, ...]] = {
    (2, 6): ("N", "W"),
    (6, 6): ("N", "E"),
    (6, 2): ("E", "S"),  # N,E,S,W enum order
    (2, 2): ("S", "W"),
}


def test_full_5x5_boundary_walk_matches_golden_order() -> None:
    anchors = build_ordered_outer_rim_anchors(rim_walk_full_5x5_complete_map())
    assert [a.coord for a in anchors] == list(GOLDEN_FULL_5X5_ORDER)
    for index, anchor in enumerate(anchors):
        assert anchor.traversal_index == index
        assert anchor.rim_segment_id != DEGRADED_BOUNDARY_ORDER_SEGMENT


def test_corner_void_dirs_deterministic() -> None:
    anchors = build_ordered_outer_rim_anchors(rim_walk_full_5x5_complete_map())
    by_coord = {a.coord: a.void_dirs for a in anchors}
    for coord, expected_dirs in GOLDEN_FULL_5X5_CORNER_VOID_DIRS.items():
        assert by_coord[coord] == expected_dirs


def test_interior_void_neighbor_not_counted_as_void_normal() -> None:
    complete_map = rim_walk_pocket_complete_map()
    assert (4, 4) not in complete_map.field_cells
    assert (4, 4) not in complete_map.external_void_cells
    anchors = build_ordered_outer_rim_anchors(complete_map)
    by_coord = {a.coord: a for a in anchors}
    # Cells that only touch interior void are not outer-rim anchors.
    assert (3, 4) not in by_coord
    assert (4, 3) not in by_coord
    assert (4, 5) not in by_coord
    # Every anchor void_dir must point at external_void only.
    for anchor in anchors:
        x, y = anchor.coord
        for direction in anchor.void_dirs:
            dx, dy = {"N": (0, 1), "E": (1, 0), "S": (0, -1), "W": (-1, 0)}[direction]
            neighbor = (x + dx, y + dy)
            assert neighbor in complete_map.external_void_cells
            assert neighbor not in complete_map.field_cells


def test_no_yx_sort_canonical_order() -> None:
    """Boundary walk must differ from naive (y, x) sort on non-convex pocket map."""
    complete_map = rim_walk_pocket_complete_map()
    anchors = build_ordered_outer_rim_anchors(complete_map)
    coords = [a.coord for a in anchors]
    yx_sorted = sorted(coords, key=lambda c: (c[1], c[0]))
    assert coords != yx_sorted


def test_traversal_indices_are_contiguous() -> None:
    anchors = build_ordered_outer_rim_anchors(rim_walk_pocket_complete_map())
    assert [a.traversal_index for a in anchors] == list(range(len(anchors)))
