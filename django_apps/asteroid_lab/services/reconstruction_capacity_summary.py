"""Reconstruction terrain upper-bound capacity (output-only; never solver input)."""

from __future__ import annotations

from decimal import Decimal

from django_apps.asteroid_lab.reconstruction.acceptance_topology import (
    acceptance_topology_from_complete_map,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.reconstruction.field_cells import (
    count_asteroid_field_cells_by_resource,
    detect_present_resource_kinds,
    detect_primary_resource_kind,
)
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.reconstruction.rim_topology import field_rim_cells
from django_apps.game_data.services.mining_extraction_rules import get_active_rule
from shapez2_factory.application.asteroid_lab.reconstruction_capacity import (
    build_terrain_capacity_summary_row,
    decimal_str,
)


def _json_safe_source_kind(rule: object) -> str:
    raw = getattr(rule, "source_kind", "")
    return str(getattr(raw, "value", raw))


def build_reconstruction_capacity_summary(
    *,
    complete_map: ReconstructionCompleteMap,
    resource_kind: str,
) -> dict[str, object]:
    """Terrain upper bound; platform count from complete map field cells only."""

    rule = get_active_rule(resource_kind)
    if resource_kind == "shape":
        platform_count = complete_map.shape_field_cell_count
    else:
        platform_count = complete_map.fluid_field_cell_count
    return build_terrain_capacity_summary_row(
        resource_kind=resource_kind,
        platform_count=platform_count,
        mini_unit_output_per_min=rule.mini_unit_output_per_min,
        output_unit=rule.output_unit,
        max_extension_count=int(rule.max_extension_count),
        source_kind=_json_safe_source_kind(rule),
        authority="MiningExtractionRule",
    )


def build_reconstruction_capacity_envelope(
    *,
    complete_map: ReconstructionCompleteMap,
) -> dict[str, object]:
    by_resource = count_asteroid_field_cells_by_resource(complete_map)
    present = detect_present_resource_kinds(complete_map)
    return {
        "capacity_basis": "terrain_upper_bound",
        "primary_resource_kind": detect_primary_resource_kind(complete_map),
        "present_resource_kinds": list(present),
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
) -> dict[str, object]:
    topo = acceptance_topology_from_complete_map(complete_map)
    field_total = len(complete_map.field_cells)
    rim_cell_count = len(field_rim_cells(complete_map.field_cells))
    obs: dict[str, object] = {
        "cell_count": len(recon.cells),
        "display_cell_count": len(complete_map.cells),
        "rim_cell_count": rim_cell_count,
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
    "detect_present_resource_kinds",
    "detect_primary_resource_kind",
]
