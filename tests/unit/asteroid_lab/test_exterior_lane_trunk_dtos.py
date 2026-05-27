"""ELCP-TM Task 1 — trunk / route / activation DTOs."""

from __future__ import annotations

from decimal import Decimal

from django_apps.asteroid_lab.contracts.exterior_lane_capacity import (
    ACTIVATION_REASON_CAPACITY_EXHAUSTED,
    ExteriorLaneActivationEvidence,
    ExteriorLaneRouteEvidence,
    ExteriorLaneTrunkState,
)
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind


def test_activation_reason_constant() -> None:
    assert ACTIVATION_REASON_CAPACITY_EXHAUSTED == "capacity_exhausted"


def test_trunk_state_frozen() -> None:
    row = ExteriorLaneTrunkState(
        lane_id="exterior_lane:shape_belt:0",
        transport_kind=TransportKind.SHAPE_BELT,
        active=True,
        assigned_load_per_min=Decimal("0"),
        trunk_cells=frozenset({(1, 2)}),
        connector_coord=(1, 5),
    )
    assert row.connector_coord == (1, 5)


def test_route_evidence_tuple_fields() -> None:
    ev = ExteriorLaneRouteEvidence(
        candidate_id="c0",
        lane_id="exterior_lane:shape_belt:0",
        candidate_throughput_per_min=Decimal("480"),
        branch_cells=((0, 1),),
        reused_trunk_cells=(),
        new_trunk_cells=((1, 1), (1, 2)),
        reached_connector_coord=(1, 5),
        reached_trunk_coord=None,
    )
    assert ev.branch_cells == ((0, 1),)


def test_activation_evidence_fields() -> None:
    ev = ExteriorLaneActivationEvidence(
        activated_lane_id="exterior_lane:shape_belt:1",
        previous_lane_id="exterior_lane:shape_belt:0",
        previous_lane_assigned_load_per_min=Decimal("2880"),
        previous_lane_capacity_per_min=Decimal("2880"),
        trigger_candidate_id="c9",
        trigger_candidate_throughput_per_min=Decimal("480"),
        activation_reason=ACTIVATION_REASON_CAPACITY_EXHAUSTED,
    )
    assert ev.activation_reason == "capacity_exhausted"
