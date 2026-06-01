"""EDGE_WEIGHTED_EVEN_SPACING_V1 placement tests."""

import pytest

from shapez2_factory.application.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.placement import (
    InsufficientConnectorSlotsError,
    choose_even_slots,
    distribute_connector_counts,
    even_slot_index,
    nearest_unused_index,
    remaining_slots_after_selection,
)


def test_even_slot_index_half_up_not_bankers() -> None:
    assert even_slot_index(i=0, count=3, slot_count=10) == 2


def test_nearest_unused_prefers_lower_index_on_tie() -> None:
    used = {2}
    assert nearest_unused_index(2, 5, used) == 1


def test_edge_weighted_count_distribution_sums_to_n() -> None:
    edge_slots = {
        CardinalEdge.NORTH: [(0, -5)] * 10,
        CardinalEdge.EAST: [(5, 0)] * 10,
        CardinalEdge.SOUTH: [(0, 9)] * 10,
        CardinalEdge.WEST: [(-5, 0)] * 10,
    }
    counts = distribute_connector_counts(9, edge_slots)
    assert sum(counts.values()) == 9


def test_edge_weighted_distribution_ignores_zero_slot_edge() -> None:
    edge_slots = {
        CardinalEdge.NORTH: [],
        CardinalEdge.EAST: [(5, 0)] * 12,
        CardinalEdge.SOUTH: [(0, 9)] * 12,
        CardinalEdge.WEST: [(-5, 0)] * 12,
    }
    counts = distribute_connector_counts(6, edge_slots)
    assert counts[CardinalEdge.NORTH] == 0
    assert sum(counts.values()) == 6


def test_choose_even_slots_interior() -> None:
    slots = [(i, 0) for i in range(10)]
    picked = choose_even_slots(slots, 3)
    indices = [slots.index(c) for c in picked]
    assert 0 not in indices and 9 not in indices


def test_choose_even_slots_raises_when_count_exceeds_slots() -> None:
    with pytest.raises(InsufficientConnectorSlotsError):
        choose_even_slots([(0, 0), (1, 0)], 3)


def test_remaining_slots_excludes_used_coords() -> None:
    edge_slots = {
        CardinalEdge.NORTH: [(0, -5), (1, -5), (2, -5)],
        CardinalEdge.EAST: [(5, 0)],
        CardinalEdge.SOUTH: [],
        CardinalEdge.WEST: [],
    }
    used = {(1, -5)}
    remaining = remaining_slots_after_selection(edge_slots, used)
    assert (1, -5) not in remaining[CardinalEdge.NORTH]
    assert len(remaining[CardinalEdge.NORTH]) == 2
    assert remaining[CardinalEdge.EAST] == [(5, 0)]
