"""P1-ELCP-RF-F1.1: private_route_overlap row-level forensic (not solver input).

Secondary root-cause taxonomy on post-F1 private_route_overlap slice rows.
Replay uses production commit helpers; attribution is non-causal evidence.
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
    shareable_trunk_cells_for_transport,
    update_trunk_state_after_commit,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    _COMMIT_PROBE_MAX_EXPANSIONS,
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
from django_apps.asteroid_lab.optimization.commit.reservation_overlap_policy import (
    compute_elcp_reservation_candidate_cells,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.routing.route_goals import (
    probe_goal_coords,
    probe_goal_priorities,
)
from django_apps.asteroid_lab.optimization.routing.route_probe_start import (
    resolve_route_probe_start,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton
from harness.investigation.rttp_elcp_c0_dual_mode import (
    build_gate_a_rf1_inputs,
    resolve_git_sha,
)
from harness.investigation.rttp_elcp_e0_reservation_mechanism import (
    ElcpE0MechanismClass,
    ElcpE0MechanismRow,
    build_e0_mechanism_rows,
    build_stale_replay_signal_cache,
)
from harness.investigation.rttp_elcp_reprobe_forensics import (
    ElcpProbeFailureClass,
    assert_mirror_parity,
    build_elcp_primary_mirror_ledger,
    classify_probe_failure,
)
from tests.support.rttp_e0_gate_a_frozen_bounds import EXPECTED_OVERLAP_STALE_ROW_COUNT
from tests.support.rttp_f11_gate_a_frozen_bounds import (
    F11_ROOT_CAUSE_DOMINANCE_MIN_COUNT,
    F11_UNCLEAR_MAX_ROWS,
)

_SAMPLE_MAX = 10


class ElcpF11PrivateOverlapRootCause(StrEnum):
    TRUNK_EVIDENCE_MISSING = "trunk_evidence_missing"
    COMMITTED_GROWTH_ARTIFACT = "committed_growth_artifact"
    SPINE_OR_STUB_RESIDUAL_OVERLAP = "spine_or_stub_residual_overlap"
    TRUE_PEER_BRANCH_OVERLAP = "true_peer_branch_overlap"
    UNCLEAR_NEEDS_TRACE = "unclear_needs_trace"


F11_ROOT_CAUSE_OWNER: dict[ElcpF11PrivateOverlapRootCause, str] = {
    ElcpF11PrivateOverlapRootCause.TRUNK_EVIDENCE_MISSING: (
        "exterior_lane_trunk.shareable_trunk_cells_for_transport"
    ),
    ElcpF11PrivateOverlapRootCause.COMMITTED_GROWTH_ARTIFACT: (
        "reservation_overlap_policy.compute_elcp_reservation_candidate_cells"
    ),
    ElcpF11PrivateOverlapRootCause.SPINE_OR_STUB_RESIDUAL_OVERLAP: (
        "incremental_commit._augment_route_cells_with_output_spine"
    ),
    ElcpF11PrivateOverlapRootCause.TRUE_PEER_BRANCH_OVERLAP: (
        "incremental_commit._private_route_cell_overlap"
    ),
    ElcpF11PrivateOverlapRootCause.UNCLEAR_NEEDS_TRACE: "unattributed",
}


class F12NominationWithheldReason(StrEnum):
    NONE = "none"
    UNCLEAR_TOO_HIGH = "unclear_too_high"
    NO_DOMINANT_ROOT_CAUSE = "no_dominant_root_cause"
    TRUE_PEER_DOMINANT = "true_peer_dominant"
    SPLIT_FIXABLE_CLASSES = "split_fixable_classes"
    PARENT_MIRROR_FAIL = "parent_mirror_fail"


_FIXABLE_CAUSES_ORDERED: tuple[ElcpF11PrivateOverlapRootCause, ...] = (
    ElcpF11PrivateOverlapRootCause.TRUNK_EVIDENCE_MISSING,
    ElcpF11PrivateOverlapRootCause.COMMITTED_GROWTH_ARTIFACT,
    ElcpF11PrivateOverlapRootCause.SPINE_OR_STUB_RESIDUAL_OVERLAP,
)

_F12_TRACK_BY_CAUSE: dict[ElcpF11PrivateOverlapRootCause, str] = {
    ElcpF11PrivateOverlapRootCause.TRUNK_EVIDENCE_MISSING: "F1.2a",
    ElcpF11PrivateOverlapRootCause.COMMITTED_GROWTH_ARTIFACT: "F1.2b",
    ElcpF11PrivateOverlapRootCause.SPINE_OR_STUB_RESIDUAL_OVERLAP: "F1.2c",
}


def classify_f11_root_cause(
    *,
    overlap_undercoverage_cells: frozenset[Coord],
    overlap_full_not_reserved: frozenset[Coord],
    overlap_spine_stub: frozenset[Coord],
    overlap_branch_only: frozenset[Coord],
    overlap_trunk_mask: frozenset[Coord],
) -> ElcpF11PrivateOverlapRootCause:
    if overlap_undercoverage_cells:
        return ElcpF11PrivateOverlapRootCause.TRUNK_EVIDENCE_MISSING
    if overlap_full_not_reserved:
        return ElcpF11PrivateOverlapRootCause.COMMITTED_GROWTH_ARTIFACT
    if overlap_spine_stub:
        return ElcpF11PrivateOverlapRootCause.SPINE_OR_STUB_RESIDUAL_OVERLAP
    if overlap_branch_only:
        return ElcpF11PrivateOverlapRootCause.TRUE_PEER_BRANCH_OVERLAP
    if not overlap_trunk_mask:
        return ElcpF11PrivateOverlapRootCause.TRUE_PEER_BRANCH_OVERLAP
    return ElcpF11PrivateOverlapRootCause.UNCLEAR_NEEDS_TRACE


@dataclass(frozen=True, slots=True)
class F12PolicyNomination:
    nominated: bool
    nominated_track: str | None
    title: str | None
    withheld_reason: F12NominationWithheldReason

    def to_dict(self) -> dict[str, Any]:
        return {
            "nominated": self.nominated,
            "nominated_track": self.nominated_track,
            "title": self.title,
            "withheld_reason": self.withheld_reason.value,
        }


def evaluate_f12_nomination(
    *,
    root_cause_counts: dict[str, int],
    unclear_count: int,
    mirror_parity_ok: bool,
    row_count: int,
    dominance_min: int = F11_ROOT_CAUSE_DOMINANCE_MIN_COUNT,
    unclear_max: int = F11_UNCLEAR_MAX_ROWS,
    split_fixable_min: int = 7,
) -> F12PolicyNomination:
    if not mirror_parity_ok:
        return F12PolicyNomination(
            nominated=False,
            nominated_track=None,
            title=None,
            withheld_reason=F12NominationWithheldReason.PARENT_MIRROR_FAIL,
        )
    if row_count == 0:
        return F12PolicyNomination(
            nominated=False,
            nominated_track=None,
            title=None,
            withheld_reason=F12NominationWithheldReason.NO_DOMINANT_ROOT_CAUSE,
        )
    if unclear_count > unclear_max:
        return F12PolicyNomination(
            nominated=False,
            nominated_track=None,
            title=None,
            withheld_reason=F12NominationWithheldReason.UNCLEAR_TOO_HIGH,
        )

    true_peer_n = root_cause_counts.get(
        ElcpF11PrivateOverlapRootCause.TRUE_PEER_BRANCH_OVERLAP.value,
        0,
    )
    if true_peer_n >= dominance_min:
        return F12PolicyNomination(
            nominated=False,
            nominated_track=None,
            title="Retain private overlap reject policy (true peer dominant)",
            withheld_reason=F12NominationWithheldReason.TRUE_PEER_DOMINANT,
        )

    fixable_counts = [
        (cause, root_cause_counts.get(cause.value, 0)) for cause in _FIXABLE_CAUSES_ORDERED
    ]
    fixable_counts.sort(
        key=lambda item: (-item[1], _FIXABLE_CAUSES_ORDERED.index(item[0])),
    )
    top_cause, top_n = fixable_counts[0]

    if top_n >= dominance_min:
        track = _F12_TRACK_BY_CAUSE[top_cause]
        return F12PolicyNomination(
            nominated=True,
            nominated_track=track,
            title=f"Bounded {track}: {top_cause.value}",
            withheld_reason=F12NominationWithheldReason.NONE,
        )

    fixable_at_split = [cause for cause, n in fixable_counts if n >= split_fixable_min]
    if len(fixable_at_split) >= 2:
        return F12PolicyNomination(
            nominated=False,
            nominated_track=None,
            title="Split fixable classes — one F1.2 policy change per PR",
            withheld_reason=F12NominationWithheldReason.SPLIT_FIXABLE_CLASSES,
        )

    return F12PolicyNomination(
        nominated=False,
        nominated_track=None,
        title=None,
        withheld_reason=F12NominationWithheldReason.NO_DOMINANT_ROOT_CAUSE,
    )


def _bounded_sample(cells: frozenset[Coord]) -> tuple[Coord, ...]:
    return tuple(sorted(cells)[:_SAMPLE_MAX])


def _stub_neighbor_coords(stub: Coord) -> tuple[Coord, ...]:
    x, y = stub
    return ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))


@dataclass(frozen=True, slots=True)
class F11OverlapPartitionEvidence:
    overlap_partition: dict[str, int]
    overlap_in_shareable_at_commit: int
    overlap_in_trunk_mask: int
    overlap_in_full_route_not_reserved: int
    overlap_in_committed_delta_only: int
    overlap_in_spine_or_stub_residual: int
    overlap_in_true_private_branch: int
    shareable_undercoverage_flag: bool
    spine_stub_residual_flag: bool
    overlap_undercoverage_cells: frozenset[Coord]
    overlap_full_not_reserved: frozenset[Coord]
    overlap_spine_stub: frozenset[Coord]
    overlap_branch_only: frozenset[Coord]
    overlap_trunk_mask: frozenset[Coord]
    reservation_candidate_cells: frozenset[Coord]
    full_route_cells: frozenset[Coord]
    path_vs_reservation_diff: frozenset[Coord]
    branch_cells: frozenset[Coord]
    new_trunk_cells: frozenset[Coord]
    reused_trunk_cells: frozenset[Coord]
    shareable_at_commit: frozenset[Coord]
    replay_invariant_violation: bool


def compute_f11_overlap_partitions(
    *,
    private_overlap: frozenset[Coord],
    shareable_at_commit: frozenset[Coord],
    reservation_candidate: frozenset[Coord],
    full_route_cells: frozenset[Coord],
    trunk_mask_cells: frozenset[Coord],
    branch_cells: frozenset[Coord],
    spine_augment_cells: frozenset[Coord],
    probe_merged_route_diff_cells: frozenset[Coord],
    stub_adjacent_committed: frozenset[Coord],
    undercoverage_cells: frozenset[Coord],
    committed_route_delta: frozenset[Coord],
    new_trunk_cells: frozenset[Coord],
    reused_trunk_cells: frozenset[Coord],
) -> F11OverlapPartitionEvidence:
    overlap_o = private_overlap
    o_shareable = frozenset(c for c in overlap_o if c in shareable_at_commit)
    o_trunk_mask = frozenset(c for c in overlap_o if c in trunk_mask_cells)
    o_full_not_reserved = frozenset(
        c for c in overlap_o if c in full_route_cells and c not in reservation_candidate
    )
    spine_stub_union = spine_augment_cells | probe_merged_route_diff_cells | stub_adjacent_committed
    o_spine_stub = frozenset(c for c in overlap_o if c in spine_stub_union)
    branch_set = branch_cells
    o_branch_only = frozenset(
        c for c in overlap_o if c in branch_set and c not in o_trunk_mask and c not in o_spine_stub
    )
    overlap_undercoverage = frozenset(c for c in undercoverage_cells if c in overlap_o)
    o_delta_only = frozenset(c for c in overlap_o if c in committed_route_delta)

    partition = {
        "shareable": len(o_shareable),
        "trunk_mask": len(o_trunk_mask),
        "full_route_not_reserved": len(o_full_not_reserved),
        "spine_or_stub": len(o_spine_stub),
        "branch_only": len(o_branch_only),
    }

    replay_invariant_violation = bool(overlap_o and full_route_cells == reservation_candidate)

    return F11OverlapPartitionEvidence(
        overlap_partition=partition,
        overlap_in_shareable_at_commit=len(o_shareable),
        overlap_in_trunk_mask=len(o_trunk_mask),
        overlap_in_full_route_not_reserved=len(o_full_not_reserved),
        overlap_in_committed_delta_only=len(o_delta_only),
        overlap_in_spine_or_stub_residual=len(o_spine_stub),
        overlap_in_true_private_branch=len(o_branch_only),
        shareable_undercoverage_flag=bool(overlap_undercoverage),
        spine_stub_residual_flag=bool(o_spine_stub),
        overlap_undercoverage_cells=overlap_undercoverage,
        overlap_full_not_reserved=o_full_not_reserved,
        overlap_spine_stub=o_spine_stub,
        overlap_branch_only=o_branch_only,
        overlap_trunk_mask=o_trunk_mask,
        reservation_candidate_cells=reservation_candidate,
        full_route_cells=full_route_cells,
        path_vs_reservation_diff=probe_merged_route_diff_cells,
        branch_cells=branch_cells,
        new_trunk_cells=new_trunk_cells,
        reused_trunk_cells=reused_trunk_cells,
        shareable_at_commit=shareable_at_commit,
        replay_invariant_violation=replay_invariant_violation,
    )


def _f11_evidence_from_attempt(
    *,
    candidate: BundleCandidate,
    inp: OptimizationInput,
    committed_route_cells: frozenset[Coord],
    current_domain: object,
    probe: object,
    shareable_at_commit: frozenset[Coord],
    branch_cells: tuple[Coord, ...],
    new_trunk_cells: tuple[Coord, ...],
    reused_trunk_cells: tuple[Coord, ...],
    committed_route_delta: frozenset[Coord],
) -> F11OverlapPartitionEvidence | None:
    if not probe.reachable:
        return None

    path_cells = _route_cells_from_path(probe.path, candidate.occupied_cells)
    reservation_candidate = compute_elcp_reservation_candidate_cells(
        candidate=candidate,
        inp=inp,
        domain=current_domain,
        branch_cells=branch_cells,
        new_trunk_cells=new_trunk_cells,
        reused_trunk_cells=reused_trunk_cells,
        shareable_at_commit=shareable_at_commit,
        committed_route_cells=committed_route_cells,
    )
    if reservation_candidate is None:
        reservation_candidate = frozenset()

    base_cells = frozenset(branch_cells) | frozenset(new_trunk_cells)
    augmented = _augment_route_cells_with_output_spine(
        candidate,
        base_cells,
        current_domain,
        committed_route_cells=committed_route_cells,
        shareable_trunk_cells=shareable_at_commit,
    )
    spine_augment = frozenset(augmented - base_cells)
    full_route = _route_cells_with_required_output_stub(
        candidate,
        augmented,
        current_domain,
        inp,
    )
    if full_route is None:
        full_route = augmented

    private_overlap = _private_route_cell_overlap(
        reservation_candidate,
        committed_route_cells,
        shareable_trunk_cells=shareable_at_commit,
    )
    if not private_overlap:
        return None

    overlap_all = reservation_candidate & committed_route_cells
    undercoverage = frozenset(
        c
        for c in overlap_all
        if c not in shareable_at_commit and c in current_domain.trunk_mask_cells
    )
    probe_merged_diff = frozenset(
        (reservation_candidate - path_cells) | (path_cells - reservation_candidate)
    )
    stub = candidate.output_stub
    stub_adjacent = frozenset(
        c for c in _stub_neighbor_coords(stub) if c in committed_route_cells and c != stub
    )

    return compute_f11_overlap_partitions(
        private_overlap=private_overlap,
        shareable_at_commit=shareable_at_commit,
        reservation_candidate=reservation_candidate,
        full_route_cells=full_route,
        trunk_mask_cells=current_domain.trunk_mask_cells,
        branch_cells=frozenset(branch_cells),
        spine_augment_cells=spine_augment,
        probe_merged_route_diff_cells=probe_merged_diff,
        stub_adjacent_committed=stub_adjacent,
        undercoverage_cells=undercoverage,
        committed_route_delta=committed_route_delta,
        new_trunk_cells=frozenset(new_trunk_cells),
        reused_trunk_cells=frozenset(reused_trunk_cells),
    )


def build_f11_overlap_evidence_cache(
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
) -> dict[tuple[int, str], F11OverlapPartitionEvidence]:
    resolved_max = _COMMIT_PROBE_MAX_EXPANSIONS if max_expansions is None else max_expansions
    goals = probe_goal_coords(inp, skeleton)
    goal_priorities = probe_goal_priorities(inp)
    goals_nonempty = len(goals) > 0

    committed_occupied = domain.committed_occupied
    committed_route_cells = domain.committed_route_cells
    committed_fixed_output_transport_cells = domain.committed_fixed_output_transport_cells

    assignment_state = initial_assignment_state(exterior_lane_plan)
    trunk_states_elcp = initial_trunk_states(exterior_lane_plan)
    cache: dict[tuple[int, str], F11OverlapPartitionEvidence] = {}

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
        tm_branch, tm_reused, tm_new_trunk = partition_path_branch_and_trunk(
            path=fill_first.probe.path,
            existing_trunk=trunk_row_pre.trunk_cells,
            connector_coord=lane_spec.connector_goal.coord,
        )
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
            precomputed_route_cells=frozenset(tm_branch) | frozenset(tm_new_trunk),
            precomputed_probe=fill_first.probe,
            shareable_trunk_cells=shareable_at_commit,
            overlap_reservation_cells=reservation_candidate_cells,
        )

        if outcome.committed:
            route_delta = (
                outcome.committed_route_delta
                if outcome.committed_route_delta
                else (outcome.route_cells or frozenset())
            )
            committed_occupied = frozenset(committed_occupied | candidate.occupied_cells)
            committed_fixed_output_transport_cells = frozenset(
                committed_fixed_output_transport_cells | {fixed_output_transport_cell(candidate)}
            )
            committed_route_cells = frozenset(committed_route_cells | route_delta)
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

        evidence = _f11_evidence_from_attempt(
            candidate=candidate,
            inp=inp,
            committed_route_cells=committed_route_cells,
            current_domain=current_domain,
            probe=fill_first.probe,
            shareable_at_commit=shareable_at_commit,
            branch_cells=tm_branch,
            new_trunk_cells=tm_new_trunk,
            reused_trunk_cells=tm_reused,
            committed_route_delta=outcome.committed_route_delta,
        )
        if evidence is not None:
            cache[(commit_index, candidate_id)] = evidence

    return cache


@dataclass(frozen=True, slots=True)
class ElcpF11OverlapForensicRow:
    commit_index: int
    candidate_id: str
    git_sha: str
    elcp_e0_mechanism_class: str
    private_overlap_cell_count: int
    private_overlap_sample: tuple[Coord, ...]
    assigned_lane_id: str | None
    overlap_partition: dict[str, int]
    overlap_in_shareable_at_commit: int
    overlap_in_trunk_mask: int
    overlap_in_full_route_not_reserved: int
    overlap_in_committed_delta_only: int
    overlap_in_spine_or_stub_residual: int
    overlap_in_true_private_branch: int
    shareable_undercoverage_flag: bool
    spine_stub_residual_flag: bool
    reservation_candidate_sample: tuple[Coord, ...]
    candidate_route_delta_sample: tuple[Coord, ...]
    branch_cells_sample: tuple[Coord, ...]
    new_trunk_cells_sample: tuple[Coord, ...]
    reused_trunk_cells_sample: tuple[Coord, ...]
    shareable_at_commit_sample: tuple[Coord, ...]
    f11_root_cause: ElcpF11PrivateOverlapRootCause
    f11_root_cause_owner: str
    replay_invariant_violation: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "commit_index": self.commit_index,
            "candidate_id": self.candidate_id,
            "git_sha": self.git_sha,
            "elcp_e0_mechanism_class": self.elcp_e0_mechanism_class,
            "private_overlap_cell_count": self.private_overlap_cell_count,
            "private_overlap_sample": [list(c) for c in self.private_overlap_sample],
            "assigned_lane_id": self.assigned_lane_id,
            "overlap_partition": self.overlap_partition,
            "overlap_in_shareable_at_commit": self.overlap_in_shareable_at_commit,
            "overlap_in_trunk_mask": self.overlap_in_trunk_mask,
            "overlap_in_full_route_not_reserved": self.overlap_in_full_route_not_reserved,
            "overlap_in_committed_delta_only": self.overlap_in_committed_delta_only,
            "overlap_in_spine_or_stub_residual": self.overlap_in_spine_or_stub_residual,
            "overlap_in_true_private_branch": self.overlap_in_true_private_branch,
            "shareable_undercoverage_flag": self.shareable_undercoverage_flag,
            "spine_stub_residual_flag": self.spine_stub_residual_flag,
            "reservation_candidate_sample": [list(c) for c in self.reservation_candidate_sample],
            "candidate_route_delta_sample": [list(c) for c in self.candidate_route_delta_sample],
            "branch_cells_sample": [list(c) for c in self.branch_cells_sample],
            "new_trunk_cells_sample": [list(c) for c in self.new_trunk_cells_sample],
            "reused_trunk_cells_sample": [list(c) for c in self.reused_trunk_cells_sample],
            "shareable_at_commit_sample": [list(c) for c in self.shareable_at_commit_sample],
            "f11_root_cause": self.f11_root_cause.value,
            "f11_root_cause_owner": self.f11_root_cause_owner,
            "replay_invariant_violation": self.replay_invariant_violation,
        }


def build_f11_forensic_rows(
    *,
    e0_rows: Sequence[ElcpE0MechanismRow],
    evidence_cache: Mapping[tuple[int, str], F11OverlapPartitionEvidence],
) -> tuple[ElcpF11OverlapForensicRow, ...]:
    rows: list[ElcpF11OverlapForensicRow] = []
    for e0_row in e0_rows:
        if e0_row.elcp_e0_mechanism_class is not ElcpE0MechanismClass.PRIVATE_ROUTE_OVERLAP:
            continue
        if e0_row.private_overlap_cell_count <= 0:
            continue
        key = (e0_row.commit_index, e0_row.candidate_id)
        evidence = evidence_cache.get(key)
        if evidence is None:
            msg = f"missing F1.1 evidence for {key}"
            raise KeyError(msg)

        root_cause = classify_f11_root_cause(
            overlap_undercoverage_cells=evidence.overlap_undercoverage_cells,
            overlap_full_not_reserved=evidence.overlap_full_not_reserved,
            overlap_spine_stub=evidence.overlap_spine_stub,
            overlap_branch_only=evidence.overlap_branch_only,
            overlap_trunk_mask=evidence.overlap_trunk_mask,
        )
        rows.append(
            ElcpF11OverlapForensicRow(
                commit_index=e0_row.commit_index,
                candidate_id=e0_row.candidate_id,
                git_sha=e0_row.git_sha,
                elcp_e0_mechanism_class=e0_row.elcp_e0_mechanism_class.value,
                private_overlap_cell_count=e0_row.private_overlap_cell_count,
                private_overlap_sample=e0_row.private_overlap_sample,
                assigned_lane_id=e0_row.assigned_lane_id,
                overlap_partition=dict(evidence.overlap_partition),
                overlap_in_shareable_at_commit=evidence.overlap_in_shareable_at_commit,
                overlap_in_trunk_mask=evidence.overlap_in_trunk_mask,
                overlap_in_full_route_not_reserved=evidence.overlap_in_full_route_not_reserved,
                overlap_in_committed_delta_only=evidence.overlap_in_committed_delta_only,
                overlap_in_spine_or_stub_residual=evidence.overlap_in_spine_or_stub_residual,
                overlap_in_true_private_branch=evidence.overlap_in_true_private_branch,
                shareable_undercoverage_flag=evidence.shareable_undercoverage_flag,
                spine_stub_residual_flag=evidence.spine_stub_residual_flag,
                reservation_candidate_sample=_bounded_sample(evidence.reservation_candidate_cells),
                candidate_route_delta_sample=_bounded_sample(evidence.path_vs_reservation_diff),
                branch_cells_sample=_bounded_sample(evidence.branch_cells),
                new_trunk_cells_sample=_bounded_sample(evidence.new_trunk_cells),
                reused_trunk_cells_sample=_bounded_sample(evidence.reused_trunk_cells),
                shareable_at_commit_sample=_bounded_sample(evidence.shareable_at_commit),
                f11_root_cause=root_cause,
                f11_root_cause_owner=F11_ROOT_CAUSE_OWNER[root_cause],
                replay_invariant_violation=evidence.replay_invariant_violation,
            )
        )
    return tuple(rows)


@dataclass(frozen=True, slots=True)
class ElcpF11ForensicsResult:
    git_sha: str
    parent_stale_row_count: int
    private_overlap_row_count: int
    rows: tuple[ElcpF11OverlapForensicRow, ...]
    root_cause_histogram: dict[str, int]
    unclear_count: int
    mirror_parity_ok: bool
    f12_nomination: F12PolicyNomination


def run_gate_a_elcp_f11_private_overlap_forensics(
    *,
    imported_game_data_batch_module: object,
) -> ElcpF11ForensicsResult:
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
        msg = "ELCP exterior_lane_plan required for F1.1 Gate A"
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

    if not mirror_parity_ok:
        return ElcpF11ForensicsResult(
            git_sha=git_sha,
            parent_stale_row_count=0,
            private_overlap_row_count=0,
            rows=(),
            root_cause_histogram={},
            unclear_count=0,
            mirror_parity_ok=False,
            f12_nomination=evaluate_f12_nomination(
                root_cause_counts={},
                unclear_count=0,
                mirror_parity_ok=False,
                row_count=0,
            ),
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

    evidence_cache = build_f11_overlap_evidence_cache(
        genome=captured["genome"],
        candidates_by_id=captured["candidates_by_id"],
        inp=captured["inp"],
        skeleton=captured["skeleton"],
        domain=captured["domain"],
        exterior_lane_plan=plan,
        route_probe_start_policy=captured["route_probe_start_policy"],
        resource_kind=str(captured["resource_kind"]),
    )

    e0_rows = build_e0_mechanism_rows(
        ledger=mirror.ledger,
        snapshots_after_success=mirror.domain_snapshots_after_success,
        snapshots_at_attempt=mirror.domain_snapshots_at_attempt,
        candidates_by_id=captured["candidates_by_id"],
        replay_cache=replay_cache,
        git_sha=git_sha,
    )

    parent_stale_row_count = len(e0_rows)
    f11_rows = build_f11_forensic_rows(
        e0_rows=e0_rows,
        evidence_cache=evidence_cache,
    )

    root_causes = [r.f11_root_cause for r in f11_rows]
    histogram = dict(Counter(c.value for c in root_causes))
    unclear_count = sum(
        1 for c in root_causes if c is ElcpF11PrivateOverlapRootCause.UNCLEAR_NEEDS_TRACE
    )

    nomination = evaluate_f12_nomination(
        root_cause_counts=histogram,
        unclear_count=unclear_count,
        mirror_parity_ok=True,
        row_count=len(f11_rows),
    )

    if parent_stale_row_count != EXPECTED_OVERLAP_STALE_ROW_COUNT:
        msg = (
            f"expected {EXPECTED_OVERLAP_STALE_ROW_COUNT} stale rows, got {parent_stale_row_count}"
        )
        raise AssertionError(msg)

    return ElcpF11ForensicsResult(
        git_sha=git_sha,
        parent_stale_row_count=parent_stale_row_count,
        private_overlap_row_count=len(f11_rows),
        rows=f11_rows,
        root_cause_histogram=histogram,
        unclear_count=unclear_count,
        mirror_parity_ok=True,
        f12_nomination=nomination,
    )
