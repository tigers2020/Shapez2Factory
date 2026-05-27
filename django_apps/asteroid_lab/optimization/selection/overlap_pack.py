"""Overlap-graph packing genome selection (P1-ELCP-RF-B1)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.candidates.placement_cells import (
    fixed_output_transport_cell,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.selection.equivalence import dedupe_candidates
from django_apps.asteroid_lab.optimization.selection.greedy_regret import (
    PlacementGenome,
    SelectionConfig,
    _base_score,
    _fot_conflict,
    _overlaps,
    _priority,
    _regret_scores,
)
from django_apps.asteroid_lab.optimization.selection.overlap_graph import (
    compute_best_known_independent_set_candidate_ids,
)
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton


def _overlap_pack_sort_key(
    candidate: BundleCandidate,
    *,
    base_score: float,
    regret: float,
    skeleton: RttpSkeleton,
    config: SelectionConfig,
) -> tuple[float, float, str]:
    priority = _priority(
        candidate,
        base_score=base_score,
        regret=regret,
        skeleton=skeleton,
        committed_route_cells=frozenset(),
        config=config,
    )
    return (
        -priority,
        float(candidate.route_probe_cost),
        candidate.candidate_id,
    )


def _order_candidate_ids(
    candidate_ids: tuple[str, ...],
    pool: tuple[BundleCandidate, ...],
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    config: SelectionConfig,
) -> tuple[str, ...]:
    by_id = {candidate.candidate_id: candidate for candidate in pool}
    subset = tuple(by_id[candidate_id] for candidate_id in candidate_ids if candidate_id in by_id)
    base_scores = {
        candidate.candidate_id: _base_score(
            candidate,
            skeleton,
            inp,
            config=config,
            committed_occupied=frozenset(),
        )
        for candidate in subset
    }
    regrets = _regret_scores(subset, base_scores)
    return tuple(
        sorted(
            (candidate.candidate_id for candidate in subset),
            key=lambda candidate_id: _overlap_pack_sort_key(
                by_id[candidate_id],
                base_score=base_scores[candidate_id],
                regret=regrets[candidate_id],
                skeleton=skeleton,
                config=config,
            ),
        )
    )


def select_genome_overlap_pack(
    normal_candidates: tuple[BundleCandidate, ...],
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    *,
    config: SelectionConfig | None = None,
    goal_count: int | None = None,
) -> PlacementGenome:
    resolved = config if config is not None else SelectionConfig()
    pool = list(dedupe_candidates(normal_candidates))
    resolved_goal = (
        max(0, goal_count) if goal_count is not None else max(0, skeleton.capacity_goals)
    )
    if not pool or resolved_goal == 0:
        return PlacementGenome(commit_order=())

    by_id = {candidate.candidate_id: candidate for candidate in pool}
    independent_ids = compute_best_known_independent_set_candidate_ids(pool)
    ordered_independent = _order_candidate_ids(
        independent_ids,
        tuple(pool),
        skeleton,
        inp,
        resolved,
    )

    commit_order: list[str] = []
    committed_occupied: set[Coord] = set()
    committed_fot: set[Coord] = set()

    def try_append(candidate_id: str) -> bool:
        candidate = by_id[candidate_id]
        occupied = frozenset(committed_occupied)
        fot_cells = frozenset(committed_fot)
        if _overlaps(candidate, occupied) or _fot_conflict(
            candidate,
            committed_occupied=occupied,
            committed_fixed_output_transport_cells=fot_cells,
        ):
            return False
        commit_order.append(candidate_id)
        committed_occupied.update(candidate.occupied_cells)
        committed_fot.add(fixed_output_transport_cell(candidate))
        return True

    for candidate_id in ordered_independent:
        if len(commit_order) >= resolved_goal:
            break
        try_append(candidate_id)

    remaining = [candidate for candidate in pool if candidate.candidate_id not in commit_order]
    while len(commit_order) < resolved_goal and remaining:
        base_scores = {
            candidate.candidate_id: _base_score(
                candidate,
                skeleton,
                inp,
                config=resolved,
                committed_occupied=frozenset(committed_occupied),
            )
            for candidate in remaining
        }
        regrets = _regret_scores(tuple(remaining), base_scores)
        pick = min(
            remaining,
            key=lambda candidate: _overlap_pack_sort_key(
                candidate,
                base_score=base_scores[candidate.candidate_id],
                regret=regrets[candidate.candidate_id],
                skeleton=skeleton,
                config=resolved,
            ),
        )
        if not try_append(pick.candidate_id):
            remaining = [
                candidate for candidate in remaining if candidate.candidate_id != pick.candidate_id
            ]
            continue
        remaining = [
            candidate
            for candidate in remaining
            if candidate.candidate_id != pick.candidate_id
            and not _overlaps(candidate, frozenset(committed_occupied))
            and not _fot_conflict(
                candidate,
                committed_occupied=frozenset(committed_occupied),
                committed_fixed_output_transport_cells=frozenset(committed_fot),
            )
        ]

    return PlacementGenome(commit_order=tuple(commit_order))


__all__ = ["select_genome_overlap_pack"]
