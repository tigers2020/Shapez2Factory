"""EVTC saturated exterior transport caps — reads game_data CANON only."""

from __future__ import annotations

from decimal import Decimal

from django_apps.asteroid_lab.contracts.rttp_exterior_throughput_tier import (
    ExteriorThroughputTier,
)
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.services.rttp_exterior_transport_configuration import (
    ExteriorTransportCapacityConfigurationError,
)
from django_apps.game_data.services.exterior_transport_capacity import (
    get_active_exterior_fluid_transport_capacity,
    get_active_exterior_shape_transport_capacity,
    space_belt_max_per_min_from_row,
    space_pipe_max_per_min_from_row,
)


def space_belt_max_per_min(
    tier: ExteriorThroughputTier = ExteriorThroughputTier.TIER_1,
) -> Decimal:
    try:
        row = get_active_exterior_shape_transport_capacity(speed_tier=int(tier))
    except LookupError as exc:
        msg = f"no active exterior transport capacity for shape " f"speed_tier={int(tier)!r}: {exc}"
        raise ExteriorTransportCapacityConfigurationError(msg) from exc
    return space_belt_max_per_min_from_row(row)


def space_pipe_max_per_min(
    tier: ExteriorThroughputTier = ExteriorThroughputTier.TIER_1,
) -> Decimal:
    try:
        row = get_active_exterior_fluid_transport_capacity(speed_tier=int(tier))
    except LookupError as exc:
        msg = f"no active exterior transport capacity for fluid " f"speed_tier={int(tier)!r}: {exc}"
        raise ExteriorTransportCapacityConfigurationError(msg) from exc
    return space_pipe_max_per_min_from_row(row)


def transport_max_throughput_per_min(
    transport_kind: TransportKind,
    *,
    tier: ExteriorThroughputTier = ExteriorThroughputTier.TIER_1,
) -> Decimal:
    if transport_kind is TransportKind.SHAPE_BELT:
        return space_belt_max_per_min(tier)
    if transport_kind is TransportKind.FLUID_PIPE:
        return space_pipe_max_per_min(tier)
    msg = f"unsupported transport_kind for EVTC denominator: {transport_kind!r}"
    raise ValueError(msg)


__all__ = [
    "space_belt_max_per_min",
    "space_pipe_max_per_min",
    "transport_max_throughput_per_min",
]
