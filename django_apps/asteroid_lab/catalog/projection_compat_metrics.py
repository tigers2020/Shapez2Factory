"""Projection compat observability — DTO-based counts + route instrumentation (Phase A Task 7)."""

from __future__ import annotations

from collections import Counter
from typing import Any

from django_apps.asteroid_lab.catalog.projection_source import (
    ProjectedEquipmentSpec,
    count_temporary_compat,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import BuildingCatalogSlice
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind

_route_compat_instrumentation_count: int = 0


def reset_projection_compat_instrumentation() -> None:
    """Reset route-tile instrumentation before a solver run or catalog step."""

    global _route_compat_instrumentation_count
    _route_compat_instrumentation_count = 0


def route_compat_instrumentation_count() -> int:
    """Route tiles emitted via ``resolve_route_tile`` since last reset (instrumentation only)."""

    return _route_compat_instrumentation_count


def record_route_compat_tile_emitted() -> None:
    """Increment instrumentation when a ``TEMPORARY_COMPAT`` route tile is synthesized."""

    global _route_compat_instrumentation_count
    _route_compat_instrumentation_count += 1


def _equipment_spec_index(
    catalog_slice: BuildingCatalogSlice,
    transport_kind: TransportKind,
) -> dict[str, ProjectedEquipmentSpec]:
    from django_apps.asteroid_lab.catalog.asteroid_equipment_projection import (
        list_equipment_placement_specs,
    )

    return {
        spec.pattern_id: spec
        for spec in list_equipment_placement_specs(catalog_slice, transport_kind=transport_kind)
    }


def _source_kind_counts(
    specs: tuple[ProjectedEquipmentSpec, ...],
) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for spec in specs:
        counter[spec.source_kind.value] += 1
    return dict(sorted(counter.items()))


def equipment_projection_metrics(
    catalog_slice: BuildingCatalogSlice,
    *,
    transport_kind: TransportKind,
) -> dict[str, Any]:
    """Output-only equipment projection summary for catalog slice step."""

    from django_apps.asteroid_lab.catalog.asteroid_equipment_projection import (
        list_equipment_placement_specs,
    )

    specs = list_equipment_placement_specs(catalog_slice, transport_kind=transport_kind)
    return {
        "equipment_projection_spec_count": len(specs),
        "temporary_compat_count_equipment": count_temporary_compat(specs),
        "projection_source_kind_counts": _source_kind_counts(tuple(specs)),
    }


def committed_projection_audit_metrics(
    catalog_slice: BuildingCatalogSlice | None,
    *,
    transport_kind: TransportKind,
    committed_ids: tuple[str, ...],
    candidates_by_id: dict[str, BundleCandidate],
    include_route_instrumentation: bool = True,
) -> dict[str, Any]:
    """Audit metrics for committed placements + route compat instrumentation."""

    if catalog_slice is None:
        route_count = route_compat_instrumentation_count() if include_route_instrumentation else 0
        return {
            "temporary_compat_count": route_count,
            "temporary_compat_count_equipment": 0,
            "temporary_compat_count_route_instrumentation": route_count,
            "projection_source_kind_counts": {},
            "committed_projection_audit": [],
        }

    index = _equipment_spec_index(catalog_slice, transport_kind)
    committed_dtos: list[ProjectedEquipmentSpec] = []
    audit_rows: list[dict[str, str]] = []
    for candidate_id in committed_ids:
        candidate = candidates_by_id.get(candidate_id)
        if candidate is None:
            continue
        ref = candidate.catalog_placement_ref
        if ref is None:
            audit_rows.append(
                {
                    "candidate_id": candidate_id,
                    "canonical_id": "",
                    "projection_source_kind": "",
                }
            )
            continue
        spec = index.get(candidate.pattern.pattern_id)
        if spec is None:
            audit_rows.append(
                {
                    "candidate_id": candidate_id,
                    "canonical_id": ref.canonical_id,
                    "projection_source_kind": "",
                }
            )
            continue
        committed_dtos.append(spec)
        audit_rows.append(
            {
                "candidate_id": candidate_id,
                "canonical_id": ref.canonical_id,
                "projection_source_kind": spec.source_kind.value,
            }
        )

    equipment_compat = count_temporary_compat(tuple(committed_dtos))
    route_count = route_compat_instrumentation_count() if include_route_instrumentation else 0
    return {
        "temporary_compat_count": equipment_compat + route_count,
        "temporary_compat_count_equipment": equipment_compat,
        "temporary_compat_count_route_instrumentation": route_count,
        "projection_source_kind_counts": _source_kind_counts(tuple(committed_dtos)),
        "committed_projection_audit": audit_rows,
    }


__all__ = [
    "committed_projection_audit_metrics",
    "equipment_projection_metrics",
    "record_route_compat_tile_emitted",
    "reset_projection_compat_instrumentation",
    "route_compat_instrumentation_count",
]
