"""Build ExteriorConnectionPlan from reconstruction-complete map + throughput target."""

from __future__ import annotations

from decimal import Decimal

from django_apps.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from django_apps.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
    ExteriorConnectionShortfallReason,
    ExteriorConnector,
)
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.capacity import (
    resolve_per_connector_capacity,
)
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.layout_t import (
    default_exterior_connector_layout_t,
)
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.placement import (
    choose_even_slots,
    distribute_connector_counts,
)
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.rotation import (
    FIELDWARD_ROTATION_BY_EDGE,
)
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.slots import (
    build_candidate_slots_by_edge,
)
from django_apps.asteroid_lab.layers.shared.ceildiv import ceildiv_decimal
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap

_EDGES_ORDER: tuple[CardinalEdge, ...] = (
    CardinalEdge.NORTH,
    CardinalEdge.EAST,
    CardinalEdge.SOUTH,
    CardinalEdge.WEST,
)


def build_exterior_connection_plan(
    *,
    complete_map: ReconstructionCompleteMap,
    resource_kind: str,
    terrain_upper_bound_per_min: Decimal,
    throughput_target_percent: int,
    speed_tier: int = 1,
) -> ExteriorConnectionPlan:
    cap_res = resolve_per_connector_capacity(resource_kind=resource_kind, speed_tier=speed_tier)
    planning_target = (
        terrain_upper_bound_per_min * Decimal(throughput_target_percent) / Decimal(100)
    )

    if cap_res.shortfall_reason is not None or cap_res.capacity_per_min is None:
        return _empty_plan(
            transport_kind=resource_kind,
            terrain_upper_bound_per_min=terrain_upper_bound_per_min,
            planning_target_per_min=planning_target,
            per_connector_capacity_per_min=Decimal(0),
            required_connector_count=0,
            unmet_reason=cap_res.shortfall_reason
            or ExteriorConnectionShortfallReason.MISSING_EVTC_ROW,
        )

    required = ceildiv_decimal(planning_target, cap_res.capacity_per_min)
    edge_slots = build_candidate_slots_by_edge(complete_map)
    total_slots = sum(len(slots) for slots in edge_slots.values())

    if total_slots < required:
        return _empty_plan(
            transport_kind=resource_kind,
            terrain_upper_bound_per_min=terrain_upper_bound_per_min,
            planning_target_per_min=planning_target,
            per_connector_capacity_per_min=cap_res.capacity_per_min,
            required_connector_count=required,
            unmet_reason=ExteriorConnectionShortfallReason.NO_FEASIBLE_CONNECTOR_SITES,
        )

    counts = distribute_connector_counts(required, edge_slots)
    connectors: list[ExteriorConnector] = []
    seq = 0
    for edge in _EDGES_ORDER:
        chosen = choose_even_slots(edge_slots[edge], counts[edge])
        for void_coord in chosen:
            connectors.append(
                ExteriorConnector(
                    connector_id=f"ext_conn_{seq:02d}",
                    void_coord=void_coord,
                    edge=edge,
                    layout_t=default_exterior_connector_layout_t(resource_kind=resource_kind),
                    rotation=FIELDWARD_ROTATION_BY_EDGE[edge],
                    capacity_per_min=cap_res.capacity_per_min,
                    coords=(void_coord,),
                )
            )
            seq += 1

    return ExteriorConnectionPlan(
        transport_kind=resource_kind,
        terrain_upper_bound_per_min=terrain_upper_bound_per_min,
        planning_target_per_min=planning_target,
        per_connector_capacity_per_min=cap_res.capacity_per_min,
        required_connector_count=required,
        planned_connectors=tuple(connectors),
        unmet_reason=None,
    )


def _empty_plan(
    *,
    transport_kind: str,
    terrain_upper_bound_per_min: Decimal,
    planning_target_per_min: Decimal,
    per_connector_capacity_per_min: Decimal,
    required_connector_count: int,
    unmet_reason: ExteriorConnectionShortfallReason,
) -> ExteriorConnectionPlan:
    return ExteriorConnectionPlan(
        transport_kind=transport_kind,
        terrain_upper_bound_per_min=terrain_upper_bound_per_min,
        planning_target_per_min=planning_target_per_min,
        per_connector_capacity_per_min=per_connector_capacity_per_min,
        required_connector_count=required_connector_count,
        planned_connectors=(),
        unmet_reason=unmet_reason,
    )


__all__ = ["build_exterior_connection_plan"]
