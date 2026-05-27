"""Read-only ELCP primary reprobe forensics (P1-ELCP-RF; not solver input).

INVESTIGATION_COUPLING: mirror loop calls production private helpers from
``incremental_commit`` and ELCP commit modules. Drift is guarded by
``assert_mirror_parity`` tests against production ``incremental_commit``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Any

from django_apps.asteroid_lab.contracts.exterior_lane_capacity import ExteriorLaneCapacityPlan
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    BundleCandidate,
    RouteProbeStartPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.placement_cells import (
    fixed_output_transport_cell,
)
from django_apps.asteroid_lab.optimization.commit.exterior_lane_assignment import (
    increment_assignment_state,
    initial_assignment_state,
)
from django_apps.asteroid_lab.optimization.commit.exterior_lane_fill_first import (
    assign_fill_first_exterior_lane,
)
from django_apps.asteroid_lab.optimization.commit.exterior_lane_trunk import (
    initial_trunk_states,
    partition_path_branch_and_trunk,
    update_trunk_state_after_commit,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    _COMMIT_PROBE_MAX_EXPANSIONS,
    CommitConflict,
    CommitConflictReason,
    CommitDomainState,
    CommitResult,
    _attempt_commit_one,
    _candidate_throughput_per_min,
    _rebuild_domain,
    _reorder_elcp_trunk_states,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.routing.route_goals import (
    probe_goal_coords,
    probe_goal_priorities,
)
from django_apps.asteroid_lab.optimization.routing.route_probe import RouteProbeResult
from django_apps.asteroid_lab.optimization.routing.route_probe_start import (
    resolve_route_probe_start,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton


class ElcpProbeFailureClass(StrEnum):
    START_BLOCKED = "start_blocked"
    LANE_CAPACITY_SHORTFALL = "lane_capacity_shortfall"
    BUDGET_EXCEEDED = "budget_exceeded"
    PROBE_UNREACHABLE = "probe_unreachable"
    NO_GOAL_CELLS = "no_goal_cells"
    POST_PROBE_COMMIT_FAIL = "post_probe_commit_fail"
    STALE_CANDIDATE_REACHABLE = "stale_candidate_reachable"
    DOMAIN_CONGESTION = "domain_congestion"
    TRUNK_ORDERING_PRESSURE = "trunk_ordering_pressure"
    UNKNOWN_REPROBE_FAILED = "unknown_reprobe_failed"


_DOMAIN_CONGESTION_ROUTE_CELL_RATIO = 0.15


@dataclass(frozen=True, slots=True)
class ElcpAttemptLedgerRow:
    candidate_id: str
    commit_index: int
    candidate_reachable: bool
    probe_start: Coord | None
    fill_first_ok: bool
    assigned_lane_id: str | None
    probe_reachable: bool | None
    probe_expanded_nodes: int | None
    max_expansions: int
    probe_failure_class: ElcpProbeFailureClass
    lane_capacity_shortfall_delta: int
    route_feasible_shortfall_delta: int
    commit_conflict_reason: str | None
    domain_version: int
    deferred_retry_eligible: bool
    tm_new_trunk_len: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "commit_index": self.commit_index,
            "candidate_reachable": self.candidate_reachable,
            "probe_start": list(self.probe_start) if self.probe_start else None,
            "fill_first_ok": self.fill_first_ok,
            "assigned_lane_id": self.assigned_lane_id,
            "probe_reachable": self.probe_reachable,
            "probe_expanded_nodes": self.probe_expanded_nodes,
            "max_expansions": self.max_expansions,
            "probe_failure_class": self.probe_failure_class.value,
            "lane_capacity_shortfall_delta": self.lane_capacity_shortfall_delta,
            "route_feasible_shortfall_delta": self.route_feasible_shortfall_delta,
            "commit_conflict_reason": self.commit_conflict_reason,
            "domain_version": self.domain_version,
            "deferred_retry_eligible": self.deferred_retry_eligible,
            "tm_new_trunk_len": self.tm_new_trunk_len,
        }


def classify_probe_failure(
    *,
    probe_start: Coord | None,
    fill_first_ok: bool,
    probe: RouteProbeResult | None,
    max_expansions: int,
    goals_nonempty: bool,
    candidate_reachable: bool,
    post_probe_committed: bool,
    committed_route_cell_count: int,
    traversable_cell_count: int,
    tm_new_trunk_len: int,
    trunk_pressure_correlated: bool,
) -> ElcpProbeFailureClass:
    """Ordered rules per design spec §5.2 (first match wins)."""
    if probe_start is None:
        return ElcpProbeFailureClass.START_BLOCKED
    if not fill_first_ok:
        return ElcpProbeFailureClass.LANE_CAPACITY_SHORTFALL
    if probe is not None and not probe.reachable:
        if not goals_nonempty:
            return ElcpProbeFailureClass.NO_GOAL_CELLS
        if probe.expanded_nodes >= max_expansions:
            return ElcpProbeFailureClass.BUDGET_EXCEEDED
        if (
            traversable_cell_count > 0
            and committed_route_cell_count / traversable_cell_count
            >= _DOMAIN_CONGESTION_ROUTE_CELL_RATIO
        ):
            return ElcpProbeFailureClass.DOMAIN_CONGESTION
        return ElcpProbeFailureClass.PROBE_UNREACHABLE
    if candidate_reachable and probe is not None and probe.reachable and not post_probe_committed:
        return ElcpProbeFailureClass.STALE_CANDIDATE_REACHABLE
    if fill_first_ok and not post_probe_committed:
        if trunk_pressure_correlated and tm_new_trunk_len > 0:
            return ElcpProbeFailureClass.TRUNK_ORDERING_PRESSURE
        return ElcpProbeFailureClass.POST_PROBE_COMMIT_FAIL
    return ElcpProbeFailureClass.UNKNOWN_REPROBE_FAILED


@dataclass(frozen=True, slots=True)
class MirrorDomainSnapshot:
    """Domain state after a successful mirror commit (investigation-only)."""

    commit_index: int
    committed_route_cells: frozenset[Coord]
    committed_occupied: frozenset[Coord]


@dataclass(frozen=True, slots=True)
class ElcpMirrorForensicsResult:
    ledger: tuple[ElcpAttemptLedgerRow, ...]
    mirror_committed_ids: tuple[str, ...]
    mirror_lane_capacity_shortfall_count: int
    mirror_route_feasible_shortfall_count: int
    mirror_conflict_count: int
    domain_snapshots_after_success: tuple[MirrorDomainSnapshot, ...] = ()
    domain_snapshots_at_attempt: tuple[MirrorDomainSnapshot, ...] = ()


def _append_ledger_row(
    ledger: list[ElcpAttemptLedgerRow],
    *,
    candidate_id: str,
    commit_index: int,
    candidate: BundleCandidate,
    probe_start: Coord | None,
    fill_first_ok: bool,
    assigned_lane_id: str | None,
    probe: RouteProbeResult | None,
    max_expansions: int,
    goals_nonempty: bool,
    post_probe_committed: bool,
    committed_route_cell_count: int,
    traversable_cell_count: int,
    tm_new_trunk_len: int,
    lane_capacity_shortfall_delta: int,
    route_feasible_shortfall_delta: int,
    conflict: CommitConflict | None,
    domain_version: int,
    trunk_pressure_correlated: bool,
) -> None:
    failure_class = classify_probe_failure(
        probe_start=probe_start,
        fill_first_ok=fill_first_ok,
        probe=probe,
        max_expansions=max_expansions,
        goals_nonempty=goals_nonempty,
        candidate_reachable=candidate.reachable,
        post_probe_committed=post_probe_committed,
        committed_route_cell_count=committed_route_cell_count,
        traversable_cell_count=traversable_cell_count,
        tm_new_trunk_len=tm_new_trunk_len,
        trunk_pressure_correlated=trunk_pressure_correlated,
    )
    reason_value = conflict.reason.value if conflict is not None else None
    deferred_eligible = (
        conflict is not None and conflict.reason is CommitConflictReason.REPROBE_FAILED
    )
    ledger.append(
        ElcpAttemptLedgerRow(
            candidate_id=candidate_id,
            commit_index=commit_index,
            candidate_reachable=candidate.reachable,
            probe_start=probe_start,
            fill_first_ok=fill_first_ok,
            assigned_lane_id=assigned_lane_id,
            probe_reachable=probe.reachable if probe is not None else None,
            probe_expanded_nodes=probe.expanded_nodes if probe is not None else None,
            max_expansions=max_expansions,
            probe_failure_class=failure_class,
            lane_capacity_shortfall_delta=lane_capacity_shortfall_delta,
            route_feasible_shortfall_delta=route_feasible_shortfall_delta,
            commit_conflict_reason=reason_value,
            domain_version=domain_version,
            deferred_retry_eligible=deferred_eligible,
            tm_new_trunk_len=tm_new_trunk_len,
        )
    )


def build_elcp_primary_mirror_ledger(
    *,
    genome: PlacementGenome,
    candidates_by_id: dict[str, BundleCandidate],
    inp: OptimizationInput,
    skeleton: RttpSkeleton,
    domain: CommitDomainState,
    exterior_lane_plan: ExteriorLaneCapacityPlan,
    route_probe_start_policy: RouteProbeStartPolicy,
    resource_kind: str,
    max_expansions: int | None = None,
    collect_domain_snapshots: bool = False,
) -> ElcpMirrorForensicsResult:
    """Mirror ELCP ``incremental_commit`` loop; ledger rows for failed attempts only."""
    use_elcp = len(exterior_lane_plan.lanes) > 0
    if not use_elcp:
        msg = "mirror forensics requires active exterior_lane_plan"
        raise ValueError(msg)

    resolved_max = _COMMIT_PROBE_MAX_EXPANSIONS if max_expansions is None else max_expansions
    goals = probe_goal_coords(inp, skeleton)
    goal_priorities = probe_goal_priorities(inp)
    goals_nonempty = len(goals) > 0

    committed_ids: list[str] = []
    conflicts: list[CommitConflict] = []
    ledger: list[ElcpAttemptLedgerRow] = []

    committed_occupied = domain.committed_occupied
    committed_route_cells = domain.committed_route_cells
    committed_fixed_output_transport_cells = domain.committed_fixed_output_transport_cells
    trunk_mask_cells = domain.trunk_mask_cells
    domain_version = domain.version

    assignment_state = initial_assignment_state(exterior_lane_plan)
    lane_capacity_shortfall_count = 0
    route_feasible_shortfall_count = 0
    trunk_states_elcp = initial_trunk_states(exterior_lane_plan)
    snapshots_after_success: list[MirrorDomainSnapshot] = []
    snapshots_at_attempt: list[MirrorDomainSnapshot] = []

    for commit_index, candidate_id in enumerate(genome.commit_order):
        if collect_domain_snapshots:
            snapshots_at_attempt.append(
                MirrorDomainSnapshot(
                    commit_index=commit_index,
                    committed_route_cells=committed_route_cells,
                    committed_occupied=committed_occupied,
                )
            )
        candidate = candidates_by_id.get(candidate_id)
        if candidate is None:
            conflicts.append(
                CommitConflict(
                    candidate_id=candidate_id,
                    reason=CommitConflictReason.CANDIDATE_NOT_FOUND,
                )
            )
            continue

        commit_goals = goals
        pending_lane_id: str | None = None
        pending_throughput = Decimal("0")
        pending_assignment_row: dict[str, object] | None = None
        precomputed_route: frozenset[Coord] | None = None
        precomputed_probe: RouteProbeResult | None = None
        lane_shareable: frozenset[Coord] | None = None
        tm_branch: tuple[Coord, ...] = ()
        tm_new_trunk: tuple[Coord, ...] = ()
        pending_fill_trunk_states = None
        fill_first_ok = False
        probe_start: Coord | None = None
        probe_for_class: RouteProbeResult | None = None
        tm_new_trunk_len = 0

        current_domain = _rebuild_domain(
            skeleton,
            inp,
            committed_occupied=committed_occupied,
            committed_route_cells=committed_route_cells,
        )
        traversable_cell_count = len(current_domain.traversable_cells)
        probe_start = resolve_route_probe_start(
            anchor_coord=candidate.anchor_coord,
            output_stub=candidate.output_stub,
            domain=current_domain,
            policy=route_probe_start_policy,
        )
        if probe_start is None:
            route_feasible_shortfall_count += 1
            conflict = CommitConflict(
                candidate_id=candidate_id,
                reason=CommitConflictReason.REPROBE_FAILED,
            )
            conflicts.append(conflict)
            _append_ledger_row(
                ledger,
                candidate_id=candidate_id,
                commit_index=commit_index,
                candidate=candidate,
                probe_start=None,
                fill_first_ok=False,
                assigned_lane_id=None,
                probe=None,
                max_expansions=resolved_max,
                goals_nonempty=goals_nonempty,
                post_probe_committed=False,
                committed_route_cell_count=len(committed_route_cells),
                traversable_cell_count=traversable_cell_count,
                tm_new_trunk_len=0,
                lane_capacity_shortfall_delta=0,
                route_feasible_shortfall_delta=1,
                conflict=conflict,
                domain_version=domain_version,
                trunk_pressure_correlated=False,
            )
            continue

        throughput = _candidate_throughput_per_min(
            candidate,
            resource_kind=resource_kind,
        )
        fill_first = assign_fill_first_exterior_lane(
            candidate,
            plan=exterior_lane_plan,
            assignment_state=assignment_state,
            trunk_states=trunk_states_elcp,
            domain=current_domain,
            candidate_throughput_per_min=throughput,
            probe_start=probe_start,
            max_expansions=resolved_max,
            trigger_candidate_id=candidate_id,
        )
        if fill_first is None:
            lane_capacity_shortfall_count += 1
            route_feasible_shortfall_count += 1
            conflict = CommitConflict(
                candidate_id=candidate_id,
                reason=CommitConflictReason.REPROBE_FAILED,
            )
            conflicts.append(conflict)
            _append_ledger_row(
                ledger,
                candidate_id=candidate_id,
                commit_index=commit_index,
                candidate=candidate,
                probe_start=probe_start,
                fill_first_ok=False,
                assigned_lane_id=None,
                probe=None,
                max_expansions=resolved_max,
                goals_nonempty=goals_nonempty,
                post_probe_committed=False,
                committed_route_cell_count=len(committed_route_cells),
                traversable_cell_count=traversable_cell_count,
                tm_new_trunk_len=0,
                lane_capacity_shortfall_delta=1,
                route_feasible_shortfall_delta=1,
                conflict=conflict,
                domain_version=domain_version,
                trunk_pressure_correlated=False,
            )
            continue

        fill_first_ok = True
        trunk_row_pre = next(s for s in trunk_states_elcp if s.lane_id == fill_first.lane_id)
        lane_spec = next(
            lane for lane in exterior_lane_plan.lanes if lane.lane_id == fill_first.lane_id
        )
        tm_branch, _tm_reused, tm_new_trunk = partition_path_branch_and_trunk(
            path=fill_first.probe.path,
            existing_trunk=trunk_row_pre.trunk_cells,
            connector_coord=lane_spec.connector_goal.coord,
        )
        tm_new_trunk_len = len(tm_new_trunk)
        route_delta = frozenset(tm_branch) | frozenset(tm_new_trunk)
        lane_shareable = frozenset(trunk_row_pre.trunk_cells) | frozenset(tm_new_trunk)
        precomputed_route = route_delta
        precomputed_probe = fill_first.probe
        probe_for_class = fill_first.probe
        commit_goals = frozenset({fill_first.connector_coord})
        pending_lane_id = fill_first.lane_id
        pending_throughput = throughput
        pending_assignment_row = {
            "candidate_id": candidate_id,
            "exterior_lane_id": fill_first.lane_id,
        }
        pending_fill_trunk_states = fill_first.trunk_states

        outcome = _attempt_commit_one(
            candidate,
            skeleton=skeleton,
            inp=inp,
            goals=commit_goals,
            goal_priorities=goal_priorities,
            committed_occupied=committed_occupied,
            committed_route_cells=committed_route_cells,
            committed_fixed_output_transport_cells=committed_fixed_output_transport_cells,
            route_probe_start_policy=route_probe_start_policy,
            max_expansions=resolved_max,
            precomputed_route_cells=precomputed_route,
            precomputed_probe=precomputed_probe,
            shareable_trunk_cells=lane_shareable,
        )
        if not outcome.committed:
            route_delta_inc = 0
            if pending_assignment_row is not None:
                route_feasible_shortfall_count += 1
                route_delta_inc = 1
            if outcome.conflict is not None:
                conflicts.append(outcome.conflict)
            _append_ledger_row(
                ledger,
                candidate_id=candidate_id,
                commit_index=commit_index,
                candidate=candidate,
                probe_start=probe_start,
                fill_first_ok=fill_first_ok,
                assigned_lane_id=pending_lane_id,
                probe=probe_for_class,
                max_expansions=resolved_max,
                goals_nonempty=len(commit_goals) > 0,
                post_probe_committed=False,
                committed_route_cell_count=len(committed_route_cells),
                traversable_cell_count=traversable_cell_count,
                tm_new_trunk_len=tm_new_trunk_len,
                lane_capacity_shortfall_delta=0,
                route_feasible_shortfall_delta=route_delta_inc,
                conflict=outcome.conflict,
                domain_version=domain_version,
                trunk_pressure_correlated=tm_new_trunk_len > 0,
            )
            continue

        if pending_assignment_row is not None and pending_lane_id is not None:
            assignment_state = increment_assignment_state(
                assignment_state,
                lane_id=pending_lane_id,
                delta=pending_throughput,
            )
            if pending_fill_trunk_states is not None:
                trunk_states_elcp = pending_fill_trunk_states
                by_lane = {s.lane_id: s for s in trunk_states_elcp}
                updated = update_trunk_state_after_commit(
                    by_lane[pending_lane_id],
                    new_trunk_cells=tm_new_trunk,
                    assigned_delta=pending_throughput,
                )
                by_lane[pending_lane_id] = updated
                trunk_states_elcp = _reorder_elcp_trunk_states(exterior_lane_plan, by_lane)

        route_cells = outcome.route_cells
        committed_ids.append(candidate_id)
        committed_occupied = frozenset(committed_occupied | candidate.occupied_cells)
        committed_fixed_output_transport_cells = frozenset(
            committed_fixed_output_transport_cells | {fixed_output_transport_cell(candidate)}
        )
        committed_route_cells = frozenset(committed_route_cells | route_cells)
        trunk_mask_cells = frozenset(trunk_mask_cells | route_cells)
        domain_version += 1
        if collect_domain_snapshots:
            snapshots_after_success.append(
                MirrorDomainSnapshot(
                    commit_index=commit_index,
                    committed_route_cells=committed_route_cells,
                    committed_occupied=committed_occupied,
                )
            )

    return ElcpMirrorForensicsResult(
        ledger=tuple(ledger),
        mirror_committed_ids=tuple(committed_ids),
        mirror_lane_capacity_shortfall_count=lane_capacity_shortfall_count,
        mirror_route_feasible_shortfall_count=route_feasible_shortfall_count,
        mirror_conflict_count=len(conflicts),
        domain_snapshots_after_success=tuple(snapshots_after_success),
        domain_snapshots_at_attempt=tuple(snapshots_at_attempt),
    )


def assert_mirror_parity(
    *,
    production: CommitResult,
    mirror: ElcpMirrorForensicsResult,
) -> None:
    assert mirror.mirror_committed_ids == production.committed_ids
    assert mirror.mirror_conflict_count == len(production.conflicts)
    assert mirror.mirror_lane_capacity_shortfall_count == production.lane_capacity_shortfall_count
    assert mirror.mirror_route_feasible_shortfall_count == production.route_feasible_shortfall_count


def build_deferred_retry_audit(
    *,
    primary_commit_result: CommitResult,
    commit_order: Sequence[str],
    candidates_by_id: Mapping[str, BundleCandidate],
    inp: OptimizationInput,
    ledger: Sequence[ElcpAttemptLedgerRow],
) -> dict[str, Any]:
    from django_apps.asteroid_lab.optimization.commit.deferred_retry_shadow import (
        build_deferred_retry_shadow_summary,
    )

    shadow = build_deferred_retry_shadow_summary(
        primary_commit_result=primary_commit_result,
        commit_order=commit_order,
        candidates_by_id=candidates_by_id,
        inp=inp,
    )
    primary_reprobe = sum(
        1
        for conflict in primary_commit_result.conflicts
        if conflict.reason is CommitConflictReason.REPROBE_FAILED
    )
    overlap = [
        {
            "candidate_id": row.candidate_id,
            "probe_failure_class": row.probe_failure_class.value,
            "deferred_retry_eligible": row.deferred_retry_eligible,
        }
        for row in ledger
    ]
    eligible_raw = shadow.domain_context.get("eligible_reprobe_failed_count")
    eligible_count = int(eligible_raw) if isinstance(eligible_raw, int) else shadow.candidate_count
    return {
        "primary_reprobe_failed_count": primary_reprobe,
        "eligible_reprobe_failed_count": eligible_count,
        "shadow_candidate_count": shadow.candidate_count,
        "shadow_enabled": shadow.enabled,
        "overlap_table": overlap,
    }


def load_recovery_evidence_compare(
    *,
    primary_committed_count: int,
    evidence_path: str = (
        "docs/superpowers/reports/2026-05-30-rttp-core-recovery-evidence-after-evtc.json"
    ),
) -> dict[str, Any]:
    import json
    from pathlib import Path

    path = Path(evidence_path)
    if not path.is_file():
        return {"loaded": False, "reason": "evidence file missing"}
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("slugs") or data.get("results") or []
    recovery_row = next(
        (row for row in rows if row.get("slug") == "rttp-core-recovery-test-map"),
        None,
    )
    if recovery_row is None:
        return {"loaded": True, "slug_row": None}
    return {
        "loaded": True,
        "evidence_committed": recovery_row.get("committed_extractor_count"),
        "primary_committed_count": primary_committed_count,
        "validation_passed": recovery_row.get("validation_passed"),
        "gate_a_passed": recovery_row.get("gate_a_passed"),
    }


__all__ = [
    "ElcpAttemptLedgerRow",
    "ElcpMirrorForensicsResult",
    "ElcpProbeFailureClass",
    "MirrorDomainSnapshot",
    "assert_mirror_parity",
    "build_deferred_retry_audit",
    "build_elcp_primary_mirror_ledger",
    "classify_probe_failure",
    "load_recovery_evidence_compare",
]
