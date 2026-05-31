"""Build ExteriorConnectionPlan from reconstruction-complete map + throughput target."""

from __future__ import annotations

from decimal import Decimal

from shapez2_factory.application.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
    ExteriorConnectionShortfallReason,
    ExteriorConnector,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.capacity import (
    resolve_per_connector_capacity,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.layout_t import (
    default_exterior_connector_layout_t,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.placement import (
    choose_even_slots,
    distribute_connector_counts,
    remaining_slots_after_selection,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.rotation import (
    FIELDWARD_ROTATION_BY_EDGE,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.slots import (
    build_candidate_slots_by_edge,
)
from shapez2_factory.application.asteroid_lab.layers.shared.ceildiv import ceildiv_decimal
from shapez2_factory.application.asteroid_lab.ports.game_data_rules import GameDataRulesPort
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)

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
    rules: GameDataRulesPort,
) -> ExteriorConnectionPlan:
    cap_res = resolve_per_connector_capacity(
        rules=rules,
        resource_kind=resource_kind,
        speed_tier=speed_tier,
    )
    planning_target = (
        terrain_upper_bound_per_min * Decimal(throughput_target_percent) / Decimal(100)
    )

    if cap_res.shortfall_reason is not None or cap_res.capacity_per_min is None:
        return _empty_plan(
            transport_kind=resource_kind,
            terrain_upper_bound_per_min=terrain_upper_bound_per_min,
            planning_target_per_min=planning_target,
            per_connector_capacity_per_min=Decimal(0),
            reference_connector_count=0,
            required_connector_count=0,
            spare_connector_count=0,
            unmet_reason=cap_res.shortfall_reason
            or ExteriorConnectionShortfallReason.MISSING_EVTC_ROW,
        )

    reference = ceildiv_decimal(terrain_upper_bound_per_min, cap_res.capacity_per_min)
    required = ceildiv_decimal(planning_target, cap_res.capacity_per_min)
    spare = max(0, reference - required)
    edge_slots = build_candidate_slots_by_edge(complete_map)
    total_slots = sum(len(slots) for slots in edge_slots.values())

    if total_slots == 0:
        return _empty_plan(
            transport_kind=resource_kind,
            terrain_upper_bound_per_min=terrain_upper_bound_per_min,
            planning_target_per_min=planning_target,
            per_connector_capacity_per_min=cap_res.capacity_per_min,
            reference_connector_count=reference,
            required_connector_count=required,
            spare_connector_count=spare,
            unmet_reason=ExteriorConnectionShortfallReason.NO_FEASIBLE_CONNECTOR_SITES,
        )

    required_to_place = min(required, total_slots)
    connectors = _place_connectors_for_role(
        resource_kind=resource_kind,
        edge_slots=edge_slots,
        count=required_to_place,
        capacity_per_min=cap_res.capacity_per_min,
        role=ExteriorConnectorRole.REQUIRED,
        seq_start=0,
    )
    seq = len(connectors)

    if spare > 0:
        used = {c.void_coord for c in connectors}
        remaining = remaining_slots_after_selection(edge_slots, used)
        remaining_total = sum(len(slots) for slots in remaining.values())
        spare_to_place = min(spare, remaining_total)
        if spare_to_place > 0:
            connectors.extend(
                _place_connectors_for_role(
                    resource_kind=resource_kind,
                    edge_slots=remaining,
                    count=spare_to_place,
                    capacity_per_min=cap_res.capacity_per_min,
                    role=ExteriorConnectorRole.SPARE,
                    seq_start=seq,
                )
            )

    unmet_reason: ExteriorConnectionShortfallReason | None = None
    if required_to_place < required:
        unmet_reason = ExteriorConnectionShortfallReason.INSUFFICIENT_CONNECTOR_SITES

    return ExteriorConnectionPlan(
        transport_kind=resource_kind,
        terrain_upper_bound_per_min=terrain_upper_bound_per_min,
        planning_target_per_min=planning_target,
        per_connector_capacity_per_min=cap_res.capacity_per_min,
        required_connector_count=required,
        reference_connector_count=reference,
        spare_connector_count=spare,
        planned_connectors=tuple(connectors),
        unmet_reason=unmet_reason,
        candidate_slot_count=total_slots,
    )


def _place_connectors_for_role(
    *,
    resource_kind: str,
    edge_slots: dict[CardinalEdge, list[Coord]],
    count: int,
    capacity_per_min: Decimal,
    role: ExteriorConnectorRole,
    seq_start: int,
) -> list[ExteriorConnector]:
    if count <= 0:
        return []

    counts = distribute_connector_counts(count, edge_slots)
    connectors: list[ExteriorConnector] = []
    seq = seq_start
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
                    capacity_per_min=capacity_per_min,
                    coords=(void_coord,),
                    role=role,
                )
            )
            seq += 1
    return connectors


def _empty_plan(
    *,
    transport_kind: str,
    terrain_upper_bound_per_min: Decimal,
    planning_target_per_min: Decimal,
    per_connector_capacity_per_min: Decimal,
    reference_connector_count: int,
    required_connector_count: int,
    spare_connector_count: int,
    unmet_reason: ExteriorConnectionShortfallReason,
) -> ExteriorConnectionPlan:
    return ExteriorConnectionPlan(
        transport_kind=transport_kind,
        terrain_upper_bound_per_min=terrain_upper_bound_per_min,
        planning_target_per_min=planning_target_per_min,
        per_connector_capacity_per_min=per_connector_capacity_per_min,
        required_connector_count=required_connector_count,
        reference_connector_count=reference_connector_count,
        spare_connector_count=spare_connector_count,
        planned_connectors=(),
        unmet_reason=unmet_reason,
    )


__all__ = ["build_exterior_connection_plan"]
