"""Read-only greedy-regret selection trace (P1-ELCP-RF-A2; not solver input).

INVESTIGATION_COUPLING: mirror loop calls production private helpers from
``greedy_regret``. Drift is guarded by ``assert_selection_trace_parity`` tests
against production ``select_genome``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

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
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton


class SelectionStopReason(StrEnum):
    GOAL_REACHED = "goal_reached"
    POOL_EXHAUSTED = "pool_exhausted"


class AttritionClass(StrEnum):
    SELECTED = "selected"
    DEDUPE_REMOVED = "dedupe_removed"
    REMOVED_BY_OVERLAP = "removed_by_overlap"
    REMOVED_BY_FOT = "removed_by_fot"
    UNPICKED_SCORE = "unpicked_score"
    UNKNOWN_ATTRITION = "unknown_attrition"


@dataclass(frozen=True, slots=True)
class GreedyRegretRoundTraceRow:
    round_index: int
    pool_size_before: int
    resolved_goal: int
    selected_candidate_id: str
    selected_occupied_cells_count: int
    selected_output_stub: Coord
    selected_fot_cell: Coord
    removed_by_overlap_count: int
    removed_by_fot_conflict_count: int
    removed_by_other_count: int
    pool_size_after: int
    commit_order_len_so_far: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "round_index": self.round_index,
            "pool_size_before": self.pool_size_before,
            "resolved_goal": self.resolved_goal,
            "selected_candidate_id": self.selected_candidate_id,
            "selected_occupied_cells_count": self.selected_occupied_cells_count,
            "selected_output_stub": list(self.selected_output_stub),
            "selected_fot_cell": list(self.selected_fot_cell),
            "removed_by_overlap_count": self.removed_by_overlap_count,
            "removed_by_fot_conflict_count": self.removed_by_fot_conflict_count,
            "removed_by_other_count": self.removed_by_other_count,
            "pool_size_after": self.pool_size_after,
            "commit_order_len_so_far": self.commit_order_len_so_far,
        }


@dataclass(frozen=True, slots=True)
class NormalCandidateAttritionRow:
    candidate_id: str
    attrition_class: AttritionClass
    round_index: int | None
    anchor_coord: Coord

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "attrition_class": self.attrition_class.value,
            "round_index": self.round_index,
            "anchor_coord": list(self.anchor_coord),
        }


@dataclass(frozen=True, slots=True)
class GreedyRegretSelectionTraceResult:
    commit_order: tuple[str, ...]
    stop_reason: SelectionStopReason
    resolved_goal: int
    pool_size_after_dedupe: int
    normal_candidate_count: int
    dedupe_removed_count: int
    round_trace: tuple[GreedyRegretRoundTraceRow, ...]
    attrition_ledger: tuple[NormalCandidateAttritionRow, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "commit_order": list(self.commit_order),
            "stop_reason": self.stop_reason.value,
            "resolved_goal": self.resolved_goal,
            "pool_size_after_dedupe": self.pool_size_after_dedupe,
            "normal_candidate_count": self.normal_candidate_count,
            "dedupe_removed_count": self.dedupe_removed_count,
            "round_trace": [row.to_dict() for row in self.round_trace],
            "attrition_ledger": [row.to_dict() for row in self.attrition_ledger],
        }


def trace_greedy_regret_selection(
    normal_candidates: tuple[BundleCandidate, ...],
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    *,
    config: SelectionConfig | None = None,
    goal_count: int | None = None,
) -> GreedyRegretSelectionTraceResult:
    """Mirror ``select_genome`` while emitting per-round trace and attrition ledger."""

    resolved = config if config is not None else SelectionConfig()
    anchor_by_id: dict[str, Coord] = {
        candidate.candidate_id: candidate.anchor_coord for candidate in normal_candidates
    }
    normal_ids = frozenset(anchor_by_id)

    deduped = dedupe_candidates(normal_candidates)
    deduped_ids = frozenset(candidate.candidate_id for candidate in deduped)
    dedupe_removed_ids = normal_ids - deduped_ids

    attrition_by_id: dict[str, NormalCandidateAttritionRow] = {}
    for candidate_id in dedupe_removed_ids:
        attrition_by_id[candidate_id] = NormalCandidateAttritionRow(
            candidate_id=candidate_id,
            attrition_class=AttritionClass.DEDUPE_REMOVED,
            round_index=None,
            anchor_coord=anchor_by_id[candidate_id],
        )

    pool = list(deduped)
    commit_order: list[str] = []
    committed_occupied: set[Coord] = set()
    committed_fixed_output_transport_cells: set[Coord] = set()
    committed_route_cells: set[Coord] = set()
    resolved_goal = (
        max(0, goal_count) if goal_count is not None else max(0, skeleton.capacity_goals)
    )
    round_trace: list[GreedyRegretRoundTraceRow] = []
    round_index = 0

    while pool and len(commit_order) < resolved_goal:
        pool_size_before = len(pool)
        base_scores = {
            candidate.candidate_id: _base_score(
                candidate,
                skeleton,
                inp,
                config=resolved,
                committed_occupied=frozenset(committed_occupied),
            )
            for candidate in pool
        }
        regrets = _regret_scores(tuple(pool), base_scores)

        best = max(
            pool,
            key=lambda candidate: (
                _priority(
                    candidate,
                    base_score=base_scores[candidate.candidate_id],
                    regret=regrets[candidate.candidate_id],
                    skeleton=skeleton,
                    committed_route_cells=frozenset(committed_route_cells),
                    config=resolved,
                ),
                -pool.index(candidate),
            ),
        )
        commit_order.append(best.candidate_id)
        committed_occupied.update(best.occupied_cells)
        committed_fixed_output_transport_cells.add(fixed_output_transport_cell(best))
        committed_route_cells.add(best.output_stub)
        committed_fot = frozenset(committed_fixed_output_transport_cells)
        committed_occ = frozenset(committed_occupied)

        removed_by_overlap_count = 0
        removed_by_fot_conflict_count = 0
        removed_by_other_count = 0
        next_pool: list[BundleCandidate] = []

        for candidate in pool:
            if candidate.candidate_id == best.candidate_id:
                continue
            if _overlaps(candidate, committed_occ):
                removed_by_overlap_count += 1
                attrition_by_id[candidate.candidate_id] = NormalCandidateAttritionRow(
                    candidate_id=candidate.candidate_id,
                    attrition_class=AttritionClass.REMOVED_BY_OVERLAP,
                    round_index=round_index,
                    anchor_coord=candidate.anchor_coord,
                )
                continue
            if _fot_conflict(
                candidate,
                committed_occupied=committed_occ,
                committed_fixed_output_transport_cells=committed_fot,
            ):
                removed_by_fot_conflict_count += 1
                attrition_by_id[candidate.candidate_id] = NormalCandidateAttritionRow(
                    candidate_id=candidate.candidate_id,
                    attrition_class=AttritionClass.REMOVED_BY_FOT,
                    round_index=round_index,
                    anchor_coord=candidate.anchor_coord,
                )
                continue
            next_pool.append(candidate)

        pool = next_pool
        attrition_by_id[best.candidate_id] = NormalCandidateAttritionRow(
            candidate_id=best.candidate_id,
            attrition_class=AttritionClass.SELECTED,
            round_index=round_index,
            anchor_coord=best.anchor_coord,
        )
        round_trace.append(
            GreedyRegretRoundTraceRow(
                round_index=round_index,
                pool_size_before=pool_size_before,
                resolved_goal=resolved_goal,
                selected_candidate_id=best.candidate_id,
                selected_occupied_cells_count=len(best.occupied_cells),
                selected_output_stub=best.output_stub,
                selected_fot_cell=fixed_output_transport_cell(best),
                removed_by_overlap_count=removed_by_overlap_count,
                removed_by_fot_conflict_count=removed_by_fot_conflict_count,
                removed_by_other_count=removed_by_other_count,
                pool_size_after=len(pool),
                commit_order_len_so_far=len(commit_order),
            )
        )
        round_index += 1

    stop_reason = (
        SelectionStopReason.GOAL_REACHED
        if len(commit_order) >= resolved_goal
        else SelectionStopReason.POOL_EXHAUSTED
    )

    if stop_reason is SelectionStopReason.GOAL_REACHED:
        for candidate in pool:
            attrition_by_id[candidate.candidate_id] = NormalCandidateAttritionRow(
                candidate_id=candidate.candidate_id,
                attrition_class=AttritionClass.UNPICKED_SCORE,
                round_index=None,
                anchor_coord=candidate.anchor_coord,
            )
    elif pool:
        msg = f"pool_exhausted stop requires empty pool, got {len(pool)}"
        raise AssertionError(msg)

    for candidate_id in normal_ids - frozenset(attrition_by_id):
        attrition_by_id[candidate_id] = NormalCandidateAttritionRow(
            candidate_id=candidate_id,
            attrition_class=AttritionClass.UNKNOWN_ATTRITION,
            round_index=None,
            anchor_coord=anchor_by_id[candidate_id],
        )

    attrition_ledger = tuple(
        attrition_by_id[candidate_id] for candidate_id in sorted(attrition_by_id)
    )

    return GreedyRegretSelectionTraceResult(
        commit_order=tuple(commit_order),
        stop_reason=stop_reason,
        resolved_goal=resolved_goal,
        pool_size_after_dedupe=len(deduped),
        normal_candidate_count=len(normal_candidates),
        dedupe_removed_count=len(dedupe_removed_ids),
        round_trace=tuple(round_trace),
        attrition_ledger=attrition_ledger,
    )


def assert_selection_trace_parity(
    *,
    production: PlacementGenome,
    trace: GreedyRegretSelectionTraceResult,
) -> None:
    assert production.commit_order == trace.commit_order, (
        f"trace commit_order mismatch: {len(production.commit_order)} vs "
        f"{len(trace.commit_order)}"
    )


def attrition_class_coverage(trace: GreedyRegretSelectionTraceResult) -> float:
    removed = [
        row for row in trace.attrition_ledger if row.attrition_class is not AttritionClass.SELECTED
    ]
    if not removed:
        return 1.0
    known = sum(1 for row in removed if row.attrition_class is not AttritionClass.UNKNOWN_ATTRITION)
    return known / len(removed)


def build_universe_reconciliation_row(
    *,
    candidate_pool_total: int,
    normal_candidate_count: int,
    commit_order_len: int,
    primary_committed_count: int,
) -> dict[str, int]:
    return {
        "candidate_pool_total": candidate_pool_total,
        "normal_candidate_count": normal_candidate_count,
        "commit_order_len": commit_order_len,
        "primary_committed_count": primary_committed_count,
    }


__all__ = [
    "AttritionClass",
    "GreedyRegretRoundTraceRow",
    "GreedyRegretSelectionTraceResult",
    "NormalCandidateAttritionRow",
    "SelectionStopReason",
    "assert_selection_trace_parity",
    "attrition_class_coverage",
    "build_universe_reconciliation_row",
    "trace_greedy_regret_selection",
]
