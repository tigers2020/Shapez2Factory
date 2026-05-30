"""Shim: relocated to the core layer_02_exterior_transport.plan module.

Relocated to
``shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.plan``.
Adds the ORM-backed GameDataRulesPort default so existing Django callers keep working.
"""

from __future__ import annotations

from decimal import Decimal

from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.plan import (
    build_exterior_connection_plan as _core_build_exterior_connection_plan,
)
from shapez2_factory.application.asteroid_lab.ports.game_data_rules import GameDataRulesPort
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)


def build_exterior_connection_plan(
    *,
    complete_map: ReconstructionCompleteMap,
    resource_kind: str,
    terrain_upper_bound_per_min: Decimal,
    throughput_target_percent: int,
    speed_tier: int = 1,
    rules: GameDataRulesPort | None = None,
) -> ExteriorConnectionPlan:
    if rules is None:
        from django_apps.asteroid_lab.adapters.orm_game_data_rules import build_orm_game_data_rules

        rules = build_orm_game_data_rules()
    return _core_build_exterior_connection_plan(
        complete_map=complete_map,
        resource_kind=resource_kind,
        terrain_upper_bound_per_min=terrain_upper_bound_per_min,
        throughput_target_percent=throughput_target_percent,
        speed_tier=speed_tier,
        rules=rules,
    )


__all__ = ["build_exterior_connection_plan"]
