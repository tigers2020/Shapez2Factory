"""Genome fitness from candidate-phase fields only (PR-GA-1)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.candidates.placement_cells import (
    fixed_output_transport_cell,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.selection.greedy_regret import (
    SelectionConfig,
    _base_score,
    _fot_conflict,
    _overlaps,
)
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton

_NEGATIVE_INF = float("-inf")


def genome_layout_valid(
    commit_order: Sequence[str],
    candidates_by_id: Mapping[str, BundleCandidate],
    *,
    goal_count: int,
) -> bool:
    if len(commit_order) > max(0, goal_count):
        return False
    seen: set[str] = set()
    committed_occupied: set[Coord] = set()
    committed_fot: set[Coord] = set()
    for candidate_id in commit_order:
        if candidate_id in seen:
            return False
        candidate = candidates_by_id.get(candidate_id)
        if candidate is None:
            return False
        seen.add(candidate_id)
        occ = frozenset(committed_occupied)
        fot = frozenset(committed_fot)
        if _overlaps(candidate, occ) or _fot_conflict(
            candidate,
            committed_occupied=occ,
            committed_fixed_output_transport_cells=fot,
        ):
            return False
        committed_occupied.update(candidate.occupied_cells)
        committed_fot.add(fixed_output_transport_cell(candidate))
    return True


def evaluate_genome_fitness(
    commit_order: Sequence[str],
    *,
    candidates_by_id: Mapping[str, BundleCandidate],
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    config: SelectionConfig | None = None,
    goal_count: int | None = None,
) -> float:
    resolved_goal = goal_count if goal_count is not None else skeleton.capacity_goals
    if not genome_layout_valid(
        commit_order,
        candidates_by_id,
        goal_count=resolved_goal,
    ):
        return _NEGATIVE_INF

    resolved = config if config is not None else SelectionConfig()
    committed_occupied: set[Coord] = set()
    total = 0.0
    for candidate_id in commit_order:
        candidate = candidates_by_id[candidate_id]
        total += _base_score(
            candidate,
            skeleton,
            inp,
            config=resolved,
            committed_occupied=frozenset(committed_occupied),
        )
        committed_occupied.update(candidate.occupied_cells)
    return total


__all__ = ["evaluate_genome_fitness", "genome_layout_valid"]
