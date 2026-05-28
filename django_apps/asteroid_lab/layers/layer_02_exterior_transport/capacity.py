"""EVTC capacity resolution for Layer 02 (current-master service wrappers)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django_apps.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionShortfallReason,
)
from django_apps.game_data.services.exterior_transport_capacity import (
    get_active_exterior_fluid_transport_capacity,
    get_active_exterior_shape_transport_capacity,
    space_belt_connector_capacity_per_min_from_row,
    space_pipe_max_per_min_from_row,
)


@dataclass(frozen=True, slots=True)
class CapacityResolution:
    capacity_per_min: Decimal | None
    shortfall_reason: ExteriorConnectionShortfallReason | None


def resolve_per_connector_capacity(
    *,
    resource_kind: str,
    speed_tier: int,
) -> CapacityResolution:
    try:
        if resource_kind == "fluid":
            fluid_row = get_active_exterior_fluid_transport_capacity(speed_tier=speed_tier)
            cap = space_pipe_max_per_min_from_row(fluid_row)
        else:
            shape_row = get_active_exterior_shape_transport_capacity(speed_tier=speed_tier)
            cap = space_belt_connector_capacity_per_min_from_row(shape_row)
    except LookupError:
        return CapacityResolution(
            capacity_per_min=None,
            shortfall_reason=ExteriorConnectionShortfallReason.MISSING_EVTC_ROW,
        )

    return CapacityResolution(capacity_per_min=cap, shortfall_reason=None)


__all__ = ["CapacityResolution", "resolve_per_connector_capacity"]
