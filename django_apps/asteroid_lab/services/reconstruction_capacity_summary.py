"""Reconstruction terrain upper-bound capacity (output-only; never solver input)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django_apps.asteroid_lab.reconstruction.acceptance_topology import (
    acceptance_topology_from_complete_map,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.reconstruction.field_cells import (
    count_asteroid_field_cells_by_resource,
    detect_primary_resource_kind,
)
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.game_data.services.mining_extraction_rules import (
    effective_mini_units,
    get_active_rule,
    max_output_per_miner,
    output_per_min,
)

# One asteroid field cell = one installation slot at ×4 mini-units (not ×16 bundle).
_FIELD_CELL_MINI_UNITS = 4


def decimal_str(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.0001")), "f")


def _json_safe_source_kind(rule: object) -> str:
    raw = getattr(rule, "source_kind", "")
    return str(getattr(raw, "value", raw))


def build_reconstruction_capacity_summary(
    *,
    complete_map: ReconstructionCompleteMap,
    resource_kind: str,
) -> dict[str, Any]:
    """Terrain upper bound; platform count from complete map field cells only."""

    rule = get_active_rule(resource_kind)
    if resource_kind == "shape":
        platform_count = complete_map.shape_field_cell_count
    else:
        platform_count = complete_map.fluid_field_cell_count
    per_cell = output_per_min(rule, _FIELD_CELL_MINI_UNITS)
    total = per_cell * Decimal(platform_count)
    max_mini_bundle = effective_mini_units(int(rule.max_extension_count))
    return {
        "resource_kind": resource_kind,
        "capacity_upper_bound_platform_count": platform_count,
        "mini_units_per_confirmed_cell": _FIELD_CELL_MINI_UNITS,
        "capacity_upper_bound_mini_units": platform_count * _FIELD_CELL_MINI_UNITS,
        "mini_unit_output_per_min": decimal_str(rule.mini_unit_output_per_min),
        "output_per_confirmed_cell": decimal_str(per_cell),
        "max_mini_units_per_miner": max_mini_bundle,
        "max_output_per_miner": decimal_str(max_output_per_miner(rule)),
        "max_throughput_per_min": decimal_str(total),
        "output_unit": rule.output_unit,
        "source_kind": _json_safe_source_kind(rule),
        "authority": "MiningExtractionRule",
    }


def build_reconstruction_capacity_envelope(
    *,
    complete_map: ReconstructionCompleteMap,
) -> dict[str, Any]:
    by_resource = count_asteroid_field_cells_by_resource(complete_map)
    return {
        "capacity_basis": "terrain_upper_bound",
        "primary_resource_kind": detect_primary_resource_kind(complete_map),
        "confirmed_platforms_by_resource": dict(by_resource),
        "by_resource": {
            "shape": build_reconstruction_capacity_summary(
                complete_map=complete_map,
                resource_kind="shape",
            ),
            "fluid": build_reconstruction_capacity_summary(
                complete_map=complete_map,
                resource_kind="fluid",
            ),
        },
    }


def build_reconstruction_observability(
    *,
    recon: ReconstructionResult,
    complete_map: ReconstructionCompleteMap,
) -> dict[str, Any]:
    topo = acceptance_topology_from_complete_map(complete_map)
    field_total = len(complete_map.field_cells)
    obs: dict[str, Any] = {
        "cell_count": len(recon.cells),
        "display_cell_count": len(complete_map.cells),
        "asteroid_field_cell_count": field_total,
        "shape_field_cell_count": complete_map.shape_field_cell_count,
        "fluid_field_cell_count": complete_map.fluid_field_cell_count,
        "primary_resource_kind": detect_primary_resource_kind(complete_map),
        "ambiguous_cell_count": len(recon.ambiguous_cells),
        "external_void_cell_count": len(topo.external_void_cells),
        "quality_tier": str(recon.quality_tier),
        "confidence_score": decimal_str(Decimal(str(recon.confidence_score))),
    }
    summary = dict(recon.summary_json or {})
    for key in ("inferred_shell_cell_count",):
        if key in summary:
            obs[key] = summary[key]
    return obs


# Backward-compatible alias (Option A: field cell count on complete map).
count_confirmed_platforms_by_resource = count_asteroid_field_cells_by_resource


__all__ = [
    "build_reconstruction_capacity_envelope",
    "build_reconstruction_capacity_summary",
    "build_reconstruction_observability",
    "count_asteroid_field_cells_by_resource",
    "count_confirmed_platforms_by_resource",
    "decimal_str",
    "detect_primary_resource_kind",
]
