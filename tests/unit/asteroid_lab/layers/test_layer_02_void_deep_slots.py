"""VOID_DEEP_SLOTS_V1 slot catalog tests."""

from django_apps.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.slots import (
    VOID_DEPTH_MIN,
    build_candidate_slots_by_edge,
    compute_void_depth_entries,
)
from tests.unit.asteroid_lab.layers.helpers.l02_complete_map_fixtures import (
    build_rect_field_with_void_shell,
    make_complete_map,
)


def test_void_depth_excludes_rim_adjacent() -> None:
    cm = build_rect_field_with_void_shell(width=6, height=6, void_pad=10)
    entries = compute_void_depth_entries(cm)
    shallow = [c for c, e in entries.items() if 1 <= e.depth < VOID_DEPTH_MIN]
    assert shallow
    chosen = {c for slots in build_candidate_slots_by_edge(cm).values() for c in slots}
    assert not chosen.intersection(shallow)


def test_void_depth_includes_at_5() -> None:
    cm = build_rect_field_with_void_shell(width=6, height=6, void_pad=10)
    entries = compute_void_depth_entries(cm)
    at_five = [c for c, e in entries.items() if e.depth == VOID_DEPTH_MIN]
    assert at_five
    chosen = {c for slots in build_candidate_slots_by_edge(cm).values() for c in slots}
    assert at_five[0] in chosen


def test_shallow_void_side_zero_slots() -> None:
    field = frozenset({(0, 0), (1, 0), (0, 1), (1, 1)})
    void = frozenset({(0, -1), (1, -1)})
    cm = make_complete_map(field_cells=field, external_void_cells=void)
    assert build_candidate_slots_by_edge(cm)[CardinalEdge.NORTH] == []


def test_void_depth_bfs_only_through_external_void() -> None:
    field = frozenset({(0, 0)})
    void = frozenset({(0, 1), (0, 2)})
    cm = make_complete_map(field_cells=field, external_void_cells=void)
    entries = compute_void_depth_entries(cm)
    assert (0, 0) not in entries
    assert all(coord in void for coord in entries)


def test_candidate_slot_order_by_edge() -> None:
    cm = build_rect_field_with_void_shell(width=8, height=8, void_pad=12)
    slots = build_candidate_slots_by_edge(cm)
    north = slots[CardinalEdge.NORTH]
    if len(north) >= 2:
        assert north[0][0] <= north[1][0]


def test_void_deep_slot_edge_from_bfs_source() -> None:
    field = frozenset({(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (0, 2), (1, 2)})
    void: set[tuple[int, int]] = set()
    for x in range(-1, 10):
        for y in range(-1, 10):
            if (x, y) not in field:
                void.add((x, y))
    cm = make_complete_map(field_cells=frozenset(field), external_void_cells=frozenset(void))
    entries = compute_void_depth_entries(cm)
    deep_east = [
        c
        for c, e in entries.items()
        if e.depth >= VOID_DEPTH_MIN and e.source_edge == CardinalEdge.EAST
    ]
    assert deep_east
    slots = build_candidate_slots_by_edge(cm)
    for coord in slots[CardinalEdge.EAST]:
        assert entries[coord].source_edge == CardinalEdge.EAST
