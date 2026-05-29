"""L4 selection sort helpers (mining-first greedy; not solver routing input)."""

from __future__ import annotations

import math

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.layers.contracts.candidates import (
    BundleCandidate,
    RouteProbedBundleCandidate,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.transport_entry import (
    derive_transport_entry_coord,
)

_OUTPUT_DIR_ORDER: dict[Direction, int] = {
    Direction.N: 0,
    Direction.E: 1,
    Direction.S: 2,
    Direction.W: 3,
}

_SORT_KEY_NAMES: tuple[str, ...] = (
    "effective_mining_gain",
    "route_cost",
    "intrinsic_priority_rank",
    "anchor_y",
    "anchor_x",
    "connector_goal_distance",
    "output_dir",
    "candidate_id",
)


def effective_mining_gain(candidate: BundleCandidate) -> int:
    """Mineable field cells covered by mining footprint (v1: cell count)."""

    return len(candidate.mining_occupied_cells)


def connector_goal_distance(entry: RouteProbedBundleCandidate) -> float:
    result = entry.route_probe_result
    if result is None or result.goal_coord is None:
        return math.inf
    candidate = entry.candidate
    start = candidate.route_probe_start_coord
    if start not in candidate.transport_stub_cells and start not in candidate.mining_occupied_cells:
        start = derive_transport_entry_coord(
            anchor_coord=candidate.anchor_coord,
            output_dir=candidate.output_dir,
        )
    gx, gy = result.goal_coord
    return float(abs(start[0] - gx) + abs(start[1] - gy))


def route_cost_for_sort(entry: RouteProbedBundleCandidate) -> float:
    result = entry.route_probe_result
    if result is None:
        return math.inf
    return float(result.route_cost)


def candidate_sort_key(entry: RouteProbedBundleCandidate) -> tuple[float | int | str, ...]:
    """Ascending tuple: lower sorts earlier and wins overlap conflicts."""

    candidate = entry.candidate
    return (
        -effective_mining_gain(candidate),
        route_cost_for_sort(entry),
        candidate.intrinsic_priority_rank,
        candidate.anchor_coord[1],
        candidate.anchor_coord[0],
        connector_goal_distance(entry),
        _OUTPUT_DIR_ORDER[candidate.output_dir],
        candidate.candidate_id,
    )


def overlap_tiebreak_step(
    winner: RouteProbedBundleCandidate,
    loser: RouteProbedBundleCandidate,
) -> str | None:
    """First sort dimension that differs when mining gains are equal."""

    wk = candidate_sort_key(winner)
    lk = candidate_sort_key(loser)
    for name, wv, lv in zip(_SORT_KEY_NAMES, wk, lk, strict=True):
        if wv != lv:
            return name
    return None


__all__ = [
    "candidate_sort_key",
    "connector_goal_distance",
    "effective_mining_gain",
    "overlap_tiebreak_step",
    "route_cost_for_sort",
]
