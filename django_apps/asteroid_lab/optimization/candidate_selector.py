"""Phase I — capacity-aware greedy candidate selection (PR4)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.bundle_selection_targets import (
    BundleSelectionTargets,
)
from django_apps.asteroid_lab.optimization.candidate_dtos import GeneCandidate
from django_apps.asteroid_lab.optimization.candidate_score import (
    GoalLoadKey,
    goal_load_key_for_candidate,
    score_gene_candidate,
    would_exceed_trunk_capacity,
)
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput


@dataclass(frozen=True, slots=True)
class SelectedCandidatePlan:
    """Commit attempt order (ids only); does not commit placements."""

    ordered_candidate_ids: tuple[str, ...]


def _selection_sort_key(
    candidate: GeneCandidate,
    *,
    inp: OptimizationInput,
    goal_load: dict[GoalLoadKey, int],
) -> tuple[float, int, str]:
    breakdown = score_gene_candidate(
        candidate,
        inp=inp,
        goal_assigned_platforms=goal_load,
    )
    return (
        breakdown.total,
        -candidate.route_probe_result.cost,
        candidate.candidate_id,
    )


def select_gene_candidates_greedy(
    candidates: tuple[GeneCandidate, ...],
    *,
    inp: OptimizationInput,
    targets: BundleSelectionTargets | None = None,
) -> SelectedCandidatePlan:
    """Order normal candidates for incremental commit (PR5); does not mutate ``inp``."""

    remaining = list(candidates)
    goal_load: dict[GoalLoadKey, int] = {}
    ordered_ids: list[str] = []

    while remaining:
        eligible = [
            c
            for c in remaining
            if not would_exceed_trunk_capacity(c, goal_assigned_platforms=goal_load)
        ]
        pool = eligible if eligible else remaining
        best = max(
            pool,
            key=lambda c: _selection_sort_key(c, inp=inp, goal_load=goal_load),
        )
        ordered_ids.append(best.candidate_id)
        key = goal_load_key_for_candidate(best)
        goal_load[key] = goal_load.get(key, 0) + 1
        remaining.remove(best)

    if targets is not None and len(ordered_ids) > targets.target_miner_bundle_count:
        ordered_ids = ordered_ids[: targets.target_miner_bundle_count]

    return SelectedCandidatePlan(ordered_candidate_ids=tuple(ordered_ids))
