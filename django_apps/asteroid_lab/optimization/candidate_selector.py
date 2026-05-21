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
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput

DEFAULT_MAX_SELECTED_VARIANTS_PER_EXTRACTOR = 1


@dataclass(frozen=True, slots=True)
class SelectedCandidatePlan:
    """Commit attempt order (ids only); does not commit placements."""

    ordered_candidate_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SelectionDiagnostics:
    """Selection-phase counters for anchor diversity (summary / replay only)."""

    selection_skipped_duplicate_anchor_count: int
    max_selected_variants_per_extractor: int
    selection_stopped_by_throughput_budget: bool = False
    selected_throughput_at_stop: int = 0


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


def _anchor_slots_available(
    candidate: GeneCandidate,
    *,
    anchor_use_count: dict[Coord, int],
    max_selected_variants_per_extractor: int,
) -> bool:
    return anchor_use_count.get(candidate.extractor, 0) < max_selected_variants_per_extractor


def select_gene_candidates_greedy(
    candidates: tuple[GeneCandidate, ...],
    *,
    inp: OptimizationInput,
    targets: BundleSelectionTargets | None = None,
    max_selected_variants_per_extractor: int = DEFAULT_MAX_SELECTED_VARIANTS_PER_EXTRACTOR,
) -> tuple[SelectedCandidatePlan, SelectionDiagnostics]:
    """Order normal candidates for incremental commit (PR5); does not mutate ``inp``."""

    if max_selected_variants_per_extractor < 1:
        msg = "max_selected_variants_per_extractor must be >= 1"
        raise ValueError(msg)

    remaining = list(candidates)
    goal_load: dict[GoalLoadKey, int] = {}
    anchor_use_count: dict[Coord, int] = {}
    ordered_ids: list[str] = []
    selection_skipped_duplicate_anchor = 0
    cumulative_throughput = 0
    selection_stopped_by_throughput_budget = False

    while remaining:
        eligible = [
            c
            for c in remaining
            if not would_exceed_trunk_capacity(c, goal_assigned_platforms=goal_load)
            and _anchor_slots_available(
                c,
                anchor_use_count=anchor_use_count,
                max_selected_variants_per_extractor=max_selected_variants_per_extractor,
            )
        ]
        if eligible:
            pool = eligible
        else:
            trunk_ok_anchor_full = [
                c
                for c in remaining
                if not would_exceed_trunk_capacity(c, goal_assigned_platforms=goal_load)
                and not _anchor_slots_available(
                    c,
                    anchor_use_count=anchor_use_count,
                    max_selected_variants_per_extractor=max_selected_variants_per_extractor,
                )
            ]
            if trunk_ok_anchor_full:
                selection_skipped_duplicate_anchor += len(trunk_ok_anchor_full)
                break
            pool = remaining

        best = max(
            pool,
            key=lambda c: _selection_sort_key(c, inp=inp, goal_load=goal_load),
        )
        ordered_ids.append(best.candidate_id)
        cumulative_throughput += best.base_throughput
        key = goal_load_key_for_candidate(best)
        goal_load[key] = goal_load.get(key, 0) + 1
        anchor_use_count[best.extractor] = anchor_use_count.get(best.extractor, 0) + 1
        remaining.remove(best)

        if targets is not None and cumulative_throughput >= targets.target_miner_bundle_count:
            selection_stopped_by_throughput_budget = True
            break

    if (
        targets is not None
        and not selection_stopped_by_throughput_budget
        and len(ordered_ids) > targets.target_miner_bundle_count
    ):
        ordered_ids = ordered_ids[: targets.target_miner_bundle_count]
        by_id = {c.candidate_id: c for c in candidates}
        cumulative_throughput = sum(
            by_id[cid].base_throughput for cid in ordered_ids if cid in by_id
        )

    plan = SelectedCandidatePlan(ordered_candidate_ids=tuple(ordered_ids))
    diagnostics = SelectionDiagnostics(
        selection_skipped_duplicate_anchor_count=selection_skipped_duplicate_anchor,
        max_selected_variants_per_extractor=max_selected_variants_per_extractor,
        selection_stopped_by_throughput_budget=selection_stopped_by_throughput_budget,
        selected_throughput_at_stop=cumulative_throughput,
    )
    return plan, diagnostics
