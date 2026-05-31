"""Terrain upper-bound capacity from mining extraction (shared Django L1 + CLI run_stack)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

FIELD_CELL_MINI_UNITS = 4
VALID_THROUGHPUT_FACTORS: frozenset[int] = frozenset({4, 8, 12, 16})


def decimal_str(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.0001")), "f")


def effective_mini_units(extension_count: int) -> int:
    if extension_count < 0 or extension_count > 3:
        msg = "extension_count must be in 0..3"
        raise ValueError(msg)
    return 4 + 4 * extension_count


def output_per_min_from_mini_unit(
    mini_unit_output_per_min: Decimal,
    throughput_factor: int,
) -> Decimal:
    if throughput_factor not in VALID_THROUGHPUT_FACTORS:
        msg = f"throughput_factor must be one of {sorted(VALID_THROUGHPUT_FACTORS)}"
        raise ValueError(msg)
    return mini_unit_output_per_min * Decimal(throughput_factor)


def build_terrain_capacity_summary_row(
    *,
    resource_kind: str,
    platform_count: int,
    mini_unit_output_per_min: Decimal,
    output_unit: str,
    max_extension_count: int,
    source_kind: str,
    authority: str,
) -> dict[str, Any]:
    """Terrain upper bound: one field cell = one platform at base ×4 mini-units (not ×16)."""

    per_cell = output_per_min_from_mini_unit(
        mini_unit_output_per_min,
        FIELD_CELL_MINI_UNITS,
    )
    total = per_cell * Decimal(platform_count)
    max_mini_bundle = effective_mini_units(max_extension_count)
    max_per_miner = output_per_min_from_mini_unit(
        mini_unit_output_per_min,
        max_mini_bundle,
    )
    return {
        "resource_kind": resource_kind,
        "capacity_upper_bound_platform_count": platform_count,
        "mini_units_per_confirmed_cell": FIELD_CELL_MINI_UNITS,
        "capacity_upper_bound_mini_units": platform_count * FIELD_CELL_MINI_UNITS,
        "mini_unit_output_per_min": decimal_str(mini_unit_output_per_min),
        "output_per_confirmed_cell": decimal_str(per_cell),
        "max_mini_units_per_miner": max_mini_bundle,
        "max_output_per_miner": decimal_str(max_per_miner),
        "max_throughput_per_min": decimal_str(total),
        "output_unit": output_unit,
        "source_kind": source_kind,
        "authority": authority,
    }


__all__ = [
    "FIELD_CELL_MINI_UNITS",
    "VALID_THROUGHPUT_FACTORS",
    "build_terrain_capacity_summary_row",
    "decimal_str",
    "effective_mini_units",
    "output_per_min_from_mini_unit",
]
