"""Commit-time route reservation diagnostic (FL-06 investigation).

Read-only reconstruction of Q1–Q4 at commit time. Not solver input.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    BundleCandidate,
    RouteProbeStartPolicy,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    _attempt_commit_one,
    _rebuild_domain,
    _route_cells_from_path,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.routing.route_probe import probe_route
from django_apps.asteroid_lab.optimization.routing.route_probe_start import (
    resolve_route_probe_start,
)
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton


class PreliminaryFl06Cause(StrEnum):
    H1A_FALLBACK_START_OMITS_STUB = "H1a"
    H1B_PATH_TO_ROUTE_CELLS_OMITS_STUB = "H1b"
    H3_PROBE_START_DRIFT = "H3"
    H4_GEOMETRY_DRIFT = "H4"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True, slots=True)
class CommitRouteReservationSnapshot:
    candidate_id: str
    output_stub: Coord
    probe_start: Coord | None
    probe_start_is_output_stub: bool
    route_probe_start_policy: RouteProbeStartPolicy
    path: tuple[Coord, ...]
    route_cells: frozenset[Coord]
    stub_in_path: bool
    stub_in_route_cells: bool
    attempt_committed: bool


@dataclass(frozen=True, slots=True)
class Fl06QuestionReport:
    q1_probe_start: Coord | None
    q2_probe_start_equals_output_stub: bool
    q3_path_contains_output_stub: bool
    q4_route_cells_contains_output_stub: bool
    start_policy: RouteProbeStartPolicy
    preliminary_outcome: PreliminaryFl06Cause


def classify_preliminary_outcome(
    snapshot: CommitRouteReservationSnapshot,
) -> PreliminaryFl06Cause:
    if snapshot.probe_start is None:
        return PreliminaryFl06Cause.INCONCLUSIVE
    if snapshot.probe_start_is_output_stub:
        if snapshot.stub_in_path and not snapshot.stub_in_route_cells:
            return PreliminaryFl06Cause.H1B_PATH_TO_ROUTE_CELLS_OMITS_STUB
        return PreliminaryFl06Cause.INCONCLUSIVE
    if not snapshot.stub_in_path and not snapshot.stub_in_route_cells:
        return PreliminaryFl06Cause.H1A_FALLBACK_START_OMITS_STUB
    if snapshot.stub_in_path and not snapshot.stub_in_route_cells:
        return PreliminaryFl06Cause.H1B_PATH_TO_ROUTE_CELLS_OMITS_STUB
    return PreliminaryFl06Cause.H3_PROBE_START_DRIFT


def build_fl06_question_report(
    snapshot: CommitRouteReservationSnapshot,
) -> Fl06QuestionReport:
    return Fl06QuestionReport(
        q1_probe_start=snapshot.probe_start,
        q2_probe_start_equals_output_stub=snapshot.probe_start_is_output_stub,
        q3_path_contains_output_stub=snapshot.stub_in_path,
        q4_route_cells_contains_output_stub=snapshot.stub_in_route_cells,
        start_policy=snapshot.route_probe_start_policy,
        preliminary_outcome=classify_preliminary_outcome(snapshot),
    )


def replay_fl06_diagnostics_for_commit_order(
    commit_order: tuple[str, ...],
    candidates_by_id: dict[str, BundleCandidate],
    *,
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    goals: frozenset[Coord],
    route_probe_start_policy: RouteProbeStartPolicy,
) -> list[tuple[CommitRouteReservationSnapshot, Fl06QuestionReport]]:
    """Replay commit order and capture Q1–Q4 snapshots at each step (read-only)."""

    from django_apps.asteroid_lab.optimization.candidates.placement_cells import (
        fixed_output_transport_cell,
    )
    from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
        _attempt_commit_one,
    )

    committed_occupied: frozenset[Coord] = frozenset()
    committed_route_cells: frozenset[Coord] = frozenset()
    committed_fot: frozenset[Coord] = frozenset()
    rows: list[tuple[CommitRouteReservationSnapshot, Fl06QuestionReport]] = []

    for candidate_id in commit_order:
        candidate = candidates_by_id.get(candidate_id)
        if candidate is None:
            continue
        snap = snapshot_commit_reservation(
            candidate,
            skeleton=skeleton,
            inp=inp,
            goals=goals,
            committed_occupied=committed_occupied,
            committed_route_cells=committed_route_cells,
            committed_fixed_output_transport_cells=committed_fot,
            route_probe_start_policy=route_probe_start_policy,
        )
        rows.append((snap, build_fl06_question_report(snap)))
        outcome = _attempt_commit_one(
            candidate,
            skeleton=skeleton,
            inp=inp,
            goals=goals,
            committed_occupied=committed_occupied,
            committed_route_cells=committed_route_cells,
            committed_fixed_output_transport_cells=committed_fot,
            route_probe_start_policy=route_probe_start_policy,
        )
        if not outcome.committed:
            continue
        committed_occupied = frozenset(committed_occupied | candidate.occupied_cells)
        committed_fot = frozenset(
            committed_fot | {fixed_output_transport_cell(candidate)}
        )
        committed_route_cells = frozenset(committed_route_cells | outcome.route_cells)

    return rows


def snapshot_commit_reservation(
    candidate: BundleCandidate,
    *,
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    goals: frozenset[Coord],
    committed_occupied: frozenset[Coord],
    committed_route_cells: frozenset[Coord],
    committed_fixed_output_transport_cells: frozenset[Coord],
    route_probe_start_policy: RouteProbeStartPolicy,
) -> CommitRouteReservationSnapshot:
    current_domain = _rebuild_domain(
        skeleton,
        inp,
        committed_occupied=committed_occupied,
        committed_route_cells=committed_route_cells,
    )
    probe_start = resolve_route_probe_start(
        anchor_coord=candidate.anchor_coord,
        output_stub=candidate.output_stub,
        domain=current_domain,
        policy=route_probe_start_policy,
    )
    path: tuple[Coord, ...] = ()
    route_cells: frozenset[Coord] = frozenset()
    if probe_start is not None:
        probe = probe_route(current_domain, probe_start, goals)
        path = probe.path
        route_cells = _route_cells_from_path(path, candidate.occupied_cells)
    outcome = _attempt_commit_one(
        candidate,
        skeleton=skeleton,
        inp=inp,
        goals=goals,
        committed_occupied=committed_occupied,
        committed_route_cells=committed_route_cells,
        committed_fixed_output_transport_cells=committed_fixed_output_transport_cells,
        route_probe_start_policy=route_probe_start_policy,
    )
    stub = candidate.output_stub
    return CommitRouteReservationSnapshot(
        candidate_id=candidate.candidate_id,
        output_stub=stub,
        probe_start=probe_start,
        probe_start_is_output_stub=probe_start == stub,
        route_probe_start_policy=route_probe_start_policy,
        path=path,
        route_cells=route_cells,
        stub_in_path=stub in path,
        stub_in_route_cells=stub in route_cells,
        attempt_committed=outcome.committed,
    )


__all__ = [
    "CommitRouteReservationSnapshot",
    "Fl06QuestionReport",
    "PreliminaryFl06Cause",
    "build_fl06_question_report",
    "classify_preliminary_outcome",
    "replay_fl06_diagnostics_for_commit_order",
    "snapshot_commit_reservation",
]
