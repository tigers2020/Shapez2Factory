"""EVTC capacity resolution for Layer 02.

Decoupled from ``django_apps.game_data`` ORM (PR-CLI-2b): the per-connector capacity is read from an
injected ``GameDataRulesPort`` (core), satisfied by a frozen snapshot adapter or the ORM-backed
adapter. A missing row surfaces as ``MISSING_EVTC_ROW``; the capacity formula stays in game_data.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionShortfallReason,
)
from shapez2_factory.application.asteroid_lab.ports.game_data_rules import GameDataRulesPort


@dataclass(frozen=True, slots=True)
class CapacityResolution:
    capacity_per_min: Decimal | None
    shortfall_reason: ExteriorConnectionShortfallReason | None


def resolve_per_connector_capacity(
    *,
    rules: GameDataRulesPort,
    resource_kind: str,
    speed_tier: int,
) -> CapacityResolution:
    try:
        row = rules.exterior_connector_capacity(
            resource_kind=resource_kind,
            speed_tier=speed_tier,
        )
    except LookupError:
        return CapacityResolution(
            capacity_per_min=None,
            shortfall_reason=ExteriorConnectionShortfallReason.MISSING_EVTC_ROW,
        )

    return CapacityResolution(
        capacity_per_min=row.per_connector_capacity_per_min,
        shortfall_reason=None,
    )


__all__ = ["CapacityResolution", "resolve_per_connector_capacity"]
