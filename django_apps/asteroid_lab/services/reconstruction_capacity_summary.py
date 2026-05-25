"""Reconstruction terrain upper-bound capacity (output-only; never solver input)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django_apps.asteroid_lab.cleanup.result import CleanupResult
from django_apps.asteroid_lab.reconstruction.acceptance_topology import (
    acceptance_topology_from_reconstruction,
    mineable_field_kind,
)
from django_apps.asteroid_lab.reconstruction.display_map import (
    merged_display_cells_from_reconstruction,
)
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.grid_contract import Coord
from django_apps.game_data.services.mining_extraction_rules import (
    effective_mini_units,
    get_active_rule,
    max_output_per_miner,
)


def decimal_str(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.0001")), "f")


def _json_safe_source_kind(rule: object) -> str:
    raw = getattr(rule, "source_kind", "")
    return str(getattr(raw, "value", raw))


def _cell_by_coord(recon: ReconstructionResult) -> dict[Coord, DecodedCellDTO]:
    by: dict[Coord, DecodedCellDTO] = {}
    for cell in recon.cells:
        by[(cell.x, cell.y)] = cell
    return by


def _resource_kind_for_field(field_kind: str | None) -> str | None:
    if field_kind == "asteroid_shape_field":
        return "shape"
    if field_kind == "asteroid_fluid_field":
        return "fluid"
    return None


def count_confirmed_platforms_by_resource(recon: ReconstructionResult) -> dict[str, int]:
    """Confirmed mineable coords per shape/fluid field kind (not shared total)."""

    by_coord = _cell_by_coord(recon)
    counts = {"shape": 0, "fluid": 0}
    for coord in recon.confirmed_cells:
        cell = by_coord.get(coord)
        if cell is None:
            continue
        resource = _resource_kind_for_field(mineable_field_kind(cell))
        if resource is not None:
            counts[resource] += 1
    return counts


def detect_primary_resource_kind(recon: ReconstructionResult) -> str:
    """Dominant asteroid resource from confirmed platforms; tie → shape (island convention)."""

    counts = count_confirmed_platforms_by_resource(recon)
    if counts["fluid"] > counts["shape"]:
        return "fluid"
    return "shape"


def build_reconstruction_capacity_summary(
    *,
    recon: ReconstructionResult,
    resource_kind: str,
    platform_count: int | None = None,
) -> dict[str, Any]:
    rule = get_active_rule(resource_kind)
    if platform_count is None:
        platform_count = count_confirmed_platforms_by_resource(recon)[resource_kind]
    per_miner = max_output_per_miner(rule)
    total = per_miner * Decimal(platform_count)
    max_mini = effective_mini_units(int(rule.max_extension_count))
    return {
        "resource_kind": resource_kind,
        "capacity_upper_bound_platform_count": platform_count,
        "mini_unit_output_per_min": decimal_str(rule.mini_unit_output_per_min),
        "max_mini_units_per_miner": max_mini,
        "max_output_per_miner": decimal_str(per_miner),
        "max_throughput_per_min": decimal_str(total),
        "output_unit": rule.output_unit,
        "source_kind": _json_safe_source_kind(rule),
        "authority": "MiningExtractionRule",
    }


def build_reconstruction_capacity_envelope(
    *,
    recon: ReconstructionResult,
) -> dict[str, Any]:
    by_resource = count_confirmed_platforms_by_resource(recon)
    return {
        "capacity_basis": "terrain_upper_bound",
        "primary_resource_kind": detect_primary_resource_kind(recon),
        "confirmed_platforms_by_resource": dict(by_resource),
        "by_resource": {
            "shape": build_reconstruction_capacity_summary(
                recon=recon,
                resource_kind="shape",
                platform_count=by_resource["shape"],
            ),
            "fluid": build_reconstruction_capacity_summary(
                recon=recon,
                resource_kind="fluid",
                platform_count=by_resource["fluid"],
            ),
        },
    }


def build_reconstruction_observability(
    *,
    recon: ReconstructionResult,
    cleanup: CleanupResult | None = None,
) -> dict[str, Any]:
    by_resource = count_confirmed_platforms_by_resource(recon)
    topo = acceptance_topology_from_reconstruction(recon)
    display_cell_count = len(recon.cells)
    if cleanup is not None:
        display_cell_count = len(merged_display_cells_from_reconstruction(cleanup, recon))

    obs: dict[str, Any] = {
        "cell_count": len(recon.cells),
        "display_cell_count": display_cell_count,
        "mineable_cell_count": len(topo.mineable_cells),
        "confirmed_cell_count": len(recon.confirmed_cells),
        "shape_confirmed_cell_count": by_resource["shape"],
        "fluid_confirmed_cell_count": by_resource["fluid"],
        "primary_resource_kind": detect_primary_resource_kind(recon),
        "ambiguous_cell_count": len(recon.ambiguous_cells),
        "external_void_cell_count": len(recon.external_void_cells),
        "quality_tier": str(recon.quality_tier),
        "confidence_score": decimal_str(Decimal(str(recon.confidence_score))),
    }
    summary = dict(recon.summary_json or {})
    for key in ("inferred_shell_cell_count",):
        if key in summary:
            obs[key] = summary[key]
    return obs


__all__ = [
    "build_reconstruction_capacity_envelope",
    "build_reconstruction_capacity_summary",
    "build_reconstruction_observability",
    "count_confirmed_platforms_by_resource",
    "decimal_str",
    "detect_primary_resource_kind",
]
