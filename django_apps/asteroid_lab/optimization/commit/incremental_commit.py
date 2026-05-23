"""Incremental commit with commit-time re-probe (RTTP Layer 4, PR-5)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.routing.lift_lane_domain import (
    RouteCellDomain,
    build_route_domain_from_skeleton,
)
from django_apps.asteroid_lab.optimization.routing.route_probe import probe_route
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton


class CommitConflictReason(StrEnum):
    INLET_ON_SHARED_TRANSPORT = "inlet_on_shared_transport"
    REPROBE_FAILED = "reprobe_failed"
    OVERLAP = "overlap"
    ROUTE_CELL_CONFLICT = "route_cell_conflict"
    OCCUPIED_CELL_CONFLICT = "occupied_cell_conflict"
    TRANSPORT_KIND_CONFLICT = "transport_kind_conflict"
    HARD_BLOCKED_CONFLICT = "hard_blocked_conflict"
    HARD_PROTECTED_CONFLICT = "hard_protected_conflict"
    CANDIDATE_NOT_FOUND = "candidate_not_found"


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
    trunk_mask_cells: frozenset[Coord]


@dataclass(frozen=True, slots=True)
class CommitResult:
    committed_ids: tuple[str, ...]
    reserved_route_cells: frozenset[Coord]
    domain_version: int
    conflicts: tuple[CommitConflict, ...]


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
        trunk_mask_cells=frozenset(skeleton.trunk_mask_cells),
    )


def _goal_coords(inp: OptimizationInput) -> frozenset[Coord]:
    return frozenset(
        goal.coord
        for goal in inp.route_goals
        if goal.transport_kind is None or goal.transport_kind is inp.transport_kind
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


def incremental_commit(
    genome: PlacementGenome,
    candidates_by_id: dict[str, BundleCandidate],
    inp: OptimizationInput,
    skeleton: RttpSkeleton,
    *,
    domain: CommitDomainState,
) -> CommitResult:
    """Commit candidates in genome order; re-probe latest domain before each confirm."""

    goals = _goal_coords(inp)
    committed_ids: list[str] = []
    conflicts: list[CommitConflict] = []
    committed_occupied = domain.committed_occupied
    committed_route_cells = domain.committed_route_cells
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

        if candidate.transport_kind is not inp.transport_kind:
            conflicts.append(
                CommitConflict(
                    candidate_id=candidate_id,
                    reason=CommitConflictReason.TRANSPORT_KIND_CONFLICT,
                )
            )
            continue

        if candidate.occupied_cells & committed_occupied:
            conflicts.append(
                CommitConflict(
                    candidate_id=candidate_id,
                    reason=CommitConflictReason.OVERLAP,
                )
            )
            continue

        if candidate.output_stub in committed_route_cells:
            conflicts.append(
                CommitConflict(
                    candidate_id=candidate_id,
                    reason=CommitConflictReason.INLET_ON_SHARED_TRANSPORT,
                )
            )
            continue

        current_domain = _rebuild_domain(
            skeleton,
            inp,
            committed_occupied=committed_occupied,
            committed_route_cells=committed_route_cells,
        )
        probe = probe_route(current_domain, candidate.output_stub, goals)
        if not probe.reachable:
            conflicts.append(
                CommitConflict(
                    candidate_id=candidate_id,
                    reason=CommitConflictReason.REPROBE_FAILED,
                )
            )
            continue

        route_cells = _route_cells_from_path(probe.path, candidate.occupied_cells)
        overlap_with_routes = route_cells & committed_route_cells
        if overlap_with_routes:
            conflicts.append(
                CommitConflict(
                    candidate_id=candidate_id,
                    reason=CommitConflictReason.ROUTE_CELL_CONFLICT,
                )
            )
            continue

        overlap_with_occupied = route_cells & committed_occupied
        if overlap_with_occupied:
            conflicts.append(
                CommitConflict(
                    candidate_id=candidate_id,
                    reason=CommitConflictReason.OCCUPIED_CELL_CONFLICT,
                )
            )
            continue

        blocked_hits = route_cells & inp.protected_corridor_cells
        if blocked_hits:
            conflicts.append(
                CommitConflict(
                    candidate_id=candidate_id,
                    reason=CommitConflictReason.HARD_PROTECTED_CONFLICT,
                )
            )
            continue

        committed_ids.append(candidate_id)
        committed_occupied = frozenset(committed_occupied | candidate.occupied_cells)
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
    "CommitConflict",
    "CommitConflictReason",
    "CommitDomainState",
    "CommitResult",
    "incremental_commit",
    "initial_commit_domain",
]
