"""Read-only ELCP exterior lane contract validation."""

from __future__ import annotations

from collections import deque
from decimal import Decimal

from django_apps.asteroid_lab.contracts.exterior_lane_capacity import (
    ACTIVATION_REASON_CAPACITY_EXHAUSTED,
    ExteriorLaneCapacityPlan,
    ExteriorTransportLane,
)
from django_apps.asteroid_lab.contracts.rttp_layout_issue_codes import (
    ISSUE_CODE_EXTERIOR_LANE_BRANCH_NOT_CONNECTED_TO_TRUNK,
    ISSUE_CODE_EXTERIOR_LANE_KIND_MISMATCH,
    ISSUE_CODE_EXTERIOR_LANE_OVER_CAPACITY,
    ISSUE_CODE_EXTERIOR_LANE_PREMATURE_ACTIVATION,
    ISSUE_CODE_EXTERIOR_LANE_TRUNK_NOT_SHARED,
    ISSUE_CODE_ROUTE_WITHOUT_LANE_ASSIGNMENT,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.commit.exterior_lane_assignment import (
    assigned_load_by_lane_id,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import CommitResult
from django_apps.asteroid_lab.snapshots.grid_contract import Coord, neighbors4


def _lane_by_id(plan: ExteriorLaneCapacityPlan) -> dict[str, ExteriorTransportLane]:
    return {lane.lane_id: lane for lane in plan.lanes}


def _trunk_is_single_component(trunk_cells: frozenset[Coord]) -> bool:
    if len(trunk_cells) <= 1:
        return True
    start = next(iter(trunk_cells))
    visited: set[Coord] = {start}
    queue: deque[Coord] = deque([start])
    while queue:
        cur = queue.popleft()
        for nb in neighbors4(cur):
            if nb in trunk_cells and nb not in visited:
                visited.add(nb)
                queue.append(nb)
    return len(visited) == len(trunk_cells)


def _branch_cells_reach_anchors(
    branch_cells: tuple[Coord, ...],
    anchors: frozenset[Coord],
) -> bool:
    """True when every branch cell lies in the same 4-neighbor component as some anchor."""
    if not branch_cells:
        return True
    if not anchors:
        return False
    branch_set = frozenset(branch_cells)
    allowed = branch_set | anchors
    visited: set[Coord] = set()
    queue: deque[Coord] = deque()
    for cell in anchors:
        if cell in allowed:
            visited.add(cell)
            queue.append(cell)
    while queue:
        cur = queue.popleft()
        for nb in neighbors4(cur):
            if nb not in allowed or nb in visited:
                continue
            visited.add(nb)
            queue.append(nb)
    return branch_set <= visited


def validate_exterior_lane_contract_issues(
    *,
    committed_ids: tuple[str, ...],
    commit_result: CommitResult,
    candidates_by_id: dict[str, BundleCandidate],
    exterior_lane_plan: ExteriorLaneCapacityPlan | None,
) -> tuple[str, ...]:
    """Return stable issue codes when ELCP lane contract is violated (read-only)."""

    if exterior_lane_plan is None or not committed_ids:
        return ()

    issues: list[str] = []
    lanes = _lane_by_id(exterior_lane_plan)
    assignments_by_candidate = {
        str(row["candidate_id"]): row
        for row in commit_result.exterior_lane_assignments
        if "candidate_id" in row
    }

    for candidate_id in committed_ids:
        if candidate_id not in assignments_by_candidate:
            issues.append(ISSUE_CODE_ROUTE_WITHOUT_LANE_ASSIGNMENT)
            continue
        row = assignments_by_candidate[candidate_id]
        lane_id = str(row.get("exterior_lane_id", ""))
        lane = lanes.get(lane_id)
        candidate = candidates_by_id.get(candidate_id)
        if lane is None or candidate is None:
            issues.append(ISSUE_CODE_ROUTE_WITHOUT_LANE_ASSIGNMENT)
            continue
        if candidate.transport_kind is not lane.transport_kind:
            issues.append(ISSUE_CODE_EXTERIOR_LANE_KIND_MISMATCH)

    assigned = assigned_load_by_lane_id(commit_result.exterior_lane_assignment_state)
    for lane_id, load in assigned.items():
        lane = lanes.get(lane_id)
        if lane is None:
            continue
        if load > lane.capacity_per_min:
            issues.append(ISSUE_CODE_EXTERIOR_LANE_OVER_CAPACITY)

    total_capacity = sum(
        (lane.capacity_per_min for lane in exterior_lane_plan.lanes),
        Decimal("0"),
    )
    total_assigned = sum(assigned.values(), start=Decimal("0"))
    if total_assigned > total_capacity:
        if ISSUE_CODE_EXTERIOR_LANE_OVER_CAPACITY not in issues:
            issues.append(ISSUE_CODE_EXTERIOR_LANE_OVER_CAPACITY)

    for activation in commit_result.exterior_lane_activations:
        if activation.activation_reason != ACTIVATION_REASON_CAPACITY_EXHAUSTED:
            issues.append(ISSUE_CODE_EXTERIOR_LANE_PREMATURE_ACTIVATION)
            continue
        combined = (
            activation.previous_lane_assigned_load_per_min
            + activation.trigger_candidate_throughput_per_min
        )
        if combined <= activation.previous_lane_capacity_per_min:
            issues.append(ISSUE_CODE_EXTERIOR_LANE_PREMATURE_ACTIVATION)

    for trunk_state in commit_result.exterior_lane_trunk_states:
        if not trunk_state.active or not trunk_state.trunk_cells:
            continue
        if not _trunk_is_single_component(trunk_state.trunk_cells):
            issues.append(ISSUE_CODE_EXTERIOR_LANE_TRUNK_NOT_SHARED)

    trunk_by_lane = {
        state.lane_id: state for state in commit_result.exterior_lane_trunk_states
    }
    for evidence in commit_result.exterior_lane_route_evidence:
        if not evidence.branch_cells:
            continue
        anchors = frozenset(evidence.reused_trunk_cells) | frozenset(evidence.new_trunk_cells)
        if not anchors:
            lane_state = trunk_by_lane.get(evidence.lane_id)
            if lane_state is not None and lane_state.trunk_cells:
                anchors = lane_state.trunk_cells
            else:
                continue
        if not _branch_cells_reach_anchors(evidence.branch_cells, anchors):
            issues.append(ISSUE_CODE_EXTERIOR_LANE_BRANCH_NOT_CONNECTED_TO_TRUNK)

    return tuple(dict.fromkeys(issues))


__all__ = ["validate_exterior_lane_contract_issues"]
