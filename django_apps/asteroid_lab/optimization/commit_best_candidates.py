"""Phase J — incremental commit with commit-time route reprobe (PR5)."""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from django_apps.asteroid_lab.optimization.candidate_dtos import GeneCandidate
from django_apps.asteroid_lab.optimization.candidate_score import GoalLoadKey
from django_apps.asteroid_lab.optimization.candidate_selector import SelectedCandidatePlan
from django_apps.asteroid_lab.optimization.enums import (
    CommitConflictReason,
    PlacementCommitState,
    ReservationState,
    RouteProbeFailureReason,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RouteDomainCellTransition,
    RouteReservation,
)
from django_apps.asteroid_lab.optimization.route_domain import (
    RouteCellDomain,
    RouteDomainSnapshotBuilder,
)
from django_apps.asteroid_lab.optimization.route_probe import (
    RouteProbeInput,
    RouteProbeResult,
    run_route_probe,
)
from django_apps.asteroid_lab.optimization.timing_metrics import CommitTiming

DEFAULT_COMMIT_PROBE_MAX_EXPANSIONS = 256


@dataclass(frozen=True, slots=True)
class ConfirmedGenePlacement:
    candidate_id: str
    reservation: RouteReservation
    commit_state: PlacementCommitState


@dataclass(frozen=True, slots=True)
class SkippedCandidateRecord:
    candidate_id: str
    reason: CommitConflictReason
    route_probe_failure_reason: RouteProbeFailureReason | None = None
    anchor_coord: tuple[int, int] | None = None
    reached_goal_coord: tuple[int, int] | None = None


@dataclass(frozen=True, slots=True)
class IncrementalCommitResult:
    confirmed: tuple[ConfirmedGenePlacement, ...]
    skipped_candidates: tuple[SkippedCandidateRecord, ...]
    goal_assigned_platforms: dict[GoalLoadKey, int]

    @property
    def skipped_candidate_ids(self) -> tuple[str, ...]:
        return tuple(r.candidate_id for r in self.skipped_candidates)


@dataclass(frozen=True, slots=True)
class CommitDiagnostics:
    """Commit survivability metrics (deferred retry); summary/replay only."""

    primary_route_probe_failed_count: int = 0
    deferred_retry_eligible_count: int = 0
    deferred_retry_recovered_count: int = 0
    deferred_retry_still_failed_count: int = 0
    deferred_retry_rounds: int = 0


@dataclass
class _CommitState:
    reservations: list[RouteReservation]
    committed_occupied: set[tuple[int, int]]
    committed_equipment_cells: set[tuple[int, int]]
    committed_route_cells: set[tuple[int, int]]
    goal_load: dict[GoalLoadKey, int]
    confirmed: list[ConfirmedGenePlacement]
    skipped_records: list[SkippedCandidateRecord]
    ordinal: int


@dataclass(frozen=True, slots=True)
class _AttemptConfirmed:
    candidate_id: str
    reservation: RouteReservation
    occupied_cells: frozenset[tuple[int, int]]
    equipment_cells: frozenset[tuple[int, int]]
    path: tuple[tuple[int, int], ...]
    goal_key: GoalLoadKey


@dataclass(frozen=True, slots=True)
class _AttemptSkipped:
    reason: CommitConflictReason
    probe: RouteProbeResult | None = None


@dataclass(frozen=True, slots=True)
class _AttemptProbeFailed:
    probe: RouteProbeResult | None = None


_AttemptOutcome = _AttemptConfirmed | _AttemptSkipped | _AttemptProbeFailed


def _path_transport_conflict(
    path: tuple[tuple[int, int], ...],
    transport_kind: TransportKind,
    reservations: tuple[RouteReservation, ...],
) -> CommitConflictReason | None:
    reserved: dict[tuple[int, int], TransportKind] = {}
    for res in reservations:
        for cell in res.reserved_cells:
            reserved[cell] = res.transport_kind
    for cell in path:
        existing = reserved.get(cell)
        if existing is not None and existing != transport_kind:
            return CommitConflictReason.TRANSPORT_KIND_CONFLICT
    return None


def _occupied_conflict(
    occupied: frozenset[tuple[int, int]],
    committed_occupied: frozenset[tuple[int, int]],
) -> CommitConflictReason | None:
    if occupied & committed_occupied:
        return CommitConflictReason.OCCUPIED_CELL_CONFLICT
    return None


def _equipment_cells_for_candidate(candidate: GeneCandidate) -> frozenset[tuple[int, int]]:
    return candidate.occupied_cells | frozenset(
        {candidate.extractor, candidate.fixed_output_transport}
    )


def _inlet_on_shared_transport_conflict(
    candidate: GeneCandidate,
    committed_route_cells: frozenset[tuple[int, int]],
) -> CommitConflictReason | None:
    """Reject outlet stub on an existing transport cell (blocks shared-trunk inlet)."""

    if candidate.fixed_output_transport in committed_route_cells:
        return CommitConflictReason.INLET_ON_SHARED_TRANSPORT
    return None


def _equipment_transport_overlap(
    *,
    candidate: GeneCandidate,
    path: tuple[tuple[int, int], ...],
    committed_equipment_cells: frozenset[tuple[int, int]],
    committed_route_cells: frozenset[tuple[int, int]],
) -> CommitConflictReason | None:
    """Reject route through committed equipment; extractor on transport cell.

    Extensions may occupy committed transport coords (shared trunk); Phase K2 drops
    equipment there. Inlet blocking uses ``_inlet_on_shared_transport_conflict`` (stub only).
    """

    path_set = frozenset(path)
    if path_set & committed_equipment_cells:
        return CommitConflictReason.EQUIPMENT_TRANSPORT_OVERLAP
    if candidate.extractor in committed_route_cells:
        return CommitConflictReason.EQUIPMENT_TRANSPORT_OVERLAP
    return None


def _protected_corridor_conflict(
    path: tuple[tuple[int, int], ...],
    inp: OptimizationInput,
) -> CommitConflictReason | None:
    if inp.protected_corridor_cells and any(c in inp.protected_corridor_cells for c in path):
        return CommitConflictReason.HARD_PROTECTED_CONFLICT
    return None


def _hard_blocked_conflict(
    path: tuple[tuple[int, int], ...],
    inp: OptimizationInput,
) -> CommitConflictReason | None:
    if any(c in inp.blocked_cells for c in path):
        return CommitConflictReason.HARD_BLOCKED_CONFLICT
    return None


def _domain_cell_transitions(
    before: dict[tuple[int, int], RouteCellDomain],
    after: dict[tuple[int, int], RouteCellDomain],
    coords: frozenset[tuple[int, int]],
) -> tuple[RouteDomainCellTransition, ...]:
    out: list[RouteDomainCellTransition] = []
    for coord in sorted(coords):
        prev = before.get(coord)
        nxt = after.get(coord)
        if prev is None or nxt is None:
            continue
        if prev.route_class != nxt.route_class:
            out.append(
                RouteDomainCellTransition(
                    coord=coord,
                    route_class_before=prev.route_class,
                    route_class_after=nxt.route_class,
                )
            )
    return tuple(out)


def _record_skip(
    skipped_records: list[SkippedCandidateRecord],
    *,
    candidate: GeneCandidate,
    reason: CommitConflictReason,
    probe: RouteProbeResult | None = None,
) -> None:
    reached_goal_coord: tuple[int, int] | None = None
    route_probe_failure_reason: RouteProbeFailureReason | None = None
    if probe is not None:
        route_probe_failure_reason = probe.failure_reason
        if probe.reached_goal is not None:
            reached_goal_coord = probe.reached_goal.coord
    skipped_records.append(
        SkippedCandidateRecord(
            candidate_id=candidate.candidate_id,
            reason=reason,
            route_probe_failure_reason=route_probe_failure_reason,
            anchor_coord=candidate.extractor,
            reached_goal_coord=reached_goal_coord,
        )
    )


def _normalize_probe_path(
    candidate: GeneCandidate,
    path: tuple[tuple[int, int], ...],
) -> tuple[tuple[int, int], ...]:
    fot = candidate.fixed_output_transport
    if not path:
        return path
    if fot in path:
        idx = path.index(fot)
        return path[idx:]
    return (fot,) + path


def _attempt_commit_one(
    candidate: GeneCandidate,
    *,
    state: _CommitState,
    inp: OptimizationInput,
    max_probe_expansions: int,
    commit_timing: CommitTiming,
) -> _AttemptOutcome:
    before_domain = RouteDomainSnapshotBuilder.build_snapshot(
        inp,
        confirmed_reservations=tuple(state.reservations),
        committed_occupied_cells=frozenset(state.committed_occupied),
    )
    probe_start = time.perf_counter()
    probe = run_route_probe(
        RouteProbeInput(
            start=candidate.route_probe_start,
            goals=inp.route_goals,
            route_domain=before_domain,
            topology_graph=inp.topology_graph,
            max_expansions=max_probe_expansions,
            transport_kind=candidate.transport_kind,
        )
    )
    commit_timing.route_probe_count += 1
    commit_timing.route_probe_expanded_nodes_total += probe.expanded_nodes
    commit_timing.commit_reprobe_ms += (time.perf_counter() - probe_start) * 1000.0

    if not probe.reachable or probe.reached_goal is None or probe.goal_priority is None:
        return _AttemptProbeFailed(probe=probe)

    path = _normalize_probe_path(candidate, probe.path)
    skip_reason: CommitConflictReason | None = (
        _path_transport_conflict(path, candidate.transport_kind, tuple(state.reservations))
        or _protected_corridor_conflict(path, inp)
        or _hard_blocked_conflict(path, inp)
        or _inlet_on_shared_transport_conflict(
            candidate,
            frozenset(state.committed_route_cells),
        )
        or _equipment_transport_overlap(
            candidate=candidate,
            path=path,
            committed_equipment_cells=frozenset(state.committed_equipment_cells),
            committed_route_cells=frozenset(state.committed_route_cells),
        )
    )
    if skip_reason is not None:
        return _AttemptSkipped(reason=skip_reason, probe=probe)

    temp_reservation = RouteReservation(
        reservation_id=f"{candidate.candidate_id}:route:{state.ordinal}",
        candidate_id=candidate.candidate_id,
        transport_kind=candidate.transport_kind,
        path=path,
        reserved_cells=frozenset(path),
        cost=probe.cost,
        reached_goal=probe.reached_goal,
        goal_priority=probe.goal_priority,
        reservation_state=ReservationState.CONFIRMED,
        domain_cell_transitions=(),
    )
    after_domain = RouteDomainSnapshotBuilder.build_snapshot(
        inp,
        confirmed_reservations=tuple(state.reservations) + (temp_reservation,),
        committed_occupied_cells=frozenset(state.committed_occupied),
    )
    transitions = _domain_cell_transitions(before_domain, after_domain, frozenset(path))
    reservation = RouteReservation(
        reservation_id=temp_reservation.reservation_id,
        candidate_id=temp_reservation.candidate_id,
        transport_kind=temp_reservation.transport_kind,
        path=temp_reservation.path,
        reserved_cells=temp_reservation.reserved_cells,
        cost=temp_reservation.cost,
        reached_goal=temp_reservation.reached_goal,
        goal_priority=temp_reservation.goal_priority,
        reservation_state=temp_reservation.reservation_state,
        domain_cell_transitions=transitions,
    )
    reached = probe.reached_goal
    kind = (
        reached.transport_kind if reached.transport_kind is not None else candidate.transport_kind
    )
    goal_key: GoalLoadKey = (reached.coord, kind)
    return _AttemptConfirmed(
        candidate_id=candidate.candidate_id,
        reservation=reservation,
        occupied_cells=candidate.occupied_cells,
        equipment_cells=_equipment_cells_for_candidate(candidate),
        path=path,
        goal_key=goal_key,
    )


def _apply_confirmed(state: _CommitState, confirmed: _AttemptConfirmed) -> None:
    state.reservations.append(confirmed.reservation)
    state.committed_occupied.update(confirmed.occupied_cells)
    state.committed_equipment_cells.update(confirmed.equipment_cells)
    state.committed_route_cells.update(confirmed.path)
    state.goal_load[confirmed.goal_key] = state.goal_load.get(confirmed.goal_key, 0) + 1
    state.confirmed.append(
        ConfirmedGenePlacement(
            candidate_id=confirmed.candidate_id,
            reservation=confirmed.reservation,
            commit_state=PlacementCommitState.CONFIRMED,
        )
    )
    state.ordinal += 1


def _process_candidate_attempt(
    candidate: GeneCandidate,
    *,
    state: _CommitState,
    inp: OptimizationInput,
    max_probe_expansions: int,
    commit_timing: CommitTiming,
    deferred_retry_rounds: int,
    deferred_queue: list[str] | None,
) -> Literal["confirmed", "skipped", "deferred", "occupied_skip"]:
    occ = frozenset(state.committed_occupied)
    if _occupied_conflict(candidate.occupied_cells, occ) is not None:
        _record_skip(
            state.skipped_records,
            candidate=candidate,
            reason=CommitConflictReason.OCCUPIED_CELL_CONFLICT,
        )
        return "occupied_skip"

    outcome = _attempt_commit_one(
        candidate,
        state=state,
        inp=inp,
        max_probe_expansions=max_probe_expansions,
        commit_timing=commit_timing,
    )
    if isinstance(outcome, _AttemptConfirmed):
        _apply_confirmed(state, outcome)
        return "confirmed"

    if isinstance(outcome, _AttemptProbeFailed):
        if deferred_retry_rounds > 0 and deferred_queue is not None:
            deferred_queue.append(candidate.candidate_id)
            return "deferred"
        _record_skip(
            state.skipped_records,
            candidate=candidate,
            reason=CommitConflictReason.ROUTE_PROBE_FAILED,
            probe=outcome.probe,
        )
        return "skipped"

    _record_skip(
        state.skipped_records,
        candidate=candidate,
        reason=outcome.reason,
        probe=outcome.probe,
    )
    return "skipped"


def commit_selected_candidates(
    plan: SelectedCandidatePlan,
    candidates_by_id: Mapping[str, GeneCandidate],
    *,
    inp: OptimizationInput,
    max_probe_expansions: int = DEFAULT_COMMIT_PROBE_MAX_EXPANSIONS,
    deferred_retry_rounds: int = 1,
) -> tuple[IncrementalCommitResult, CommitTiming, CommitDiagnostics]:
    """Commit candidates in plan order; reprobe on latest route_domain each attempt."""

    if deferred_retry_rounds < 0:
        msg = "deferred_retry_rounds must be >= 0"
        raise ValueError(msg)

    commit_timing = CommitTiming()
    state = _CommitState(
        reservations=[],
        committed_occupied=set(),
        committed_equipment_cells=set(),
        committed_route_cells=set(),
        goal_load={},
        confirmed=[],
        skipped_records=[],
        ordinal=0,
    )
    deferred_queue: list[str] = []
    primary_probe_failed_count = 0

    for cid in plan.ordered_candidate_ids:
        candidate = candidates_by_id[cid]
        result = _process_candidate_attempt(
            candidate,
            state=state,
            inp=inp,
            max_probe_expansions=max_probe_expansions,
            commit_timing=commit_timing,
            deferred_retry_rounds=deferred_retry_rounds,
            deferred_queue=deferred_queue if deferred_retry_rounds > 0 else None,
        )
        if result == "deferred":
            primary_probe_failed_count += 1

    recovered_count = 0
    still_failed_count = 0
    rounds_run = 0
    if deferred_retry_rounds > 0 and deferred_queue:
        rounds_run = min(deferred_retry_rounds, 1)
        for cid in deferred_queue:
            candidate = candidates_by_id[cid]
            skip_count_before = len(state.skipped_records)
            result = _process_candidate_attempt(
                candidate,
                state=state,
                inp=inp,
                max_probe_expansions=max_probe_expansions,
                commit_timing=commit_timing,
                deferred_retry_rounds=0,
                deferred_queue=None,
            )
            if result == "confirmed":
                recovered_count += 1
                continue
            new_records = state.skipped_records[skip_count_before:]
            if any(
                r.candidate_id == cid and r.reason is CommitConflictReason.ROUTE_PROBE_FAILED
                for r in new_records
            ):
                still_failed_count += 1

    if deferred_retry_rounds == 0:
        primary_probe_failed_count = sum(
            1
            for r in state.skipped_records
            if r.reason is CommitConflictReason.ROUTE_PROBE_FAILED
        )

    diagnostics = CommitDiagnostics(
        primary_route_probe_failed_count=primary_probe_failed_count,
        deferred_retry_eligible_count=len(deferred_queue),
        deferred_retry_recovered_count=recovered_count,
        deferred_retry_still_failed_count=still_failed_count,
        deferred_retry_rounds=rounds_run,
    )

    result = IncrementalCommitResult(
        confirmed=tuple(state.confirmed),
        skipped_candidates=tuple(state.skipped_records),
        goal_assigned_platforms=dict(state.goal_load),
    )
    return result, commit_timing, diagnostics


__all__ = [
    "CommitDiagnostics",
    "ConfirmedGenePlacement",
    "DEFAULT_COMMIT_PROBE_MAX_EXPANSIONS",
    "IncrementalCommitResult",
    "SkippedCandidateRecord",
    "commit_selected_candidates",
]
