"""Layer 2 skeleton — algorithm reset (contracts preserved; no planning)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.ports.game_data_rules import GameDataRulesPort
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)


def execute_layer_02_exterior_transport_plan(
    *,
    complete_map: ReconstructionCompleteMap,
    capacity_envelope: dict[str, object],
    throughput_target_percent: int,
    speed_tier: int = 1,
    rules: GameDataRulesPort,
) -> ExteriorConnectionPlan | None:
    _ = (
        complete_map,
        capacity_envelope,
        throughput_target_percent,
        speed_tier,
        rules,
    )
    return None


def run_layer_02_exterior_transport(
    *,
    complete_map: ReconstructionCompleteMap,
    budget_ctx: LayerBudgetContext,
    capacity_envelope: dict[str, object] | None = None,
    throughput_target_percent: int | None = None,
    speed_tier: int = 1,
    rules: GameDataRulesPort | None = None,
) -> ExteriorConnectionPlan | None:
    _ = (complete_map, budget_ctx, capacity_envelope, throughput_target_percent, speed_tier, rules)
    return None


__all__ = [
    "execute_layer_02_exterior_transport_plan",
    "run_layer_02_exterior_transport",
]
