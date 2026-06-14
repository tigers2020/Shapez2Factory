"""Queryable EVTC exterior transport caps. Runtime SoT — no RTTP imports."""

from __future__ import annotations

from decimal import ROUND_CEILING, Decimal
from typing import cast

from django_apps.game_data.models.exterior_transport_capacity import (
    ExteriorFluidTransportCapacity,
    ExteriorShapeTransportCapacity,
)

EVTC_SPEC_NOTE = (
    "documents/superpowers/specs/2026-05-26-rttp-external-void-transport-capacity-contract.md"
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


def inner_belt_throughput_per_min_from_row(row: ExteriorShapeTransportCapacity) -> Decimal:
    """Inner belt: mini_unit × buildings_per_regular_belt (tier-1: 30×4 = 120/min)."""

    return cast(
        Decimal,
        row.mini_unit_output_per_min * Decimal(row.buildings_per_regular_belt),
    )


def regular_belt_throughput_per_min_from_row(row: ExteriorShapeTransportCapacity) -> Decimal:
    """Alias for inner-belt throughput (legacy name)."""

    return inner_belt_throughput_per_min_from_row(row)


def full_miner_output_per_min_from_row(row: ExteriorShapeTransportCapacity) -> Decimal:
    """Full mini miner: mini_unit × miner_full_output_multiplier (tier-1: 30×16 = 480/min)."""

    return cast(
        Decimal,
        row.mini_unit_output_per_min * Decimal(row.miner_full_output_multiplier),
    )


def line_throughput_per_min_from_row(row: ExteriorShapeTransportCapacity) -> Decimal:
    """One exterior Space Belt line at full miner export (tier-1: 480 shapes/min)."""

    return full_miner_output_per_min_from_row(row)


def space_belt_connector_capacity_per_min_from_row(row: ExteriorShapeTransportCapacity) -> Decimal:
    """One Space Belt building: ``line × lines_per_space_belt`` (tier-1: 480×12 = 5760/min)."""

    return cast(
        Decimal,
        line_throughput_per_min_from_row(row) * Decimal(row.lines_per_space_belt),
    )


def space_belt_max_per_min_from_row(row: ExteriorShapeTransportCapacity) -> Decimal:
    """Wiki cap: inner_belt × space_belt_full_belt_count (tier-1: 120×48 = 5760/min)."""

    inner = inner_belt_throughput_per_min_from_row(row)
    return cast(
        Decimal,
        inner * Decimal(row.space_belt_full_belt_count),
    )


def space_pipe_max_per_min_from_row(row: ExteriorFluidTransportCapacity) -> Decimal:
    return cast(
        Decimal,
        row.fluid_launcher_output_per_min * Decimal(row.space_pipe_full_fluid_launcher_count),
    )


def exterior_line_throughput_per_min(
    *,
    resource_kind: str,
    speed_tier: int = 1,
) -> Decimal:
    if resource_kind != "shape":
        msg = f"exterior_line_throughput_per_min unsupported for {resource_kind!r}"
        raise ValueError(msg)
    row = get_active_exterior_shape_transport_capacity(speed_tier=speed_tier)
    return line_throughput_per_min_from_row(row)


def exterior_connector_capacity_per_min(
    *,
    resource_kind: str,
    speed_tier: int = 1,
) -> Decimal:
    """Per-building Space Belt or saturated Space Pipe cap for connector sizing."""

    if resource_kind == "fluid":
        row = get_active_exterior_fluid_transport_capacity(speed_tier=speed_tier)
        return space_pipe_max_per_min_from_row(row)
    row = get_active_exterior_shape_transport_capacity(speed_tier=speed_tier)
    return space_belt_connector_capacity_per_min_from_row(row)


def exterior_line_count_for_throughput(
    max_throughput_per_min: Decimal,
    *,
    resource_kind: str,
    speed_tier: int = 1,
) -> int:
    """``ceil(max_throughput / line_throughput)``; shape only."""

    if max_throughput_per_min <= 0:
        return 0
    line = exterior_line_throughput_per_min(
        resource_kind=resource_kind,
        speed_tier=speed_tier,
    )
    if line <= 0:
        return 0
    return int((max_throughput_per_min / line).to_integral_value(rounding=ROUND_CEILING))


def exterior_connector_count_for_throughput(
    max_throughput_per_min: Decimal,
    *,
    resource_kind: str,
    speed_tier: int = 1,
) -> int:
    """``ceil(max_throughput / per_building_connector_capacity)``; 0 when throughput ≤ 0."""

    if max_throughput_per_min <= 0:
        return 0
    cap = exterior_connector_capacity_per_min(
        resource_kind=resource_kind,
        speed_tier=speed_tier,
    )
    if cap <= 0:
        return 0
    return int(
        (max_throughput_per_min / cap).to_integral_value(rounding=ROUND_CEILING),
    )
