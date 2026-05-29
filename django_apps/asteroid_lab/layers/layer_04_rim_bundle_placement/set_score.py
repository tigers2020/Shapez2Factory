"""Lexicographic set_score for L4 v2 component packing."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.candidates import RouteProbedBundleCandidate
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.sort_keys import (
    connector_goal_distance,
    effective_mining_gain,
    route_cost_for_sort,
)

SetScoreTuple = tuple[int, int, float, float, tuple[str, ...]]


def set_score_tuple(
    *,
    entries: tuple[RouteProbedBundleCandidate, ...],
) -> SetScoreTuple:
    """Higher tuple is better under lexicographic compare_set_scores."""

    total_gain = sum(effective_mining_gain(e.candidate) for e in entries)
    count = len(entries)
    total_route = sum(route_cost_for_sort(e) for e in entries)
    total_conn = sum(connector_goal_distance(e) for e in entries)
    ids = tuple(sorted(e.candidate.candidate_id for e in entries))
    return (total_gain, count, -total_route, -total_conn, ids)


def compare_set_scores(left: SetScoreTuple, right: SetScoreTuple) -> int:
    """Return >0 if left is strictly better than right."""

    if left > right:
        return 1
    if left < right:
        return -1
    return 0


__all__ = ["SetScoreTuple", "compare_set_scores", "set_score_tuple"]
