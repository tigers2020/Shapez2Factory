"""Shim: relocated to the core layer_02_exterior_transport.run module.

Relocated to
``shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.run``.
Adds the ORM-backed GameDataRulesPort default so existing Django callers keep working.
"""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.run import (
    execute_layer_02_exterior_transport_plan as _core_execute_layer_02_exterior_transport_plan,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.run import (
    run_layer_02_exterior_transport as _core_run_layer_02_exterior_transport,
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
    rules: GameDataRulesPort | None = None,
) -> ExteriorConnectionPlan:
    if rules is None:
        from django_apps.asteroid_lab.adapters.orm_game_data_rules import build_orm_game_data_rules

        rules = build_orm_game_data_rules()
    return _core_execute_layer_02_exterior_transport_plan(
        complete_map=complete_map,
        capacity_envelope=capacity_envelope,
        throughput_target_percent=throughput_target_percent,
        speed_tier=speed_tier,
        rules=rules,
    )


def run_layer_02_exterior_transport(
    *,
    complete_map: ReconstructionCompleteMap,
    budget_ctx: LayerBudgetContext,
    capacity_envelope: dict[str, object] | None = None,
    throughput_target_percent: int | None = None,
    speed_tier: int = 1,
    rules: GameDataRulesPort | None = None,
) -> ExteriorConnectionPlan | None:
    # Stub-hold short-circuit before resolving rules: keeps the no-input path free of ORM/DB
    # access (behavior-preserving), since core would return None here regardless.
    if capacity_envelope is None or throughput_target_percent is None:
        return None
    if rules is None:
        from django_apps.asteroid_lab.adapters.orm_game_data_rules import build_orm_game_data_rules

        rules = build_orm_game_data_rules()
    return _core_run_layer_02_exterior_transport(
        complete_map=complete_map,
        budget_ctx=budget_ctx,
        capacity_envelope=capacity_envelope,
        throughput_target_percent=throughput_target_percent,
        speed_tier=speed_tier,
        rules=rules,
    )


__all__ = [
    "execute_layer_02_exterior_transport_plan",
    "run_layer_02_exterior_transport",
]
