"""Incremental commit with commit-time re-probe (RTTP Layer 4, PR-5)."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from enum import StrEnum

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import cardinal_unit_vector
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    BundleCandidate,
    RouteProbeStartPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.placement_cells import (
    fixed_output_transport_cell,
)
from django_apps.asteroid_lab.optimization.commit.route_path_evidence import (
    build_route_path_evidence,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.routing.lift_lane_domain import (
    RouteCellDomain,
    build_route_domain_from_skeleton,
)
from django_apps.asteroid_lab.optimization.routing.route_goals import (
    probe_goal_coords,
    probe_goal_priorities,
)
from django_apps.asteroid_lab.optimization.routing.route_probe import RouteProbeResult, probe_route
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
    OUTPUT_STUB_NOT_RESERVED = "output_stub_not_reserved"
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
    commit_route_evidence: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True, slots=True)
class CommitAttemptOutcome:
    """Single candidate commit attempt (probe + post-probe checks)."""

    committed: bool
    conflict: CommitConflict | None = None
    route_cells: frozenset[Coord] = frozenset()
    route_probe: RouteProbeResult | None = None


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
        step_costs=base.step_costs,
    )


def _route_cells_from_path(
    path: tuple[Coord, ...],
    occupied: frozenset[Coord],
) -> frozenset[Coord]:
    return frozenset(cell for cell in path if cell not in occupied)


def _augment_route_cells_with_output_spine(
    candidate: BundleCandidate,
    route_cells: frozenset[Coord],
    domain: RouteCellDomain,
    *,
    committed_route_cells: frozenset[Coord] = frozenset(),
    shareable_trunk_cells: frozenset[Coord] = frozenset(),
    max_steps: int = 128,
) -> frozenset[Coord]:
    """Reserve belt cells from FOT through stub toward trunk when probe path is degenerate."""

    unit = cardinal_unit_vector(CardinalDirection(candidate.output_dir))
    stub = candidate.output_stub
    fot = fixed_output_transport_cell(candidate)
    spine: set[Coord] = set(route_cells)
    trunk_shareable = shareable_trunk_cells or domain.trunk_mask_cells

    def _may_traverse_toward_trunk(cell: Coord) -> bool:
        if cell in candidate.occupied_cells or cell in domain.blocked_cells:
            return False
        if cell in committed_route_cells and cell not in trunk_shareable:
            return False
        return cell in domain.traversable_cells or cell in domain.trunk_mask_cells

    cur = stub
    while cur != fot and len(spine) < max_steps:
        prev = (cur[0] - unit[0], cur[1] - unit[1])
        if not _may_traverse_toward_trunk(prev):
            break
        spine.add(prev)
        cur = prev

    cur = stub
    for _ in range(max_steps):
        nxt = (cur[0] + unit[0], cur[1] + unit[1])
        if not _may_traverse_toward_trunk(nxt):
            break
        spine.add(nxt)
        if nxt in trunk_shareable:
            break
        cur = nxt

    return frozenset(spine)


def _private_route_cell_overlap(
    route_cells: frozenset[Coord],
    committed_route_cells: frozenset[Coord],
    *,
    shareable_trunk_cells: frozenset[Coord],
) -> frozenset[Coord]:
    """Cells where a new route collides with prior reservations outside shared trunk."""

    overlap = route_cells & committed_route_cells
    return frozenset(cell for cell in overlap if cell not in shareable_trunk_cells)


def _route_cells_with_required_output_stub(
    candidate: BundleCandidate,
    route_cells: frozenset[Coord],
    domain: RouteCellDomain,
    inp: OptimizationInput,
) -> frozenset[Coord] | None:
    """Ensure committed route reservation includes output_stub when routes are reserved (FL-06).

    When probe uses platform/anchor fallback, ``probe.path`` may omit ``output_stub`` even though
    validation requires stub membership in ``reserved_route_cells``. Include stub when it is not
    equipment-occupied; reject commit when stub lies on occupied equipment only.

    ``domain.blocked_cells`` blocks route *probe* traversal, not belt reservation at the miner
    output face (often outside ``traversable_cells`` for OUTWARD_FROM_RIM FOT).
    """

    stub = candidate.output_stub
    if stub in candidate.occupied_cells:
        return None
    fot = fixed_output_transport_cell(candidate)
    if stub in domain.blocked_cells:
        if fot in inp.mineable_cells:
            return None
        if not route_cells:
            return frozenset({stub})
        if stub in route_cells:
            return route_cells
        return frozenset({stub}) | route_cells
    if not route_cells:
        return frozenset({stub})
    if stub in route_cells:
        return route_cells
    return frozenset({stub}) | route_cells


def _attempt_commit_one(
    candidate: BundleCandidate,
    *,
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    goals: frozenset[Coord],
    goal_priorities: dict[Coord, int],
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
        goal_priority=goal_priorities,
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
    route_cells = _augment_route_cells_with_output_spine(
        candidate,
        route_cells,
        current_domain,
        committed_route_cells=committed_route_cells,
        shareable_trunk_cells=skeleton.trunk_mask_cells,
    )
    merged_route_cells = _route_cells_with_required_output_stub(
        candidate,
        route_cells,
        current_domain,
        inp,
    )
    if merged_route_cells is None:
        return CommitAttemptOutcome(
            committed=False,
            conflict=CommitConflict(
                candidate_id=candidate.candidate_id,
                reason=CommitConflictReason.OUTPUT_STUB_NOT_RESERVED,
            ),
        )
    route_cells = merged_route_cells
    private_overlap = _private_route_cell_overlap(
        route_cells,
        committed_route_cells,
        shareable_trunk_cells=skeleton.trunk_mask_cells,
    )
    if private_overlap:
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
    return CommitAttemptOutcome(
        committed=True,
        route_cells=route_cells,
        route_probe=probe,
    )


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
    goal_priorities = probe_goal_priorities(inp)
    committed_ids: list[str] = []
    conflicts: list[CommitConflict] = []
    evidence_rows: list[dict[str, object]] = []
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
            goal_priorities=goal_priorities,
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
        if outcome.route_probe is not None:
            evidence_rows.append(
                build_route_path_evidence(
                    candidate_id=candidate_id,
                    probe=outcome.route_probe,
                )
            )
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
        commit_route_evidence=tuple(evidence_rows),
    )


__all__ = [
    "CommitAttemptOutcome",
    "CommitConflict",
    "CommitConflictReason",
    "CommitDomainState",
    "CommitResult",
    "_attempt_commit_one",
    "_private_route_cell_overlap",
    "incremental_commit",
    "initial_commit_domain",
]
