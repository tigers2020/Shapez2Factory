"""ELCP — build static exterior lane capacity plan from EVTC connector goals."""

from __future__ import annotations

from decimal import Decimal

from django_apps.asteroid_lab.contracts.exterior_lane_capacity import (
    ExteriorLaneCapacityPlan,
    ExteriorTransportLane,
)
from django_apps.asteroid_lab.contracts.rttp_exterior_throughput_tier import (
    ExteriorThroughputTier,
)
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput, TransportKind
from django_apps.asteroid_lab.optimization.routing.exterior_connector_planner import (
    plan_exterior_connectors,
)
from django_apps.asteroid_lab.optimization.routing.exterior_lane_capacity_helpers import (
    lane_target_loads_per_min,
    normalize_required_lane_count,
)
from django_apps.asteroid_lab.services.rttp_exterior_transport_resolver import (
    transport_max_throughput_per_min,
)


def build_exterior_lane_capacity_plan(
    inp: OptimizationInput,
    *,
    max_asteroid_throughput_per_min: Decimal,
    transport_kind: TransportKind,
    tier: ExteriorThroughputTier = ExteriorThroughputTier.TIER_1,
) -> ExteriorLaneCapacityPlan:
    """Plan capacity-bearing exterior lanes (reuses EVTC connector goal selection)."""

    lane_capacity = transport_max_throughput_per_min(transport_kind, tier=tier)
    required = normalize_required_lane_count(
        max_asteroid_throughput_per_min=max_asteroid_throughput_per_min,
        lane_capacity_per_min=lane_capacity,
    )
    connector_plan = plan_exterior_connectors(
        inp,
        required_count=required,
        transport_kind=transport_kind,
    )
    target_loads = lane_target_loads_per_min(
        max_asteroid_throughput_per_min=max_asteroid_throughput_per_min,
        lane_capacity_per_min=lane_capacity,
        required_lane_count=required,
    )
    lanes: list[ExteriorTransportLane] = []
    for index, goal in enumerate(connector_plan.selected_goals):
        lane_id = f"exterior_lane:{transport_kind.value}:{index}"
        lanes.append(
            ExteriorTransportLane(
                lane_id=lane_id,
                transport_kind=transport_kind,
                connector_goal=goal,
                capacity_per_min=lane_capacity,
                target_load_per_min=target_loads[index],
                anchor_coord=goal.coord,
            )
        )
    return ExteriorLaneCapacityPlan(
        transport_kind=transport_kind,
        max_asteroid_throughput_per_min=max_asteroid_throughput_per_min,
        lane_capacity_per_min=lane_capacity,
        required_lane_count=required,
        lanes=tuple(lanes),
    )


__all__ = ["build_exterior_lane_capacity_plan"]
