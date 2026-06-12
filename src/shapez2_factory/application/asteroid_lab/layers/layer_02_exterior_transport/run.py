"""Layer 2 exterior transport ??builds ExteriorConnectionPlan from complete map."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.plan import (
    build_exterior_connection_plan,
    merge_exterior_connection_plans,
)
from shapez2_factory.application.asteroid_lab.ports.game_data_rules import GameDataRulesPort
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.resource_kinds import (
    detect_present_resource_kinds,
)
from shapez2_factory.domain.asteroid_lab.wire_coerce import wire_dict, wire_str


def execute_layer_02_exterior_transport_plan(
    *,
    complete_map: ReconstructionCompleteMap,
    capacity_envelope: dict[str, object],
    throughput_target_percent: int,
    speed_tier: int = 1,
    rules: GameDataRulesPort,
) -> ExteriorConnectionPlan:
    """Run Layer 02 planning (pure; no I/O)."""

    primary = wire_str(capacity_envelope.get("primary_resource_kind"), default="shape")
    by_resource = wire_dict(capacity_envelope.get("by_resource", {}))
    envelope_present = capacity_envelope.get("present_resource_kinds")
    if isinstance(envelope_present, (list, tuple)) and envelope_present:
        resource_kinds = tuple(wire_str(kind) for kind in envelope_present)
    else:
        resource_kinds = detect_present_resource_kinds(complete_map)
    if not resource_kinds:
        resource_kinds = (primary,)

    plans: list[ExteriorConnectionPlan] = []
    for resource_kind in resource_kinds:
        resource_row = wire_dict(by_resource.get(resource_kind, {}))
        terrain_raw = resource_row.get("max_throughput_per_min", "0")
        try:
            terrain_upper_bound = Decimal(str(terrain_raw))
        except (InvalidOperation, ValueError):
            terrain_upper_bound = Decimal(0)
        plans.append(
            build_exterior_connection_plan(
                complete_map=complete_map,
                resource_kind=resource_kind,
                terrain_upper_bound_per_min=terrain_upper_bound,
                throughput_target_percent=throughput_target_percent,
                speed_tier=speed_tier,
                rules=rules,
            )
        )

    return merge_exterior_connection_plans(
        tuple(plans),
        primary_resource_kind=primary,
    )


def run_layer_02_exterior_transport(
    *,
    complete_map: ReconstructionCompleteMap,
    budget_ctx: LayerBudgetContext,
    capacity_envelope: dict[str, object] | None = None,
    throughput_target_percent: int | None = None,
    speed_tier: int = 1,
    rules: GameDataRulesPort,
) -> ExteriorConnectionPlan | None:
    """Stack runner entry; returns None when planning inputs are not provided (stub hold)."""

    _ = budget_ctx
    if capacity_envelope is None or throughput_target_percent is None:
        return None
    return execute_layer_02_exterior_transport_plan(
        complete_map=complete_map,
        capacity_envelope=capacity_envelope,
        throughput_target_percent=throughput_target_percent,
        speed_tier=speed_tier,
        rules=rules,
    )


__all__ = [
    "execute_layer_02_exterior_transport_plan",
    "run_layer_02_exterior_transport",
]
