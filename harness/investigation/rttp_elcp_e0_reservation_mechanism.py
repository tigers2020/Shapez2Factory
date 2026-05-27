"""P1-ELCP-RF-E0: post-probe reservation mechanism forensics (not solver input).

Replay signals use production commit helpers; mechanism attribution is non-causal
evidence per spec §2.4.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any
from unittest.mock import patch

from django_apps.asteroid_lab.contracts.exterior_lane_capacity import ExteriorLaneCapacityPlan
from django_apps.asteroid_lab.contracts.selection_mode import SelectionMode
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    BundleCandidate,
    ExtractorPlacementPolicy,
    FixedOutputTransportPolicy,
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
    CommitConflictReason,
    CommitResult,
    _attempt_commit_one,
    _augment_route_cells_with_output_spine,
    _candidate_throughput_per_min,
    _private_route_cell_overlap,
    _rebuild_domain,
    _reorder_elcp_trunk_states,
    _route_cells_from_path,
    _route_cells_with_required_output_stub,
    incremental_commit,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
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
from harness.investigation.rttp_elcp_c0_dual_mode import (
    build_gate_a_rf1_inputs,
    resolve_git_sha,
)
from harness.investigation.rttp_elcp_d0_stale_attribution import (
    RESERVATION_CONFLICT_REASONS,
    MirrorDomainSnapshot,
    _at_attempt_by_index,
    _snapshot_before_commit_index,
    diff_blocking_cells,
)
from harness.investigation.rttp_elcp_reprobe_forensics import (
    ElcpAttemptLedgerRow,
    ElcpProbeFailureClass,
    assert_mirror_parity,
    build_elcp_primary_mirror_ledger,
    classify_probe_failure,
)

_SAMPLE_MAX = 10
_E0_VERDICT_DOMINANCE = 0.50
_E0_SPLIT_FAMILY_MIN = 0.35
_E0_UNATTRIBUTED_MAX = 0.10


class ElcpE0MechanismClass(StrEnum):
    PRIVATE_ROUTE_OVERLAP = "private_route_overlap"
    SHAREABLE_TRUNK_UNDERCOVERAGE = "shareable_trunk_undercoverage"
    SPINE_AUGMENTATION_CONFLICT = "spine_augmentation_conflict"
    PROBE_VS_MERGED_ROUTE_MISMATCH = "probe_vs_merged_route_mismatch"
    UNATTRIBUTED_ROUTE_CELL_MECHANISM = "unattributed_route_cell_mechanism"
    INLET_STUB_ON_COMMITTED_ROUTE = "inlet_stub_on_committed_route"
    INLET_STUB_ADJACENT_SHARED_TRANSPORT = "inlet_stub_adjacent_shared_transport"
    UNATTRIBUTED_INLET_MECHANISM = "unattributed_inlet_mechanism"
    UNATTRIBUTED_RESERVATION_MECHANISM = "unattributed_reservation_mechanism"


class ElcpE0Verdict(StrEnum):
    ROUTE_CELL_RESERVATION_CONFLICT_DOMINANT = "route_cell_reservation_conflict_dominant"
    INLET_SHARED_TRANSPORT_POLICY_DOMINANT = "inlet_shared_transport_policy_dominant"
    SPLIT_RESERVATION_POLICY_NEEDS_DECOMPOSITION = "split_reservation_policy_needs_decomposition"
    INCONCLUSIVE_NEEDS_TELEMETRY = "inconclusive_needs_telemetry"


class BSpecNominationWithheldReason(StrEnum):
    NONE = "none"
    VERDICT_NOT_DOMINANT = "verdict_not_dominant"
    APPENDIX_VETO = "appendix_veto"
    OWNER_SPLIT = "owner_split"
    INCONCLUSIVE = "inconclusive"


_ROUTE_CELL_MECHANISMS: frozenset[ElcpE0MechanismClass] = frozenset(
    {
        ElcpE0MechanismClass.PRIVATE_ROUTE_OVERLAP,
        ElcpE0MechanismClass.SHAREABLE_TRUNK_UNDERCOVERAGE,
        ElcpE0MechanismClass.SPINE_AUGMENTATION_CONFLICT,
        ElcpE0MechanismClass.PROBE_VS_MERGED_ROUTE_MISMATCH,
        ElcpE0MechanismClass.UNATTRIBUTED_ROUTE_CELL_MECHANISM,
    }
)

_INLET_MECHANISMS: frozenset[ElcpE0MechanismClass] = frozenset(
    {
        ElcpE0MechanismClass.INLET_STUB_ON_COMMITTED_ROUTE,
        ElcpE0MechanismClass.INLET_STUB_ADJACENT_SHARED_TRANSPORT,
        ElcpE0MechanismClass.UNATTRIBUTED_INLET_MECHANISM,
    }
)

MECHANISM_OWNER_MODULE: dict[ElcpE0MechanismClass, str] = {
    ElcpE0MechanismClass.PRIVATE_ROUTE_OVERLAP: ("incremental_commit._private_route_cell_overlap"),
    ElcpE0MechanismClass.SHAREABLE_TRUNK_UNDERCOVERAGE: (
        "exterior_lane_trunk.shareable_trunk_cells"
    ),
    ElcpE0MechanismClass.SPINE_AUGMENTATION_CONFLICT: (
        "incremental_commit._augment_route_cells_with_output_spine"
    ),
    ElcpE0MechanismClass.PROBE_VS_MERGED_ROUTE_MISMATCH: (
        "incremental_commit._route_cells_from_path+_route_cells_with_required_output_stub"
    ),
    ElcpE0MechanismClass.INLET_STUB_ON_COMMITTED_ROUTE: (
        "incremental_commit._attempt_commit_one.inlet_guard"
    ),
    ElcpE0MechanismClass.INLET_STUB_ADJACENT_SHARED_TRANSPORT: (
        "incremental_commit.inlet_on_shared_transport_policy"
    ),
    ElcpE0MechanismClass.UNATTRIBUTED_ROUTE_CELL_MECHANISM: "unattributed",
    ElcpE0MechanismClass.UNATTRIBUTED_INLET_MECHANISM: "unattributed",
    ElcpE0MechanismClass.UNATTRIBUTED_RESERVATION_MECHANISM: "unattributed",
}


def is_unattributed_mechanism_class(cls: ElcpE0MechanismClass) -> bool:
    return cls.value.startswith("unattributed_")


def is_route_cell_mechanism_family(cls: ElcpE0MechanismClass) -> bool:
    return cls in _ROUTE_CELL_MECHANISMS


def is_inlet_mechanism_family(cls: ElcpE0MechanismClass) -> bool:
    return cls in _INLET_MECHANISMS


def _bounded_sample(cells: frozenset[Coord]) -> tuple[Coord, ...]:
    return tuple(sorted(cells)[:_SAMPLE_MAX])


def _stub_neighbor_coords(stub: Coord) -> tuple[Coord, ...]:
    x, y = stub
    return ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))


@dataclass(frozen=True, slots=True)
class MechanismReplaySignals:
    private_overlap_cells: frozenset[Coord]
    shareable_trunk_undercoverage_cells: frozenset[Coord]
    spine_augment_cells: frozenset[Coord]
    probe_merged_route_diff_cells: frozenset[Coord]
    output_stub_in_committed_route: bool
    inlet_stub_adjacent_committed_route_cells: frozenset[Coord]


def classify_e0_mechanism(
    *,
    commit_conflict_reason: str | None,
    private_overlap_cells: frozenset[Coord],
    shareable_trunk_undercoverage_cells: frozenset[Coord],
    spine_augment_cells: frozenset[Coord],
    probe_merged_route_diff_cells: frozenset[Coord],
    output_stub_in_committed_route: bool,
    inlet_stub_adjacent_committed_route_cells: frozenset[Coord],
) -> ElcpE0MechanismClass:
    if commit_conflict_reason == CommitConflictReason.ROUTE_CELL_CONFLICT.value:
        if private_overlap_cells:
            return ElcpE0MechanismClass.PRIVATE_ROUTE_OVERLAP
        if shareable_trunk_undercoverage_cells:
            return ElcpE0MechanismClass.SHAREABLE_TRUNK_UNDERCOVERAGE
        if spine_augment_cells:
            return ElcpE0MechanismClass.SPINE_AUGMENTATION_CONFLICT
        if probe_merged_route_diff_cells:
            return ElcpE0MechanismClass.PROBE_VS_MERGED_ROUTE_MISMATCH
        return ElcpE0MechanismClass.UNATTRIBUTED_ROUTE_CELL_MECHANISM

    if commit_conflict_reason == CommitConflictReason.INLET_ON_SHARED_TRANSPORT.value:
        if output_stub_in_committed_route:
            return ElcpE0MechanismClass.INLET_STUB_ON_COMMITTED_ROUTE
        if inlet_stub_adjacent_committed_route_cells:
            return ElcpE0MechanismClass.INLET_STUB_ADJACENT_SHARED_TRANSPORT
        return ElcpE0MechanismClass.UNATTRIBUTED_INLET_MECHANISM

    return ElcpE0MechanismClass.UNATTRIBUTED_RESERVATION_MECHANISM


def compute_e0_verdict(
    mechanism_classes: Sequence[ElcpE0MechanismClass],
    *,
    mirror_parity_ok: bool,
    appendix_veto: bool,
) -> ElcpE0Verdict:
    n = len(mechanism_classes)
    if not mirror_parity_ok or n == 0:
        return ElcpE0Verdict.INCONCLUSIVE_NEEDS_TELEMETRY

    unattributed = sum(1 for c in mechanism_classes if is_unattributed_mechanism_class(c))
    if unattributed / n > _E0_UNATTRIBUTED_MAX:
        return ElcpE0Verdict.INCONCLUSIVE_NEEDS_TELEMETRY

    if appendix_veto:
        return ElcpE0Verdict.SPLIT_RESERVATION_POLICY_NEEDS_DECOMPOSITION

    route_n = sum(1 for c in mechanism_classes if is_route_cell_mechanism_family(c))
    inlet_n = sum(1 for c in mechanism_classes if is_inlet_mechanism_family(c))

    route_ratio = route_n / n
    inlet_ratio = inlet_n / n

    if route_ratio >= _E0_VERDICT_DOMINANCE and route_n > inlet_n:
        return ElcpE0Verdict.ROUTE_CELL_RESERVATION_CONFLICT_DOMINANT
    if inlet_ratio >= _E0_VERDICT_DOMINANCE and inlet_n > route_n:
        return ElcpE0Verdict.INLET_SHARED_TRANSPORT_POLICY_DOMINANT
    if route_ratio >= _E0_VERDICT_DOMINANCE and inlet_ratio >= _E0_VERDICT_DOMINANCE:
        return ElcpE0Verdict.INCONCLUSIVE_NEEDS_TELEMETRY

    if route_ratio >= _E0_SPLIT_FAMILY_MIN and inlet_ratio >= _E0_SPLIT_FAMILY_MIN:
        return ElcpE0Verdict.SPLIT_RESERVATION_POLICY_NEEDS_DECOMPOSITION

    return ElcpE0Verdict.INCONCLUSIVE_NEEDS_TELEMETRY


def evaluate_appendix_veto(
    *,
    primary_route_family_count: int,
    primary_inlet_family_count: int,
    appendix_route_family_count: int,
    appendix_inlet_family_count: int,
) -> bool:
    appendix_total = appendix_route_family_count + appendix_inlet_family_count
    if appendix_total == 0:
        return False

    if primary_route_family_count >= primary_inlet_family_count:
        primary_dominant = "route_cell"
        primary_dominant_count = primary_route_family_count
        opposite_count = appendix_inlet_family_count
    else:
        primary_dominant = "inlet"
        primary_dominant_count = primary_inlet_family_count
        opposite_count = appendix_route_family_count

    _ = primary_dominant
    opposite_ratio = opposite_count / appendix_total
    if opposite_ratio <= _E0_VERDICT_DOMINANCE:
        return False
    return opposite_count >= primary_dominant_count + 1


@dataclass(frozen=True, slots=True)
class BSpecNomination:
    nominated: bool
    title: str | None
    owner_module: str | None
    withheld_reason: BSpecNominationWithheldReason

    def to_dict(self) -> dict[str, Any]:
        return {
            "nominated": self.nominated,
            "title": self.title,
            "owner_module": self.owner_module,
            "withheld_reason": self.withheld_reason.value,
        }


def _dominant_mechanism_class(
    classes: Sequence[ElcpE0MechanismClass],
    *,
    family: frozenset[ElcpE0MechanismClass],
) -> ElcpE0MechanismClass | None:
    filtered = [c for c in classes if c in family and not is_unattributed_mechanism_class(c)]
    if not filtered:
        return None
    counts = Counter(filtered)
    top_class, top_n = counts.most_common(1)[0]
    if top_n / len(classes) >= _E0_VERDICT_DOMINANCE:
        return top_class
    return None


def _shared_owner_in_family(classes: Sequence[ElcpE0MechanismClass]) -> str | None:
    owners = {MECHANISM_OWNER_MODULE[c] for c in classes if not is_unattributed_mechanism_class(c)}
    owners.discard("unattributed")
    if len(owners) == 1:
        return next(iter(owners))
    return None


def evaluate_b_spec_nomination(
    *,
    verdict: ElcpE0Verdict,
    mechanism_classes: Sequence[ElcpE0MechanismClass],
    appendix_veto: bool,
) -> BSpecNomination:
    if appendix_veto:
        return BSpecNomination(
            nominated=False,
            title=None,
            owner_module=None,
            withheld_reason=BSpecNominationWithheldReason.APPENDIX_VETO,
        )

    if verdict in (
        ElcpE0Verdict.SPLIT_RESERVATION_POLICY_NEEDS_DECOMPOSITION,
        ElcpE0Verdict.INCONCLUSIVE_NEEDS_TELEMETRY,
    ):
        return BSpecNomination(
            nominated=False,
            title=None,
            owner_module=None,
            withheld_reason=BSpecNominationWithheldReason.VERDICT_NOT_DOMINANT,
        )

    if verdict is ElcpE0Verdict.ROUTE_CELL_RESERVATION_CONFLICT_DOMINANT:
        family = _ROUTE_CELL_MECHANISMS
        title = "Bounded B-spec: route-cell reservation / shareable trunk / private overlap"
    elif verdict is ElcpE0Verdict.INLET_SHARED_TRANSPORT_POLICY_DOMINANT:
        family = _INLET_MECHANISMS
        title = "Bounded B-spec: inlet_on_shared_transport / stub-vs-shared-route policy"
    else:
        return BSpecNomination(
            nominated=False,
            title=None,
            owner_module=None,
            withheld_reason=BSpecNominationWithheldReason.VERDICT_NOT_DOMINANT,
        )

    family_classes = [c for c in mechanism_classes if c in family]
    dominant_class = _dominant_mechanism_class(mechanism_classes, family=family)
    shared_owner = _shared_owner_in_family(family_classes)

    if dominant_class is not None:
        return BSpecNomination(
            nominated=True,
            title=title,
            owner_module=MECHANISM_OWNER_MODULE[dominant_class],
            withheld_reason=BSpecNominationWithheldReason.NONE,
        )

    if shared_owner is not None:
        return BSpecNomination(
            nominated=True,
            title=title,
            owner_module=shared_owner,
            withheld_reason=BSpecNominationWithheldReason.NONE,
        )

    return BSpecNomination(
        nominated=False,
        title=title,
        owner_module=None,
        withheld_reason=BSpecNominationWithheldReason.OWNER_SPLIT,
    )


def _mechanism_signals_from_route_bundle(
    *,
    candidate: BundleCandidate,
    inp: OptimizationInput,
    committed_route_cells: frozenset[Coord],
    current_domain: object,
    probe: RouteProbeResult,
    precomputed_route: frozenset[Coord],
    lane_shareable: frozenset[Coord],
) -> MechanismReplaySignals:
    stub = candidate.output_stub
    output_stub_in_committed_route = stub in committed_route_cells
    adjacent = frozenset(
        c for c in _stub_neighbor_coords(stub) if c in committed_route_cells and c != stub
    )

    if not probe.reachable:
        return MechanismReplaySignals(
            private_overlap_cells=frozenset(),
            shareable_trunk_undercoverage_cells=frozenset(),
            spine_augment_cells=frozenset(),
            probe_merged_route_diff_cells=frozenset(),
            output_stub_in_committed_route=output_stub_in_committed_route,
            inlet_stub_adjacent_committed_route_cells=adjacent,
        )

    path_cells = _route_cells_from_path(probe.path, candidate.occupied_cells)
    route_cells = frozenset(c for c in precomputed_route if c not in candidate.occupied_cells)
    augmented = _augment_route_cells_with_output_spine(
        candidate,
        route_cells,
        current_domain,
        committed_route_cells=committed_route_cells,
        shareable_trunk_cells=lane_shareable,
    )
    merged = _route_cells_with_required_output_stub(
        candidate,
        augmented,
        current_domain,
        inp,
    )
    if merged is None:
        merged = frozenset()

    private_overlap = _private_route_cell_overlap(
        merged,
        committed_route_cells,
        shareable_trunk_cells=lane_shareable,
    )
    overlap_all = merged & committed_route_cells
    undercoverage = frozenset(
        c for c in overlap_all if c not in lane_shareable and c in current_domain.trunk_mask_cells
    )
    spine_augment = frozenset(augmented - path_cells)
    probe_merged_diff = frozenset((merged - path_cells) | (path_cells - merged))

    return MechanismReplaySignals(
        private_overlap_cells=private_overlap,
        shareable_trunk_undercoverage_cells=undercoverage,
        spine_augment_cells=spine_augment,
        probe_merged_route_diff_cells=probe_merged_diff,
        output_stub_in_committed_route=output_stub_in_committed_route,
        inlet_stub_adjacent_committed_route_cells=adjacent,
    )


def build_stale_replay_signal_cache(
    *,
    genome: PlacementGenome,
    candidates_by_id: dict[str, BundleCandidate],
    inp: OptimizationInput,
    skeleton: RttpSkeleton,
    domain: object,
    exterior_lane_plan: ExteriorLaneCapacityPlan,
    route_probe_start_policy: RouteProbeStartPolicy,
    resource_kind: str,
    max_expansions: int | None = None,
) -> dict[tuple[int, str], MechanismReplaySignals]:
    """Mirror walk with commit-order state; cache replay signals for stale failures only."""

    resolved_max = _COMMIT_PROBE_MAX_EXPANSIONS if max_expansions is None else max_expansions
    goals = probe_goal_coords(inp, skeleton)
    goal_priorities = probe_goal_priorities(inp)
    goals_nonempty = len(goals) > 0

    committed_occupied = domain.committed_occupied
    committed_route_cells = domain.committed_route_cells
    committed_fixed_output_transport_cells = domain.committed_fixed_output_transport_cells

    assignment_state = initial_assignment_state(exterior_lane_plan)
    trunk_states_elcp = initial_trunk_states(exterior_lane_plan)
    cache: dict[tuple[int, str], MechanismReplaySignals] = {}

    for commit_index, candidate_id in enumerate(genome.commit_order):
        candidate = candidates_by_id.get(candidate_id)
        if candidate is None:
            continue

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
            continue

        throughput = _candidate_throughput_per_min(candidate, resource_kind=resource_kind)
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
            continue

        trunk_row_pre = next(s for s in trunk_states_elcp if s.lane_id == fill_first.lane_id)
        lane_spec = next(
            lane for lane in exterior_lane_plan.lanes if lane.lane_id == fill_first.lane_id
        )
        tm_branch, _, tm_new_trunk = partition_path_branch_and_trunk(
            path=fill_first.probe.path,
            existing_trunk=trunk_row_pre.trunk_cells,
            connector_coord=lane_spec.connector_goal.coord,
        )
        precomputed_route = frozenset(tm_branch) | frozenset(tm_new_trunk)
        lane_shareable = frozenset(trunk_row_pre.trunk_cells) | frozenset(tm_new_trunk)
        commit_goals = frozenset({fill_first.connector_coord})

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
            precomputed_probe=fill_first.probe,
            shareable_trunk_cells=lane_shareable,
        )

        if outcome.committed:
            route_cells = outcome.route_cells or frozenset()
            committed_occupied = frozenset(committed_occupied | candidate.occupied_cells)
            committed_fixed_output_transport_cells = frozenset(
                committed_fixed_output_transport_cells | {fixed_output_transport_cell(candidate)}
            )
            committed_route_cells = frozenset(committed_route_cells | route_cells)
            assignment_state = increment_assignment_state(
                assignment_state,
                lane_id=fill_first.lane_id,
                delta=throughput,
            )
            trunk_states_elcp = fill_first.trunk_states
            by_lane = {s.lane_id: s for s in trunk_states_elcp}
            updated = update_trunk_state_after_commit(
                by_lane[fill_first.lane_id],
                new_trunk_cells=tm_new_trunk,
                assigned_delta=throughput,
            )
            by_lane[fill_first.lane_id] = updated
            trunk_states_elcp = _reorder_elcp_trunk_states(exterior_lane_plan, by_lane)
            continue

        failure_class = classify_probe_failure(
            probe_start=probe_start,
            fill_first_ok=True,
            probe=fill_first.probe,
            max_expansions=resolved_max,
            goals_nonempty=goals_nonempty,
            candidate_reachable=candidate.reachable,
            post_probe_committed=False,
            committed_route_cell_count=len(committed_route_cells),
            traversable_cell_count=len(current_domain.traversable_cells),
            tm_new_trunk_len=len(tm_new_trunk),
            trunk_pressure_correlated=len(tm_new_trunk) > 0,
        )
        if failure_class is not ElcpProbeFailureClass.STALE_CANDIDATE_REACHABLE:
            continue

        cache[(commit_index, candidate_id)] = _mechanism_signals_from_route_bundle(
            candidate=candidate,
            inp=inp,
            committed_route_cells=committed_route_cells,
            current_domain=current_domain,
            probe=fill_first.probe,
            precomputed_route=precomputed_route,
            lane_shareable=lane_shareable,
        )

    return cache


@dataclass(frozen=True, slots=True)
class ElcpE0MechanismRow:
    commit_index: int
    candidate_id: str
    probe_failure_class: str
    commit_conflict_reason: str | None
    elcp_e0_mechanism_class: ElcpE0MechanismClass
    mechanism_owner_module: str
    candidate_route_probe_reachable: bool
    commit_probe_reachable: bool
    private_overlap_cell_count: int
    private_overlap_sample: tuple[Coord, ...]
    shareable_trunk_undercoverage_count: int
    spine_augment_cell_count: int
    probe_merged_route_diff_count: int
    output_stub_in_committed_route: bool
    probe_expanded_nodes: int | None
    probe_max_expansions: int
    new_blocking_cells_since_last_commit_count: int
    assigned_lane_id: str | None
    git_sha: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "commit_index": self.commit_index,
            "candidate_id": self.candidate_id,
            "probe_failure_class": self.probe_failure_class,
            "commit_conflict_reason": self.commit_conflict_reason,
            "elcp_e0_mechanism_class": self.elcp_e0_mechanism_class.value,
            "mechanism_owner_module": self.mechanism_owner_module,
            "candidate_route_probe_reachable": self.candidate_route_probe_reachable,
            "commit_probe_reachable": self.commit_probe_reachable,
            "private_overlap_cell_count": self.private_overlap_cell_count,
            "private_overlap_sample": [list(c) for c in self.private_overlap_sample],
            "shareable_trunk_undercoverage_count": self.shareable_trunk_undercoverage_count,
            "spine_augment_cell_count": self.spine_augment_cell_count,
            "probe_merged_route_diff_count": self.probe_merged_route_diff_count,
            "output_stub_in_committed_route": self.output_stub_in_committed_route,
            "probe_expanded_nodes": self.probe_expanded_nodes,
            "probe_max_expansions": self.probe_max_expansions,
            "new_blocking_cells_since_last_commit_count": (
                self.new_blocking_cells_since_last_commit_count
            ),
            "assigned_lane_id": self.assigned_lane_id,
            "git_sha": self.git_sha,
        }


@dataclass(frozen=True, slots=True)
class AppendixAggregate:
    total_reservation_class_failed: int
    stale_reservation_class_failed: int
    non_stale_reservation_class_failed: int
    conflict_reason_histogram: dict[str, int]
    route_cell_family_count: int
    inlet_family_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_reservation_class_failed": self.total_reservation_class_failed,
            "stale_reservation_class_failed": self.stale_reservation_class_failed,
            "non_stale_reservation_class_failed": self.non_stale_reservation_class_failed,
            "conflict_reason_histogram": self.conflict_reason_histogram,
            "route_cell_family_count": self.route_cell_family_count,
            "inlet_family_count": self.inlet_family_count,
        }


def _appendix_family_from_conflict(reason: str | None) -> str | None:
    if reason == CommitConflictReason.ROUTE_CELL_CONFLICT.value:
        return "route_cell"
    if reason == CommitConflictReason.INLET_ON_SHARED_TRANSPORT.value:
        return "inlet"
    return None


def build_reservation_class_appendix_aggregate(
    ledger: Sequence[ElcpAttemptLedgerRow],
) -> AppendixAggregate:
    reservation_rows = [
        r for r in ledger if r.commit_conflict_reason in RESERVATION_CONFLICT_REASONS
    ]
    stale_res = [
        r
        for r in reservation_rows
        if r.probe_failure_class is ElcpProbeFailureClass.STALE_CANDIDATE_REACHABLE
    ]
    route_n = 0
    inlet_n = 0
    for row in reservation_rows:
        family = _appendix_family_from_conflict(row.commit_conflict_reason)
        if family == "route_cell":
            route_n += 1
        elif family == "inlet":
            inlet_n += 1

    return AppendixAggregate(
        total_reservation_class_failed=len(reservation_rows),
        stale_reservation_class_failed=len(stale_res),
        non_stale_reservation_class_failed=len(reservation_rows) - len(stale_res),
        conflict_reason_histogram=dict(
            Counter(r.commit_conflict_reason or "null" for r in reservation_rows)
        ),
        route_cell_family_count=route_n,
        inlet_family_count=inlet_n,
    )


def build_e0_mechanism_rows(
    *,
    ledger: Sequence[ElcpAttemptLedgerRow],
    snapshots_after_success: Sequence[MirrorDomainSnapshot],
    snapshots_at_attempt: Sequence[MirrorDomainSnapshot],
    candidates_by_id: Mapping[str, BundleCandidate],
    replay_cache: Mapping[tuple[int, str], MechanismReplaySignals],
    git_sha: str,
) -> tuple[ElcpE0MechanismRow, ...]:
    at_attempt = _at_attempt_by_index(snapshots_at_attempt)
    rows: list[ElcpE0MechanismRow] = []

    for entry in ledger:
        if entry.probe_failure_class is not ElcpProbeFailureClass.STALE_CANDIDATE_REACHABLE:
            continue
        candidate = candidates_by_id[entry.candidate_id]
        attempt_snap = at_attempt[entry.commit_index]
        before = _snapshot_before_commit_index(snapshots_after_success, entry.commit_index)
        blocking_count, _ = diff_blocking_cells(before=before, at_attempt=attempt_snap)

        cache_key = (entry.commit_index, entry.candidate_id)
        signals = replay_cache.get(cache_key)
        if signals is None:
            stub = candidate.output_stub
            signals = MechanismReplaySignals(
                private_overlap_cells=frozenset(),
                shareable_trunk_undercoverage_cells=frozenset(),
                spine_augment_cells=frozenset(),
                probe_merged_route_diff_cells=frozenset(),
                output_stub_in_committed_route=stub in attempt_snap.committed_route_cells,
                inlet_stub_adjacent_committed_route_cells=frozenset(
                    c
                    for c in _stub_neighbor_coords(stub)
                    if c in attempt_snap.committed_route_cells and c != stub
                ),
            )

        mechanism_class = classify_e0_mechanism(
            commit_conflict_reason=entry.commit_conflict_reason,
            private_overlap_cells=signals.private_overlap_cells,
            shareable_trunk_undercoverage_cells=signals.shareable_trunk_undercoverage_cells,
            spine_augment_cells=signals.spine_augment_cells,
            probe_merged_route_diff_cells=signals.probe_merged_route_diff_cells,
            output_stub_in_committed_route=signals.output_stub_in_committed_route,
            inlet_stub_adjacent_committed_route_cells=(
                signals.inlet_stub_adjacent_committed_route_cells
            ),
        )

        rows.append(
            ElcpE0MechanismRow(
                commit_index=entry.commit_index,
                candidate_id=entry.candidate_id,
                probe_failure_class=entry.probe_failure_class.value,
                commit_conflict_reason=entry.commit_conflict_reason,
                elcp_e0_mechanism_class=mechanism_class,
                mechanism_owner_module=MECHANISM_OWNER_MODULE[mechanism_class],
                candidate_route_probe_reachable=candidate.reachable,
                commit_probe_reachable=bool(entry.probe_reachable),
                private_overlap_cell_count=len(signals.private_overlap_cells),
                private_overlap_sample=_bounded_sample(signals.private_overlap_cells),
                shareable_trunk_undercoverage_count=len(
                    signals.shareable_trunk_undercoverage_cells
                ),
                spine_augment_cell_count=len(signals.spine_augment_cells),
                probe_merged_route_diff_count=len(signals.probe_merged_route_diff_cells),
                output_stub_in_committed_route=signals.output_stub_in_committed_route,
                probe_expanded_nodes=entry.probe_expanded_nodes,
                probe_max_expansions=entry.max_expansions,
                new_blocking_cells_since_last_commit_count=blocking_count,
                assigned_lane_id=entry.assigned_lane_id,
                git_sha=git_sha,
            )
        )

    return tuple(rows)


@dataclass(frozen=True, slots=True)
class ElcpE0ForensicsResult:
    git_sha: str
    rows: tuple[ElcpE0MechanismRow, ...]
    mechanism_histogram: dict[str, int]
    verdict: ElcpE0Verdict
    nomination: BSpecNomination
    mechanism_coverage: float
    unattributed_ratio: float
    mirror_parity_ok: bool
    appendix_aggregate: AppendixAggregate
    d0_carry_forward: dict[str, Any]


def run_gate_a_elcp_e0_reservation_forensics(
    *,
    imported_game_data_batch_module: object,
) -> ElcpE0ForensicsResult:
    git_sha = resolve_git_sha()
    inp, pipeline_config = build_gate_a_rf1_inputs(
        imported_game_data_batch_module=imported_game_data_batch_module,
    )
    config = replace(
        pipeline_config,
        selection_mode=SelectionMode.GREEDY_REGRET_OVERLAP_PACK,
    )
    captured: dict[str, object] = {}
    primary_results: list[CommitResult] = []
    real_commit = incremental_commit

    def _capture_primary(*args: object, **kwargs: object) -> CommitResult:
        result = real_commit(*args, **kwargs)
        primary_results.append(result)
        captured["genome"] = args[0]
        captured["candidates_by_id"] = args[1]
        captured["inp"] = args[2]
        captured["skeleton"] = args[3]
        captured["domain"] = kwargs["domain"]
        captured["exterior_lane_plan"] = kwargs.get("exterior_lane_plan")
        captured["route_probe_start_policy"] = kwargs.get("route_probe_start_policy")
        captured["resource_kind"] = kwargs.get("resource_kind")
        return result

    with patch(
        "django_apps.asteroid_lab.optimization.pipeline.incremental_commit",
        side_effect=_capture_primary,
    ):
        run_rttp_pipeline(
            inp,
            policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
            fixed_output_transport_policy=FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
            route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
            pipeline_config=config,
        )

    if not primary_results:
        msg = "primary incremental_commit was not called"
        raise AssertionError(msg)

    primary = primary_results[0]
    plan = captured["exterior_lane_plan"]
    if plan is None:
        msg = "ELCP exterior_lane_plan required for E0 Gate A"
        raise AssertionError(msg)

    mirror_parity_ok = True
    try:
        mirror = build_elcp_primary_mirror_ledger(
            genome=captured["genome"],
            candidates_by_id=captured["candidates_by_id"],
            inp=captured["inp"],
            skeleton=captured["skeleton"],
            domain=captured["domain"],
            exterior_lane_plan=plan,
            route_probe_start_policy=captured["route_probe_start_policy"],
            resource_kind=str(captured["resource_kind"]),
            collect_domain_snapshots=True,
        )
        assert_mirror_parity(production=primary, mirror=mirror)
    except AssertionError:
        mirror_parity_ok = False
        mirror = build_elcp_primary_mirror_ledger(
            genome=captured["genome"],
            candidates_by_id=captured["candidates_by_id"],
            inp=captured["inp"],
            skeleton=captured["skeleton"],
            domain=captured["domain"],
            exterior_lane_plan=plan,
            route_probe_start_policy=captured["route_probe_start_policy"],
            resource_kind=str(captured["resource_kind"]),
            collect_domain_snapshots=True,
        )

    replay_cache = build_stale_replay_signal_cache(
        genome=captured["genome"],
        candidates_by_id=captured["candidates_by_id"],
        inp=captured["inp"],
        skeleton=captured["skeleton"],
        domain=captured["domain"],
        exterior_lane_plan=plan,
        route_probe_start_policy=captured["route_probe_start_policy"],
        resource_kind=str(captured["resource_kind"]),
    )

    rows = build_e0_mechanism_rows(
        ledger=mirror.ledger,
        snapshots_after_success=mirror.domain_snapshots_after_success,
        snapshots_at_attempt=mirror.domain_snapshots_at_attempt,
        candidates_by_id=captured["candidates_by_id"],
        replay_cache=replay_cache,
        git_sha=git_sha,
    )

    appendix = build_reservation_class_appendix_aggregate(mirror.ledger)
    mechanism_classes = [r.elcp_e0_mechanism_class for r in rows]
    histogram = dict(Counter(c.value for c in mechanism_classes))
    unattributed = sum(1 for c in mechanism_classes if is_unattributed_mechanism_class(c))
    coverage = 1.0 - (unattributed / len(rows)) if rows else 0.0

    primary_route = sum(1 for c in mechanism_classes if is_route_cell_mechanism_family(c))
    primary_inlet = sum(1 for c in mechanism_classes if is_inlet_mechanism_family(c))

    appendix_veto = evaluate_appendix_veto(
        primary_route_family_count=primary_route,
        primary_inlet_family_count=primary_inlet,
        appendix_route_family_count=appendix.route_cell_family_count,
        appendix_inlet_family_count=appendix.inlet_family_count,
    )

    verdict = compute_e0_verdict(
        mechanism_classes,
        mirror_parity_ok=mirror_parity_ok,
        appendix_veto=appendix_veto,
    )
    nomination = evaluate_b_spec_nomination(
        verdict=verdict,
        mechanism_classes=mechanism_classes,
        appendix_veto=appendix_veto,
    )

    return ElcpE0ForensicsResult(
        git_sha=git_sha,
        rows=rows,
        mechanism_histogram=histogram,
        verdict=verdict,
        nomination=nomination,
        mechanism_coverage=coverage,
        unattributed_ratio=unattributed / len(rows) if rows else 1.0,
        mirror_parity_ok=mirror_parity_ok,
        appendix_aggregate=appendix,
        d0_carry_forward={
            "d0_verdict": "reservation_drift_dominant",
            "d0_stale_row_count": 34,
            "d0_conflict_mix": "route_cell_conflict=22,inlet_on_shared_transport=12",
        },
    )
