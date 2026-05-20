"""Phase J — incremental commit with commit-time route reprobe (PR5)."""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.candidate_dtos import GeneCandidate
from django_apps.asteroid_lab.optimization.candidate_score import GoalLoadKey
from django_apps.asteroid_lab.optimization.candidate_selector import SelectedCandidatePlan
from django_apps.asteroid_lab.optimization.enums import (
    CommitConflictReason,
    PlacementCommitState,
    ReservationState,
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
from django_apps.asteroid_lab.optimization.route_probe import RouteProbeInput, run_route_probe
from django_apps.asteroid_lab.optimization.timing_metrics import CommitTiming

DEFAULT_COMMIT_PROBE_MAX_EXPANSIONS = 256


@dataclass(frozen=True, slots=True)
class ConfirmedGenePlacement:
    candidate_id: str
    reservation: RouteReservation
    commit_state: PlacementCommitState


@dataclass(frozen=True, slots=True)
class IncrementalCommitResult:
    confirmed: tuple[ConfirmedGenePlacement, ...]
    skipped_candidate_ids: tuple[str, ...]
    goal_assigned_platforms: dict[GoalLoadKey, int]


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


def commit_selected_candidates(
    plan: SelectedCandidatePlan,
    candidates_by_id: Mapping[str, GeneCandidate],
    *,
    inp: OptimizationInput,
    max_probe_expansions: int = DEFAULT_COMMIT_PROBE_MAX_EXPANSIONS,
) -> tuple[IncrementalCommitResult, CommitTiming]:
    """Commit candidates in plan order; reprobe on latest route_domain each attempt."""

    commit_timing = CommitTiming()

    reservations: list[RouteReservation] = []
    committed_occupied: set[tuple[int, int]] = set()
    goal_load: dict[GoalLoadKey, int] = {}
    confirmed: list[ConfirmedGenePlacement] = []
    skipped: list[str] = []
    ordinal = 0

    for cid in plan.ordered_candidate_ids:
        candidate = candidates_by_id[cid]
        occ = frozenset(committed_occupied)
        if _occupied_conflict(candidate.occupied_cells, occ) is not None:
            skipped.append(cid)
            continue

        before_domain = RouteDomainSnapshotBuilder.build_snapshot(
            inp,
            confirmed_reservations=tuple(reservations),
            committed_occupied_cells=frozenset(committed_occupied),
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
            skipped.append(cid)
            continue

        path = probe.path
        fot = candidate.fixed_output_transport
        if path:
            if fot in path:
                idx = path.index(fot)
                path = path[idx:]
            else:
                path = (fot,) + path
        skip_reason: CommitConflictReason | None = (
            _path_transport_conflict(path, candidate.transport_kind, tuple(reservations))
            or _protected_corridor_conflict(path, inp)
            or _hard_blocked_conflict(path, inp)
        )
        if skip_reason is not None:
            skipped.append(cid)
            continue

        temp_reservation = RouteReservation(
            reservation_id=f"{candidate.candidate_id}:route:{ordinal}",
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
            confirmed_reservations=tuple(reservations) + (temp_reservation,),
            committed_occupied_cells=frozenset(committed_occupied),
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
        reservations.append(reservation)
        committed_occupied.update(candidate.occupied_cells)
        reached = probe.reached_goal
        kind = (
            reached.transport_kind
            if reached.transport_kind is not None
            else candidate.transport_kind
        )
        key: GoalLoadKey = (reached.coord, kind)
        goal_load[key] = goal_load.get(key, 0) + candidate.base_throughput
        confirmed.append(
            ConfirmedGenePlacement(
                candidate_id=cid,
                reservation=reservation,
                commit_state=PlacementCommitState.CONFIRMED,
            )
        )
        ordinal += 1

    result = IncrementalCommitResult(
        confirmed=tuple(confirmed),
        skipped_candidate_ids=tuple(skipped),
        goal_assigned_platforms=dict(goal_load),
    )
    return result, commit_timing
