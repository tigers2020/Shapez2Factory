"""Branch-and-bound maximum set_score independent set for small components."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.candidates import RouteProbedBundleCandidate
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.conflict_graph import (
    occupied_cells_for_entry,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.set_score import (
    SetScoreTuple,
    compare_set_scores,
    set_score_tuple,
)
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.sort_keys import (
    candidate_sort_key,
    effective_mining_gain,
)

MAX_EXACT_COMPONENT_SIZE = 20
MAX_BRANCH_NODES = 500_000


def select_max_set_score_independent_set(
    entries: tuple[RouteProbedBundleCandidate, ...],
) -> tuple[RouteProbedBundleCandidate, ...]:
    """Return a maximum ``set_score`` non-overlapping subset (deterministic)."""

    n = len(entries)
    if n == 0:
        return ()
    if n > MAX_EXACT_COMPONENT_SIZE:
        msg = f"component size {n} exceeds MAX_EXACT_COMPONENT_SIZE={MAX_EXACT_COMPONENT_SIZE}"
        raise ValueError(msg)

    ordered = tuple(sorted(entries, key=candidate_sort_key))
    occupied = [occupied_cells_for_entry(e) for e in ordered]
    neighbor_masks = [_neighbor_mask(i, occupied) for i in range(n)]

    best_entries: tuple[RouteProbedBundleCandidate, ...] = ()
    best_score: SetScoreTuple = (-1, -1, 0.0, 0.0, ())
    branch_nodes = 0

    def optimistic_gain_upper_bound(start_idx: int) -> int:
        return sum(effective_mining_gain(ordered[i].candidate) for i in range(start_idx, n))

    def optimistic_score_tuple(
        current: SetScoreTuple,
        start_idx: int,
    ) -> SetScoreTuple:
        add_gain = optimistic_gain_upper_bound(start_idx)
        return (current[0] + add_gain, current[1] + (n - start_idx), current[2], current[3], ())

    def dfs(
        idx: int,
        selected_mask: int,
        picked: list[RouteProbedBundleCandidate],
    ) -> None:
        nonlocal best_entries, best_score, branch_nodes
        branch_nodes += 1
        if branch_nodes > MAX_BRANCH_NODES:
            msg = "exact_pack branch limit exceeded"
            raise RuntimeError(msg)

        if idx == n:
            current_score = set_score_tuple(entries=tuple(picked))
            if compare_set_scores(current_score, best_score) > 0:
                best_score = current_score
                best_entries = tuple(picked)
            return

        current_score = set_score_tuple(entries=tuple(picked))
        if compare_set_scores(optimistic_score_tuple(current_score, idx), best_score) <= 0:
            return

        dfs(idx + 1, selected_mask, picked)

        if not (selected_mask & neighbor_masks[idx]):
            picked.append(ordered[idx])
            dfs(idx + 1, selected_mask | (1 << idx), picked)
            picked.pop()

    dfs(0, 0, [])
    return best_entries


def _neighbor_mask(index: int, occupied: list[frozenset]) -> int:
    mask = 0
    for j in range(index):
        if occupied[index] & occupied[j]:
            mask |= 1 << j
    for j in range(index + 1, len(occupied)):
        if occupied[index] & occupied[j]:
            mask |= 1 << j
    return mask


__all__ = [
    "MAX_BRANCH_NODES",
    "MAX_EXACT_COMPONENT_SIZE",
    "select_max_set_score_independent_set",
]
