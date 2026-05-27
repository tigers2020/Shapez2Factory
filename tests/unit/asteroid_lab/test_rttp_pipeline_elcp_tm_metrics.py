"""ELCP-TM Task 6 — rttp.commit pipeline metrics for exterior lane evidence (output-only)."""

from __future__ import annotations

from decimal import Decimal

from django_apps.asteroid_lab.contracts.exterior_lane_capacity import (
    ACTIVATION_REASON_CAPACITY_EXHAUSTED,
    ExteriorLaneActivationEvidence,
    ExteriorLaneCapacityPlan,
    ExteriorLaneRouteEvidence,
    ExteriorLaneTrunkState,
    ExteriorTransportLane,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import CommitResult
from django_apps.asteroid_lab.optimization.input_contracts import (
    RouteGoal,
    RouteGoalKind,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.pipeline import _exterior_lane_metrics_from_commit


def _goal(coord: tuple[int, int], *, priority: int = 20) -> RouteGoal:
    return RouteGoal(
        coord=coord,
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=priority,
        existing_trunk=False,
    )


def _minimal_exterior_lane_plan() -> ExteriorLaneCapacityPlan:
    lane = ExteriorTransportLane(
        lane_id="lane-a",
        transport_kind=TransportKind.SHAPE_BELT,
        connector_goal=_goal((10, 0)),
        capacity_per_min=Decimal("100"),
        target_load_per_min=Decimal("100"),
        anchor_coord=(10, 0),
    )
    return ExteriorLaneCapacityPlan(
        transport_kind=TransportKind.SHAPE_BELT,
        max_asteroid_throughput_per_min=Decimal("100"),
        lane_capacity_per_min=Decimal("100"),
        required_lane_count=1,
        lanes=(lane,),
    )


def test_exterior_lane_pipeline_metrics_empty_when_plan_disabled() -> None:
    commit = CommitResult(
        committed_ids=(),
        reserved_route_cells=frozenset(),
        domain_version=0,
        conflicts=(),
    )
    out = _exterior_lane_metrics_from_commit(commit, None)
    assert out["exterior_lane_activations"] == []
    assert out["exterior_lane_route_evidence"] == []
    assert out["exterior_lane_trunk_states_summary"] == []


def test_exterior_lane_pipeline_metrics_serializes_evidence_when_plan_enabled() -> None:
    activation = ExteriorLaneActivationEvidence(
        activated_lane_id="lane-b",
        previous_lane_id="lane-a",
        previous_lane_assigned_load_per_min=Decimal("99.5"),
        previous_lane_capacity_per_min=Decimal("100"),
        trigger_candidate_id="cand-1",
        trigger_candidate_throughput_per_min=Decimal("12"),
        activation_reason=ACTIVATION_REASON_CAPACITY_EXHAUSTED,
    )
    route_row = ExteriorLaneRouteEvidence(
        candidate_id="cand-1",
        lane_id="lane-a",
        candidate_throughput_per_min=Decimal("12"),
        branch_cells=((1, 2), (3, 4)),
        reused_trunk_cells=((0, 0),),
        new_trunk_cells=((5, 6),),
        reached_connector_coord=(10, 0),
        reached_trunk_coord=None,
    )
    trunk = ExteriorLaneTrunkState(
        lane_id="lane-a",
        transport_kind=TransportKind.SHAPE_BELT,
        active=True,
        assigned_load_per_min=Decimal("12"),
        trunk_cells=frozenset({(0, 0), (5, 6)}),
        connector_coord=(10, 0),
    )
    commit = CommitResult(
        committed_ids=("cand-1",),
        reserved_route_cells=frozenset({(0, 0)}),
        domain_version=1,
        conflicts=(),
        exterior_lane_activations=(activation,),
        exterior_lane_route_evidence=(route_row,),
        exterior_lane_trunk_states=(trunk,),
    )
    plan = _minimal_exterior_lane_plan()
    out = _exterior_lane_metrics_from_commit(commit, plan)

    assert len(out["exterior_lane_activations"]) == 1
    act = out["exterior_lane_activations"][0]
    assert act["activated_lane_id"] == "lane-b"
    assert act["previous_lane_id"] == "lane-a"
    assert act["activation_reason"] == ACTIVATION_REASON_CAPACITY_EXHAUSTED
    assert act["previous_lane_assigned_load_per_min"] == "99.5"
    assert act["previous_lane_capacity_per_min"] == "100"
    assert act["trigger_candidate_id"] == "cand-1"
    assert act["trigger_candidate_throughput_per_min"] == "12"

    assert len(out["exterior_lane_route_evidence"]) == 1
    ev = out["exterior_lane_route_evidence"][0]
    assert ev["candidate_id"] == "cand-1"
    assert ev["lane_id"] == "lane-a"
    assert ev["candidate_throughput_per_min"] == "12"
    assert ev["branch_cells"] == [[1, 2], [3, 4]]
    assert ev["reused_trunk_cells"] == [[0, 0]]
    assert ev["new_trunk_cells"] == [[5, 6]]
    assert ev["reached_connector_coord"] == [10, 0]
    assert ev["reached_trunk_coord"] is None

    assert len(out["exterior_lane_trunk_states_summary"]) == 1
    ts = out["exterior_lane_trunk_states_summary"][0]
    assert ts["lane_id"] == "lane-a"
    assert ts["active"] is True
    assert ts["assigned_load_per_min"] == "12"
    assert ts["trunk_cell_count"] == 2
