"""Layer 2 exterior transport ??builds ExteriorConnectionPlan from complete map."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.plan import (
    build_exterior_connection_plan,
)
from shapez2_factory.application.asteroid_lab.ports.game_data_rules import GameDataRulesPort
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)


def execute_layer_02_exterior_transport_plan(
    *,
    complete_map: ReconstructionCompleteMap,
    capacity_envelope: dict[str, Any],
    throughput_target_percent: int,
    speed_tier: int = 1,
    rules: GameDataRulesPort,
) -> ExteriorConnectionPlan:
    """Run Layer 02 planning (pure; no I/O)."""

    primary = str(capacity_envelope.get("primary_resource_kind") or "shape")
    by_resource = dict(capacity_envelope.get("by_resource") or {})
    resource_row = dict(by_resource.get(primary) or {})
    terrain_raw = resource_row.get("max_throughput_per_min", "0")
    try:
        terrain_upper_bound = Decimal(str(terrain_raw))
    except (InvalidOperation, ValueError):
        terrain_upper_bound = Decimal(0)

    return build_exterior_connection_plan(
        complete_map=complete_map,
        resource_kind=primary,
        terrain_upper_bound_per_min=terrain_upper_bound,
        throughput_target_percent=throughput_target_percent,
        speed_tier=speed_tier,
        rules=rules,
    )


def run_layer_02_exterior_transport(
    *,
    complete_map: ReconstructionCompleteMap,
    budget_ctx: LayerBudgetContext,
    capacity_envelope: dict[str, Any] | None = None,
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
