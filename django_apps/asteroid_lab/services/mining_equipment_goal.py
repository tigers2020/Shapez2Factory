"""Mining equipment goal — read-only measurement (MEG-C1/C2).

Pass-qualified extractor + extension equipment cells on mineable platform cells.
Not imported by selection or commit ordering.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import ROUND_CEILING, Decimal

from django_apps.asteroid_lab.contracts.rttp_optimization_goal import (
    MINING_EQUIPMENT_GOAL_SHORTFALL_ISSUE_CODE,
    RttpRunStatus,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.commit.incremental_commit import CommitResult
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind


def compute_target_mining_equipment_cells(
    *,
    mineable_cell_count: int,
    placement_target_percent: int,
) -> int:
    """Target count of mining equipment cells (ceil coverage %). Spec §4."""

    if mineable_cell_count <= 0 or placement_target_percent <= 0:
        return 0
    product = Decimal(mineable_cell_count) * Decimal(placement_target_percent) / Decimal(100)
    return int(product.to_integral_value(rounding=ROUND_CEILING))


def _translate_offset(anchor: Coord, offset: Coord) -> Coord:
    return (anchor[0] + offset[0], anchor[1] + offset[1])


def mining_equipment_cells(
    candidate: BundleCandidate,
    *,
    mineable_cells: frozenset[Coord],
) -> frozenset[Coord]:
    """Extractor + extension absolute coords intersected with mineable cells."""

    anchor = candidate.anchor_coord
    equipment: set[Coord] = {_translate_offset(anchor, candidate.pattern.extractor_offset)}
    for off in candidate.pattern.extension_offsets:
        equipment.add(_translate_offset(anchor, off))
    return frozenset(c for c in equipment if c in mineable_cells)


@dataclass(frozen=True, slots=True)
class MiningEquipmentGoalPlan:
    mineable_cell_count: int
    placement_target_percent: int
    target_mining_equipment_cells: int

    @property
    def placement_goal_count(self) -> int:
        """Deprecated alias — same value as ``target_mining_equipment_cells``."""

        return self.target_mining_equipment_cells


@dataclass(frozen=True, slots=True)
class ExteriorPassEvidence:
    candidate_id: str
    transport_kind: TransportKind
    output_stub_reserved: bool
    reached_elcp_lane_id: str | None
    reached_external_margin: bool
    shareable_trunk_overlap_only: bool
    lane_capacity_ok: bool


def has_confirmed_exterior_pass(
    evidence: ExteriorPassEvidence,
    *,
    elcp_plan_active: bool,
) -> bool:
    if not evidence.output_stub_reserved:
        return False
    if not evidence.shareable_trunk_overlap_only:
        return False
    if elcp_plan_active:
        return evidence.reached_elcp_lane_id is not None and evidence.lane_capacity_ok
    return evidence.reached_external_margin


@dataclass(frozen=True, slots=True)
class _NormalizedLaneAssignment:
    candidate_id: str
    exterior_lane_id: str | None
    legacy_elcp_fallback: bool
    reached_goal: Coord | None


def _normalize_exterior_lane_assignments(
    commit_result: CommitResult,
) -> dict[str, _NormalizedLaneAssignment]:
    out: dict[str, _NormalizedLaneAssignment] = {}
    for raw in commit_result.exterior_lane_assignments:
        if not isinstance(raw, dict):
            continue
        cid = raw.get("candidate_id")
        if not isinstance(cid, str):
            continue
        reached: Coord | None = None
        rg = raw.get("reached_goal")
        if isinstance(rg, list) and len(rg) >= 2:
            reached = (int(rg[0]), int(rg[1]))
        lane_raw = raw.get("exterior_lane_id")
        out[cid] = _NormalizedLaneAssignment(
            candidate_id=cid,
            exterior_lane_id=str(lane_raw) if lane_raw else None,
            legacy_elcp_fallback=bool(raw.get("legacy_elcp_fallback")),
            reached_goal=reached,
        )
    return out


def _normalize_elcp_route_evidence_by_candidate(
    commit_result: CommitResult,
) -> frozenset[str]:
    return frozenset(ev.candidate_id for ev in commit_result.exterior_lane_route_evidence)


def build_exterior_pass_evidence_for_committed_bundles(
    *,
    commit_result: CommitResult,
    candidates_by_id: dict[str, BundleCandidate],
    inp_transport_kind: TransportKind,
    elcp_plan_active: bool,
    exterior_lane_plan_present: bool,
) -> tuple[ExteriorPassEvidence, ...]:
    assignment_by_id = _normalize_exterior_lane_assignments(commit_result)
    elcp_route_ids = _normalize_elcp_route_evidence_by_candidate(commit_result)
    reserved = commit_result.reserved_route_cells
    out: list[ExteriorPassEvidence] = []
    for cid in commit_result.committed_ids:
        candidate = candidates_by_id.get(cid)
        if candidate is None:
            continue
        row = assignment_by_id.get(cid)
        legacy_fallback = bool(row and row.legacy_elcp_fallback)
        has_reached_goal = row is not None and row.reached_goal is not None
        lane_id: str | None = None
        if (
            elcp_plan_active
            and exterior_lane_plan_present
            and row is not None
            and not legacy_fallback
            and has_reached_goal
        ):
            lane_id = row.exterior_lane_id
        reached_margin = cid in elcp_route_ids or has_reached_goal
        if not elcp_plan_active:
            reached_margin = candidate.output_stub in reserved
        out.append(
            ExteriorPassEvidence(
                candidate_id=cid,
                transport_kind=inp_transport_kind,
                output_stub_reserved=candidate.output_stub in reserved,
                reached_elcp_lane_id=lane_id,
                reached_external_margin=reached_margin,
                shareable_trunk_overlap_only=True,
                lane_capacity_ok=lane_id is not None or not elcp_plan_active,
            )
        )
    return tuple(out)


@dataclass(frozen=True, slots=True)
class MiningEquipmentGoalResult:
    target_mining_equipment_cells: int
    confirmed_passed_mining_equipment_cells: int
    confirmed_committed_bundle_count: int
    shortfall: int
    confirmed_transport_route_cell_count: int = 0
    confirmed_trunk_cell_count: int = 0
    confirmed_external_link_touch_count: int = 0


def aggregate_mining_equipment_goal_result(
    *,
    evidence_rows: tuple[ExteriorPassEvidence, ...],
    candidates_by_id: dict[str, BundleCandidate],
    mineable_cells: frozenset[Coord],
    target_mining_equipment_cells: int,
    elcp_plan_active: bool,
    committed_ids: tuple[str, ...],
    reserved_route_cells: frozenset[Coord] | None = None,
) -> MiningEquipmentGoalResult:
    passed_cells = 0
    for ev in evidence_rows:
        if not has_confirmed_exterior_pass(ev, elcp_plan_active=elcp_plan_active):
            continue
        cand = candidates_by_id.get(ev.candidate_id)
        if cand is None:
            continue
        passed_cells += len(mining_equipment_cells(cand, mineable_cells=mineable_cells))
    shortfall = max(0, target_mining_equipment_cells - passed_cells)
    route_count = len(reserved_route_cells or frozenset())
    return MiningEquipmentGoalResult(
        target_mining_equipment_cells=target_mining_equipment_cells,
        confirmed_passed_mining_equipment_cells=passed_cells,
        confirmed_committed_bundle_count=len(committed_ids),
        shortfall=shortfall,
        confirmed_transport_route_cell_count=route_count,
    )


def optimization_goal_passed(result: MiningEquipmentGoalResult) -> bool:
    if result.target_mining_equipment_cells <= 0:
        return True
    return result.confirmed_passed_mining_equipment_cells >= result.target_mining_equipment_cells


def optimization_goal_to_json(result: MiningEquipmentGoalResult) -> dict[str, object]:
    passed = optimization_goal_passed(result)
    return {
        "passed": passed,
        "issue_code": None if passed else MINING_EQUIPMENT_GOAL_SHORTFALL_ISSUE_CODE,
        "target_mining_equipment_cells": result.target_mining_equipment_cells,
        "confirmed_passed_mining_equipment_cells": result.confirmed_passed_mining_equipment_cells,
        "shortfall": result.shortfall,
        "confirmed_committed_bundle_count": result.confirmed_committed_bundle_count,
    }


def resolve_run_status(
    *,
    structural_validation_passed: bool,
    optimization_goal: Mapping[str, object],
) -> RttpRunStatus:
    if not structural_validation_passed:
        return RttpRunStatus.FAIL
    if bool(optimization_goal.get("passed")):
        return RttpRunStatus.SUCCESS
    return RttpRunStatus.PARTIAL_SUCCESS


@dataclass(frozen=True, slots=True)
class MiningEquipmentGoalEvaluation:
    structural_validation_passed: bool
    validation_passed: bool
    optimization_goal: dict[str, object]
    run_status: str


def evaluate_mining_equipment_goal_for_pipeline(
    *,
    structural_validation_passed: bool,
    commit_result: CommitResult,
    candidates_by_id: dict[str, BundleCandidate],
    mineable_cells: frozenset[Coord],
    transport_kind: TransportKind,
    placement_target_percent: int,
    placement_platform_cell_count: int,
    elcp_plan_active: bool,
    exterior_lane_plan_present: bool,
) -> MiningEquipmentGoalEvaluation:
    target = compute_target_mining_equipment_cells(
        mineable_cell_count=placement_platform_cell_count,
        placement_target_percent=placement_target_percent,
    )
    evidence = build_exterior_pass_evidence_for_committed_bundles(
        commit_result=commit_result,
        candidates_by_id=candidates_by_id,
        inp_transport_kind=transport_kind,
        elcp_plan_active=elcp_plan_active,
        exterior_lane_plan_present=exterior_lane_plan_present,
    )
    meg_result = aggregate_mining_equipment_goal_result(
        evidence_rows=evidence,
        candidates_by_id=candidates_by_id,
        mineable_cells=mineable_cells,
        target_mining_equipment_cells=target,
        elcp_plan_active=elcp_plan_active,
        committed_ids=commit_result.committed_ids,
        reserved_route_cells=commit_result.reserved_route_cells,
    )
    optimization_goal = optimization_goal_to_json(meg_result)
    run_status = resolve_run_status(
        structural_validation_passed=structural_validation_passed,
        optimization_goal=optimization_goal,
    )
    validation_passed = structural_validation_passed and bool(optimization_goal["passed"])
    return MiningEquipmentGoalEvaluation(
        structural_validation_passed=structural_validation_passed,
        validation_passed=validation_passed,
        optimization_goal=optimization_goal,
        run_status=run_status.value,
    )


def macro_only_optimization_goal() -> dict[str, object]:
    """MEG not applied on macro-only pipeline runs."""

    return {
        "passed": True,
        "issue_code": None,
        "macro_only_mode": True,
        "target_mining_equipment_cells": 0,
        "confirmed_passed_mining_equipment_cells": 0,
        "shortfall": 0,
        "confirmed_committed_bundle_count": 0,
    }


__all__ = [
    "ExteriorPassEvidence",
    "MiningEquipmentGoalPlan",
    "MiningEquipmentGoalResult",
    "MiningEquipmentGoalEvaluation",
    "aggregate_mining_equipment_goal_result",
    "build_exterior_pass_evidence_for_committed_bundles",
    "compute_target_mining_equipment_cells",
    "evaluate_mining_equipment_goal_for_pipeline",
    "has_confirmed_exterior_pass",
    "macro_only_optimization_goal",
    "mining_equipment_cells",
    "optimization_goal_passed",
    "optimization_goal_to_json",
    "resolve_run_status",
]
