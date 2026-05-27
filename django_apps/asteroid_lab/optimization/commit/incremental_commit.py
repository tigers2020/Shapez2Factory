"""Incremental commit with commit-time re-probe (RTTP Layer 4, PR-5)."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import cardinal_unit_vector
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.contracts.exterior_lane_capacity import (
    ExteriorLaneActivationEvidence,
    ExteriorLaneAssignmentState,
    ExteriorLaneCapacityPlan,
    ExteriorLaneRouteEvidence,
    ExteriorLaneTrunkState,
)
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
    shareable_trunk_cells_for_transport,
    update_trunk_state_after_commit,
)
from django_apps.asteroid_lab.optimization.commit.reservation_overlap_policy import (
    compute_elcp_reservation_candidate_cells,
)
from django_apps.asteroid_lab.optimization.commit.route_path_evidence import (
    build_route_path_evidence,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput, TransportKind
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
    exterior_lane_assignments: tuple[dict[str, object], ...] = ()
    exterior_lane_assignment_state: tuple[ExteriorLaneAssignmentState, ...] = ()
    lane_capacity_shortfall_count: int = 0
    route_feasible_shortfall_count: int = 0
    exterior_lane_trunk_states: tuple[ExteriorLaneTrunkState, ...] = ()
    exterior_lane_route_evidence: tuple[ExteriorLaneRouteEvidence, ...] = ()
    exterior_lane_activations: tuple[ExteriorLaneActivationEvidence, ...] = ()


@dataclass(frozen=True, slots=True)
class CommitAttemptOutcome:
    """Single candidate commit attempt (probe + post-probe checks)."""

    committed: bool
    conflict: CommitConflict | None = None
    route_cells: frozenset[Coord] = frozenset()
    route_probe: RouteProbeResult | None = None
    committed_route_delta: frozenset[Coord] = frozenset()


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
    shareable_trunk_cells: frozenset[Coord] | None = None,
    max_steps: int = 128,
) -> frozenset[Coord]:
    """Reserve belt cells from FOT through stub toward trunk when probe path is degenerate."""

    unit = cardinal_unit_vector(CardinalDirection(candidate.output_dir))
    stub = candidate.output_stub
    fot = fixed_output_transport_cell(candidate)
    spine: set[Coord] = set(route_cells)
    trunk_shareable = (
        domain.trunk_mask_cells if shareable_trunk_cells is None else shareable_trunk_cells
    )

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


def _resource_kind_for_transport(transport_kind: TransportKind) -> str:
    if transport_kind is TransportKind.FLUID_PIPE:
        return "fluid"
    return "shape"


def _candidate_throughput_per_min(
    candidate: BundleCandidate,
    *,
    resource_kind: str,
) -> Decimal:
    from django_apps.game_data.services.mining_extraction_rules import (
        get_active_rule,
        output_per_min,
    )

    rule = get_active_rule(resource_kind)
    return output_per_min(rule, candidate.throughput_factor)


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
    precomputed_route_cells: frozenset[Coord] | None = None,
    precomputed_probe: RouteProbeResult | None = None,
    shareable_trunk_cells: frozenset[Coord] | None = None,
    overlap_reservation_cells: frozenset[Coord] | None = None,
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
    resolved_shareable = (
        frozenset(skeleton.trunk_mask_cells)
        if shareable_trunk_cells is None
        else shareable_trunk_cells
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
    if precomputed_route_cells is not None:
        probe = precomputed_probe
        if probe is None or not probe.reachable:
            return CommitAttemptOutcome(
                committed=False,
                conflict=CommitConflict(
                    candidate_id=candidate.candidate_id,
                    reason=CommitConflictReason.REPROBE_FAILED,
                ),
            )
        route_cells = frozenset(
            c for c in precomputed_route_cells if c not in candidate.occupied_cells
        )
    else:
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
        shareable_trunk_cells=resolved_shareable,
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
    cells_for_overlap = (
        overlap_reservation_cells if overlap_reservation_cells is not None else route_cells
    )
    private_overlap = _private_route_cell_overlap(
        cells_for_overlap,
        committed_route_cells,
        shareable_trunk_cells=resolved_shareable,
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
    committed_delta = (
        overlap_reservation_cells if overlap_reservation_cells is not None else route_cells
    )
    return CommitAttemptOutcome(
        committed=True,
        route_cells=route_cells,
        route_probe=probe,
        committed_route_delta=committed_delta,
    )


def _reorder_elcp_trunk_states(
    plan: ExteriorLaneCapacityPlan,
    by_lane_id: dict[str, ExteriorLaneTrunkState],
) -> tuple[ExteriorLaneTrunkState, ...]:
    return tuple(by_lane_id[lane.lane_id] for lane in plan.lanes)


def incremental_commit(
    genome: PlacementGenome,
    candidates_by_id: dict[str, BundleCandidate],
    inp: OptimizationInput,
    skeleton: RttpSkeleton,
    *,
    domain: CommitDomainState,
    route_probe_start_policy: RouteProbeStartPolicy = (RouteProbeStartPolicy.OUTPUT_STUB_ONLY),
    exterior_lane_plan: ExteriorLaneCapacityPlan | None = None,
    resource_kind: str | None = None,
) -> CommitResult:
    """Commit candidates in genome order; re-probe latest domain before each confirm."""

    use_elcp = exterior_lane_plan is not None and len(exterior_lane_plan.lanes) > 0
    goals = probe_goal_coords(inp, skeleton)
    goal_priorities = probe_goal_priorities(inp)
    committed_ids: list[str] = []
    conflicts: list[CommitConflict] = []
    evidence_rows: list[dict[str, object]] = []
    lane_assignment_rows: list[dict[str, object]] = []
    committed_occupied = domain.committed_occupied
    committed_route_cells = domain.committed_route_cells
    committed_fixed_output_transport_cells = domain.committed_fixed_output_transport_cells
    trunk_mask_cells = domain.trunk_mask_cells
    domain_version = domain.version
    assignment_state = (
        initial_assignment_state(exterior_lane_plan)
        if use_elcp and exterior_lane_plan is not None
        else ()
    )
    resolved_resource_kind = resource_kind or _resource_kind_for_transport(inp.transport_kind)
    lane_capacity_shortfall_count = 0
    route_feasible_shortfall_count = 0
    max_expansions = _COMMIT_PROBE_MAX_EXPANSIONS
    trunk_states_elcp: tuple[ExteriorLaneTrunkState, ...] = ()
    elcp_route_evidence_rows: list[ExteriorLaneRouteEvidence] = []
    elcp_activation_rows: list[ExteriorLaneActivationEvidence] = []
    if use_elcp and exterior_lane_plan is not None:
        trunk_states_elcp = initial_trunk_states(exterior_lane_plan)

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

        commit_goals = goals
        pending_lane_id: str | None = None
        pending_throughput = Decimal("0")
        pending_assignment_row: dict[str, object] | None = None
        precomputed_route: frozenset[Coord] | None = None
        precomputed_probe: RouteProbeResult | None = None
        lane_shareable: frozenset[Coord] | None = None
        elcp_overlap_reservation_cells: frozenset[Coord] | None = None
        tm_branch: tuple[Coord, ...] = ()
        tm_reused: tuple[Coord, ...] = ()
        tm_new_trunk: tuple[Coord, ...] = ()
        pending_fill_trunk_states: tuple[ExteriorLaneTrunkState, ...] | None = None
        pending_fill_activation: ExteriorLaneActivationEvidence | None = None
        pending_connector_coord: Coord | None = None
        pending_reached_trunk_coord: Coord | None = None

        if use_elcp and exterior_lane_plan is not None:
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
                route_feasible_shortfall_count += 1
                conflicts.append(
                    CommitConflict(
                        candidate_id=candidate_id,
                        reason=CommitConflictReason.REPROBE_FAILED,
                    )
                )
                continue
            throughput = _candidate_throughput_per_min(
                candidate,
                resource_kind=resolved_resource_kind,
            )
            fill_first = assign_fill_first_exterior_lane(
                candidate,
                plan=exterior_lane_plan,
                assignment_state=assignment_state,
                trunk_states=trunk_states_elcp,
                domain=current_domain,
                candidate_throughput_per_min=throughput,
                probe_start=probe_start,
                max_expansions=max_expansions,
                trigger_candidate_id=candidate_id,
            )
            if fill_first is None:
                lane_capacity_shortfall_count += 1
                route_feasible_shortfall_count += 1
                conflicts.append(
                    CommitConflict(
                        candidate_id=candidate_id,
                        reason=CommitConflictReason.REPROBE_FAILED,
                    )
                )
                continue
            trunk_row_pre = next(s for s in trunk_states_elcp if s.lane_id == fill_first.lane_id)
            lane_spec = next(
                lane for lane in exterior_lane_plan.lanes if lane.lane_id == fill_first.lane_id
            )
            tm_branch, tm_reused, tm_new_trunk = partition_path_branch_and_trunk(
                path=fill_first.probe.path,
                existing_trunk=trunk_row_pre.trunk_cells,
                connector_coord=lane_spec.connector_goal.coord,
            )
            route_delta = frozenset(tm_branch) | frozenset(tm_new_trunk)
            shareable_at_commit = shareable_trunk_cells_for_transport(
                trunk_states_elcp,
                transport_kind=candidate.transport_kind,
                prospective_new_trunk=frozenset(tm_new_trunk),
            )
            reservation_candidate_cells = compute_elcp_reservation_candidate_cells(
                candidate=candidate,
                inp=inp,
                domain=current_domain,
                branch_cells=tm_branch,
                new_trunk_cells=tm_new_trunk,
                reused_trunk_cells=tm_reused,
                shareable_at_commit=shareable_at_commit,
                committed_route_cells=committed_route_cells,
            )
            if reservation_candidate_cells is None:
                route_feasible_shortfall_count += 1
                conflicts.append(
                    CommitConflict(
                        candidate_id=candidate_id,
                        reason=CommitConflictReason.OUTPUT_STUB_NOT_RESERVED,
                    )
                )
                continue
            lane_shareable = shareable_at_commit
            elcp_overlap_reservation_cells = reservation_candidate_cells
            precomputed_route = route_delta
            precomputed_probe = fill_first.probe
            commit_goals = frozenset({fill_first.connector_coord})
            pending_lane_id = fill_first.lane_id
            pending_throughput = throughput
            pending_assignment_row = {
                "candidate_id": candidate_id,
                "exterior_lane_id": fill_first.lane_id,
                "candidate_throughput_per_min": str(throughput),
                "route_probe_cost": fill_first.route_probe_cost,
                "reached_goal": [
                    int(fill_first.connector_coord[0]),
                    int(fill_first.connector_coord[1]),
                ],
            }
            pending_fill_trunk_states = fill_first.trunk_states
            pending_fill_activation = fill_first.activation
            pending_connector_coord = fill_first.connector_coord
            pending_reached_trunk_coord = fill_first.reached_trunk_coord

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
            precomputed_route_cells=precomputed_route,
            precomputed_probe=precomputed_probe,
            shareable_trunk_cells=lane_shareable,
            overlap_reservation_cells=elcp_overlap_reservation_cells,
        )
        if not outcome.committed:
            if outcome.conflict is not None:
                conflicts.append(outcome.conflict)
                if use_elcp and pending_assignment_row is not None:
                    route_feasible_shortfall_count += 1
            continue

        if use_elcp and pending_assignment_row is not None and pending_lane_id is not None:
            assignment_state = increment_assignment_state(
                assignment_state,
                lane_id=pending_lane_id,
                delta=pending_throughput,
            )
            lane_assignment_rows.append(pending_assignment_row)
            if pending_fill_trunk_states is not None and exterior_lane_plan is not None:
                if pending_fill_activation is not None:
                    elcp_activation_rows.append(pending_fill_activation)
                trunk_states_elcp = pending_fill_trunk_states
                by_lane = {s.lane_id: s for s in trunk_states_elcp}
                updated = update_trunk_state_after_commit(
                    by_lane[pending_lane_id],
                    new_trunk_cells=tm_new_trunk,
                    assigned_delta=pending_throughput,
                )
                by_lane[pending_lane_id] = updated
                trunk_states_elcp = _reorder_elcp_trunk_states(exterior_lane_plan, by_lane)
                elcp_route_evidence_rows.append(
                    ExteriorLaneRouteEvidence(
                        candidate_id=candidate_id,
                        lane_id=pending_lane_id,
                        candidate_throughput_per_min=pending_throughput,
                        branch_cells=tm_branch,
                        reused_trunk_cells=tm_reused,
                        new_trunk_cells=tm_new_trunk,
                        reached_connector_coord=pending_connector_coord,
                        reached_trunk_coord=pending_reached_trunk_coord,
                    )
                )

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
        route_delta_committed = (
            outcome.committed_route_delta if outcome.committed_route_delta else route_cells
        )
        committed_route_cells = frozenset(committed_route_cells | route_delta_committed)
        trunk_mask_cells = frozenset(trunk_mask_cells | route_delta_committed)
        domain_version += 1

    return CommitResult(
        committed_ids=tuple(committed_ids),
        reserved_route_cells=committed_route_cells,
        domain_version=domain_version,
        conflicts=tuple(conflicts),
        commit_route_evidence=tuple(evidence_rows),
        exterior_lane_assignments=tuple(lane_assignment_rows),
        exterior_lane_assignment_state=assignment_state,
        lane_capacity_shortfall_count=lane_capacity_shortfall_count,
        route_feasible_shortfall_count=route_feasible_shortfall_count,
        exterior_lane_trunk_states=trunk_states_elcp,
        exterior_lane_route_evidence=tuple(elcp_route_evidence_rows),
        exterior_lane_activations=tuple(elcp_activation_rows),
    )


__all__ = [
    "CommitAttemptOutcome",
    "CommitConflict",
    "CommitConflictReason",
    "CommitDomainState",
    "CommitResult",
    "_attempt_commit_one",
    "_private_route_cell_overlap",
    "_resource_kind_for_transport",
    "incremental_commit",
    "initial_commit_domain",
]
