"""Incremental commit with commit-time re-probe (RTTP Layer 4, PR-5)."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from enum import StrEnum

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    BundleCandidate,
    RouteProbeStartPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.placement_cells import (
    fixed_output_transport_cell,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.routing.lift_lane_domain import (
    RouteCellDomain,
    build_route_domain_from_skeleton,
)
from django_apps.asteroid_lab.optimization.routing.route_goals import probe_goal_coords
from django_apps.asteroid_lab.optimization.routing.route_probe import probe_route
from django_apps.asteroid_lab.optimization.routing.route_probe_start import (
    resolve_route_probe_start,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton

_COMMIT_PROBE_MAX_EXPANSIONS: int = int(
    inspect.signature(probe_route).parameters["max_expansions"].default
)


class CommitConflictReason(StrEnum):
    INLET_ON_SHARED_TRANSPORT = "inlet_on_shared_transport"
    REPROBE_FAILED = "reprobe_failed"
    OVERLAP = "overlap"
    ROUTE_CELL_CONFLICT = "route_cell_conflict"
    OCCUPIED_CELL_CONFLICT = "occupied_cell_conflict"
    # Cross-commit FOT reservation (INV-COMMIT-FOT-01/02); not CandidateRejectReason.
    FIXED_OUTPUT_TRANSPORT_CONFLICT = "fixed_output_transport_conflict"
    FIXED_OUTPUT_TRANSPORT_INSIDE_MINEABLE = "fixed_output_transport_inside_mineable"
    TRANSPORT_KIND_CONFLICT = "transport_kind_conflict"
    HARD_PROTECTED_CONFLICT = "hard_protected_conflict"
    CANDIDATE_NOT_FOUND = "candidate_not_found"
    MACRO_CHILD_CONFLICT = "macro_child_conflict"


@dataclass(frozen=True, slots=True)
class CommitConflict:
    candidate_id: str
    reason: CommitConflictReason


@dataclass(frozen=True, slots=True)
class CommitDomainState:
    """Mutable-through-replacement commit-time route domain snapshot."""

    domain: RouteCellDomain
    version: int
    committed_route_cells: frozenset[Coord]
    committed_occupied: frozenset[Coord]
    committed_fixed_output_transport_cells: frozenset[Coord]
    trunk_mask_cells: frozenset[Coord]


@dataclass(frozen=True, slots=True)
class CommitResult:
    committed_ids: tuple[str, ...]
    reserved_route_cells: frozenset[Coord]
    domain_version: int
    conflicts: tuple[CommitConflict, ...]


@dataclass(frozen=True, slots=True)
class CommitAttemptOutcome:
    """Single candidate commit attempt (probe + post-probe checks)."""

    committed: bool
    conflict: CommitConflict | None = None
    route_cells: frozenset[Coord] = frozenset()


def initial_commit_domain(
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
) -> CommitDomainState:
    domain = build_route_domain_from_skeleton(skeleton, inp)
    return CommitDomainState(
        domain=domain,
        version=0,
        committed_route_cells=frozenset(),
        committed_occupied=frozenset(),
        committed_fixed_output_transport_cells=frozenset(),
        trunk_mask_cells=frozenset(skeleton.trunk_mask_cells),
    )


def _rebuild_domain(
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    *,
    committed_occupied: frozenset[Coord],
    committed_route_cells: frozenset[Coord],
) -> RouteCellDomain:
    base = build_route_domain_from_skeleton(skeleton, inp)
    trunk_mask = base.trunk_mask_cells | committed_route_cells
    traversable = base.traversable_cells | committed_route_cells
    blocked = frozenset(base.blocked_cells | committed_occupied)
    return RouteCellDomain(
        blocked_cells=blocked,
        trunk_mask_cells=trunk_mask,
        lift_edges=base.lift_edges,
        traversable_cells=traversable,
    )


def _route_cells_from_path(
    path: tuple[Coord, ...],
    occupied: frozenset[Coord],
) -> frozenset[Coord]:
    return frozenset(cell for cell in path if cell not in occupied)


def _attempt_commit_one(
    candidate: BundleCandidate,
    *,
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    goals: frozenset[Coord],
    committed_occupied: frozenset[Coord],
    committed_route_cells: frozenset[Coord],
    committed_fixed_output_transport_cells: frozenset[Coord],
    route_probe_start_policy: RouteProbeStartPolicy,
    max_expansions: int | None = None,
) -> CommitAttemptOutcome:
    if candidate.transport_kind is not inp.transport_kind:
        return CommitAttemptOutcome(
            committed=False,
            conflict=CommitConflict(
                candidate_id=candidate.candidate_id,
                reason=CommitConflictReason.TRANSPORT_KIND_CONFLICT,
            ),
        )
    if candidate.occupied_cells & committed_occupied:
        return CommitAttemptOutcome(
            committed=False,
            conflict=CommitConflict(
                candidate_id=candidate.candidate_id,
                reason=CommitConflictReason.OVERLAP,
            ),
        )
    if candidate.output_stub in committed_route_cells:
        return CommitAttemptOutcome(
            committed=False,
            conflict=CommitConflict(
                candidate_id=candidate.candidate_id,
                reason=CommitConflictReason.INLET_ON_SHARED_TRANSPORT,
            ),
        )
    fot_cell = fixed_output_transport_cell(candidate)
    if candidate.occupied_cells & committed_fixed_output_transport_cells:
        return CommitAttemptOutcome(
            committed=False,
            conflict=CommitConflict(
                candidate_id=candidate.candidate_id,
                reason=CommitConflictReason.FIXED_OUTPUT_TRANSPORT_CONFLICT,
            ),
        )
    if fot_cell in committed_occupied:
        return CommitAttemptOutcome(
            committed=False,
            conflict=CommitConflict(
                candidate_id=candidate.candidate_id,
                reason=CommitConflictReason.FIXED_OUTPUT_TRANSPORT_CONFLICT,
            ),
        )
    if fot_cell in inp.mineable_cells:
        return CommitAttemptOutcome(
            committed=False,
            conflict=CommitConflict(
                candidate_id=candidate.candidate_id,
                reason=CommitConflictReason.FIXED_OUTPUT_TRANSPORT_INSIDE_MINEABLE,
            ),
        )
    resolved_expansions = _COMMIT_PROBE_MAX_EXPANSIONS if max_expansions is None else max_expansions
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
    if probe_start is None:
        return CommitAttemptOutcome(
            committed=False,
            conflict=CommitConflict(
                candidate_id=candidate.candidate_id,
                reason=CommitConflictReason.REPROBE_FAILED,
            ),
        )
    probe = probe_route(
        current_domain,
        probe_start,
        goals,
        max_expansions=resolved_expansions,
    )
    if not probe.reachable:
        return CommitAttemptOutcome(
            committed=False,
            conflict=CommitConflict(
                candidate_id=candidate.candidate_id,
                reason=CommitConflictReason.REPROBE_FAILED,
            ),
        )
    route_cells = _route_cells_from_path(probe.path, candidate.occupied_cells)
    if route_cells & committed_route_cells:
        return CommitAttemptOutcome(
            committed=False,
            conflict=CommitConflict(
                candidate_id=candidate.candidate_id,
                reason=CommitConflictReason.ROUTE_CELL_CONFLICT,
            ),
        )
    if route_cells & committed_occupied:
        return CommitAttemptOutcome(
            committed=False,
            conflict=CommitConflict(
                candidate_id=candidate.candidate_id,
                reason=CommitConflictReason.OCCUPIED_CELL_CONFLICT,
            ),
        )
    if route_cells & inp.protected_corridor_cells:
        return CommitAttemptOutcome(
            committed=False,
            conflict=CommitConflict(
                candidate_id=candidate.candidate_id,
                reason=CommitConflictReason.HARD_PROTECTED_CONFLICT,
            ),
        )
    return CommitAttemptOutcome(committed=True, route_cells=route_cells)


def incremental_commit(
    genome: PlacementGenome,
    candidates_by_id: dict[str, BundleCandidate],
    inp: OptimizationInput,
    skeleton: RttpSkeleton,
    *,
    domain: CommitDomainState,
    route_probe_start_policy: RouteProbeStartPolicy = (RouteProbeStartPolicy.OUTPUT_STUB_ONLY),
) -> CommitResult:
    """Commit candidates in genome order; re-probe latest domain before each confirm."""

    goals = probe_goal_coords(inp, skeleton)
    committed_ids: list[str] = []
    conflicts: list[CommitConflict] = []
    committed_occupied = domain.committed_occupied
    committed_route_cells = domain.committed_route_cells
    committed_fixed_output_transport_cells = domain.committed_fixed_output_transport_cells
    trunk_mask_cells = domain.trunk_mask_cells
    domain_version = domain.version

    for candidate_id in genome.commit_order:
        candidate = candidates_by_id.get(candidate_id)
        if candidate is None:
            conflicts.append(
                CommitConflict(
                    candidate_id=candidate_id,
                    reason=CommitConflictReason.CANDIDATE_NOT_FOUND,
                )
            )
            continue

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
        if not outcome.committed:
            if outcome.conflict is not None:
                conflicts.append(outcome.conflict)
            continue

        route_cells = outcome.route_cells
        committed_ids.append(candidate_id)
        committed_occupied = frozenset(committed_occupied | candidate.occupied_cells)
        committed_fixed_output_transport_cells = frozenset(
            committed_fixed_output_transport_cells | {fixed_output_transport_cell(candidate)}
        )
        committed_route_cells = frozenset(committed_route_cells | route_cells)
        trunk_mask_cells = frozenset(trunk_mask_cells | route_cells)
        domain_version += 1

    return CommitResult(
        committed_ids=tuple(committed_ids),
        reserved_route_cells=committed_route_cells,
        domain_version=domain_version,
        conflicts=tuple(conflicts),
    )


__all__ = [
    "CommitAttemptOutcome",
    "CommitConflict",
    "CommitConflictReason",
    "CommitDomainState",
    "CommitResult",
    "_attempt_commit_one",
    "incremental_commit",
    "initial_commit_domain",
]
