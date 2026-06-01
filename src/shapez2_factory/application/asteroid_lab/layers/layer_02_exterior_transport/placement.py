"""EDGE_WEIGHTED_EVEN_SPACING_V1 ??connector count and slot selection."""

from __future__ import annotations

import math

from shapez2_factory.application.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord

_EDGES_ORDER: tuple[CardinalEdge, ...] = (
    CardinalEdge.NORTH,
    CardinalEdge.EAST,
    CardinalEdge.SOUTH,
    CardinalEdge.WEST,
)


class InsufficientConnectorSlotsError(ValueError):
    """Raised when even slot selection needs more slots than available."""


class NoConnectorSlotsError(ValueError):
    """Raised when no candidate slots exist for distribution."""


def even_slot_index(*, i: int, count: int, slot_count: int) -> int:
    if count <= 0 or slot_count <= 0:
        return 0
    numer = (i + 1) * (slot_count + 1)
    denom = count + 1
    idx = (numer + denom // 2) // denom - 1
    return max(0, min(slot_count - 1, idx))


def nearest_unused_index(idx: int, length: int, used: set[int]) -> int:
    for offset in range(1, length):
        for candidate in (idx - offset, idx + offset):
            if 0 <= candidate < length and candidate not in used:
                return candidate
    return idx


def distribute_connector_counts(
    total: int,
    edge_slots: dict[CardinalEdge, list[Coord]],
) -> dict[CardinalEdge, int]:
    lengths = {edge: len(edge_slots[edge]) for edge in _EDGES_ORDER}
    perimeter = sum(lengths.values())

    if total <= 0:
        return {edge: 0 for edge in _EDGES_ORDER}

    if perimeter <= 0:
        msg = "no connector slots available"
        raise NoConnectorSlotsError(msg)

    raw = {edge: total * lengths[edge] / perimeter for edge in _EDGES_ORDER}
    counts = {edge: int(math.floor(raw[edge])) for edge in _EDGES_ORDER}

    remaining = total - sum(counts.values())
    order = sorted(
        _EDGES_ORDER,
        key=lambda edge: (
            -(raw[edge] - counts[edge]),
            -lengths[edge],
            _EDGES_ORDER.index(edge),
        ),
    )
    for edge in order[:remaining]:
        counts[edge] += 1

    return counts


def choose_even_slots(slots: list[Coord], count: int) -> list[Coord]:
    if count <= 0:
        return []

    if count > len(slots):
        msg = f"need {count} slots but only {len(slots)} available"
        raise InsufficientConnectorSlotsError(msg)

    selected: list[Coord] = []
    used_indices: set[int] = set()
    slot_count = len(slots)

    for i in range(count):
        idx = even_slot_index(i=i, count=count, slot_count=slot_count)
        if idx in used_indices:
            idx = nearest_unused_index(idx, slot_count, used_indices)
        used_indices.add(idx)
        selected.append(slots[idx])

    return selected


def remaining_slots_after_selection(
    edge_slots: dict[CardinalEdge, list[Coord]],
    used: set[Coord],
) -> dict[CardinalEdge, list[Coord]]:
    return {
        edge: [coord for coord in slots if coord not in used] for edge, slots in edge_slots.items()
    }


__all__ = [
    "InsufficientConnectorSlotsError",
    "NoConnectorSlotsError",
    "choose_even_slots",
    "distribute_connector_counts",
    "even_slot_index",
    "nearest_unused_index",
    "remaining_slots_after_selection",
]
