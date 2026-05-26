"""Queryable EVTC exterior transport caps. Runtime SoT — no RTTP imports."""

from __future__ import annotations

from decimal import Decimal
from typing import cast

from django_apps.game_data.models.exterior_transport_capacity import (
    ExteriorFluidTransportCapacity,
    ExteriorShapeTransportCapacity,
)

EVTC_SPEC_NOTE = (
    "docs/superpowers/specs/2026-05-26-rttp-external-void-transport-capacity-contract.md"
)


def get_active_exterior_shape_transport_capacity(
    *,
    speed_tier: int = 1,
) -> ExteriorShapeTransportCapacity:
    row = ExteriorShapeTransportCapacity.objects.filter(
        speed_tier=speed_tier,
        is_active=True,
    ).first()
    if row is None:
        msg = f"no active ExteriorShapeTransportCapacity for speed_tier={speed_tier!r}"
        raise LookupError(msg)
    return row


def get_active_exterior_fluid_transport_capacity(
    *,
    speed_tier: int = 1,
) -> ExteriorFluidTransportCapacity:
    row = ExteriorFluidTransportCapacity.objects.filter(
        speed_tier=speed_tier,
        is_active=True,
    ).first()
    if row is None:
        msg = f"no active ExteriorFluidTransportCapacity for speed_tier={speed_tier!r}"
        raise LookupError(msg)
    return row


def space_belt_max_per_min_from_row(row: ExteriorShapeTransportCapacity) -> Decimal:
    regular = cast(
        Decimal,
        row.mini_unit_output_per_min * Decimal(row.buildings_per_regular_belt),
    )
    return cast(
        Decimal,
        regular * Decimal(row.space_belt_full_belt_count),
    )


def space_pipe_max_per_min_from_row(row: ExteriorFluidTransportCapacity) -> Decimal:
    return cast(
        Decimal,
        row.fluid_launcher_output_per_min * Decimal(row.space_pipe_full_fluid_launcher_count),
    )
