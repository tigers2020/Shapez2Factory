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


def _min_index_distance(idx: int, avoid_indices: set[int]) -> int:
    if not avoid_indices:
        return 0
    return min(abs(idx - avoid_index) for avoid_index in avoid_indices)


def _is_between_required(index: int, avoid_indices: set[int]) -> bool:
    return (index - 1) in avoid_indices and (index + 1) in avoid_indices


def _spare_candidate_rank(
    index: int,
    *,
    avoid_indices: set[int],
    picked_indices: set[int],
) -> tuple[int, int, int, int]:
    required_distance = _min_index_distance(index, avoid_indices)
    spare_distance = _min_index_distance(index, picked_indices)
    return (
        int(_is_between_required(index, avoid_indices)),
        -required_distance,
        -spare_distance,
        index,
    )


def choose_spare_slots(
    slots: list[Coord],
    count: int,
    *,
    avoid: set[Coord],
) -> list[Coord]:
    """Pick spare connectors as far from required slots as the edge allows."""

    if count <= 0:
        return []

    avoid_indices = {index for index, coord in enumerate(slots) if coord in avoid}
    available_count = len(slots) - len(avoid_indices)
    if count > available_count:
        msg = f"need {count} spare slots but only {available_count} available"
        raise InsufficientConnectorSlotsError(msg)

    if not avoid_indices:
        return choose_even_slots(slots, count)

    candidates: list[tuple[int, int]] = []
    for index in range(len(slots)):
        if index in avoid_indices:
            continue
        candidates.append((_min_index_distance(index, avoid_indices), index))

    by_distance: dict[int, list[int]] = {}
    for distance, index in candidates:
        by_distance.setdefault(distance, []).append(index)

    picked_indices: list[int] = []
    picked_index_set: set[int] = set()
    for distance in sorted(by_distance.keys(), reverse=True):
        need = count - len(picked_indices)
        if need <= 0:
            break
        pool = sorted(by_distance[distance])
        if len(pool) <= need:
            picked_indices.extend(pool)
            picked_index_set.update(pool)
            continue
        ranked_pool = sorted(
            pool,
            key=lambda index: _spare_candidate_rank(
                index,
                avoid_indices=avoid_indices,
                picked_indices=picked_index_set,
            ),
        )
        if need == 1:
            picked_indices.append(ranked_pool[0])
            picked_index_set.add(ranked_pool[0])
            continue
        pool_coords = [slots[index] for index in ranked_pool]
        chosen_coords = choose_even_slots(pool_coords, need)
        chosen_indices = [slots.index(coord) for coord in chosen_coords]
        picked_indices.extend(chosen_indices)
        picked_index_set.update(chosen_indices)
        break

    if len(picked_indices) < count:
        msg = f"need {count} spare slots but only {len(picked_indices)} could be placed"
        raise InsufficientConnectorSlotsError(msg)

    return [slots[index] for index in sorted(picked_indices)]


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
    "choose_spare_slots",
    "distribute_connector_counts",
    "even_slot_index",
    "nearest_unused_index",
    "remaining_slots_after_selection",
]
