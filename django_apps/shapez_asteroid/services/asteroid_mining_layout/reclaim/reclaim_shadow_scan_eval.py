"""P4-A shadow bundle evaluation (shared probe state + per-bundle scoring)."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from django_apps.shapez_asteroid.extraction.shape_miner_rotation import shape_miner_output_cell
from django_apps.shapez_asteroid.services.asteroid_mining_layout.dto.reclaim_shadow_types import (
    _P4BundleEval,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    INF_COST,
    P4_REJECT_FINAL_ROUTE_OVERLAP,
    P4_REJECT_GAIN_RATIO,
    P4_REJECT_HARD_PROTECTED_CORRIDOR,
    P4_REJECT_INTERNAL_TRANSPORT_BUDGET,
    P4_REJECT_NO_INCREMENTAL_ROUTE,
    P4_REJECT_NO_OUTPUT_STUB,
    P4_REJECT_SOFT_PROTECTED_CORRIDOR,
    P4_REJECT_VALIDATION,
    RECLAIM_DIVERSITY_CLUSTER_FALLOFF_K,
    RECLAIM_DIVERSITY_CLUSTER_RADIUS,
    RECLAIM_ROUTE_ZONE_OVERLAP_PENALTY,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_greedy_core import (
    pick_pass3_anchor_transport_cell,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_map_ops import (
    _all_transport_cells,
    _transport_role_dict_from_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_p4_bundle import (
    _p4_bundle_eval,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_route_metrics import (  # noqa: E501
    _incremental_internal_transport_on_path,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    blocked_cells as _blocked_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    cells_dict_from_mining_map,
)


@dataclass(frozen=True, slots=True)
class _P4ShadowScanShared:
    """Per-scan probe state reused across shadow bundle evaluations."""

    cells: dict[Coord, dict[str, Any]]
    probe_buildings: dict[Coord, str]
    transport_cells: dict[Coord, str]
    fixed_stubs: frozenset[Coord]
    mineable_cells: set[Coord]
    asteroid_cells: set[Coord]
    anchor_cell: Coord | None
    existing_transport: frozenset[Coord]


def _p4_reclaim_diversity_fields(
    anchor: Coord,
    gain_ratio: float,
    *,
    prior_reclaim_anchors: frozenset[Coord] | None,
    route_zone_cells_for_overlap: frozenset[Coord] | None,
    shadow_route_path: tuple[Coord, ...],
) -> dict[str, Any]:
    """Anchor falloff vs prior commits + weak overlap with committed incremental route zone."""
    priors = prior_reclaim_anchors or frozenset()
    min_d: int | None = None
    local_density = 0.0
    cluster_penalty = 0.0
    if priors:
        distances = [abs(anchor[0] - p[0]) + abs(anchor[1] - p[1]) for p in priors]
        min_d = min(distances)
        for d in distances:
            local_density += float(max(0, RECLAIM_DIVERSITY_CLUSTER_RADIUS - d))
        cluster_penalty = local_density * RECLAIM_DIVERSITY_CLUSTER_FALLOFF_K
    rz = route_zone_cells_for_overlap or frozenset()
    overlap_cells = sum(1 for c in shadow_route_path if c in rz)
    route_zone_penalty = float(overlap_cells) * RECLAIM_ROUTE_ZONE_OVERLAP_PENALTY
    total = cluster_penalty + route_zone_penalty
    if math.isinf(gain_ratio):
        gr_adj: float | None = None
    else:
        gr_adj = gain_ratio / (1.0 + total) if total > 0.0 else gain_ratio
    return {
        "p4_cluster_penalty": cluster_penalty,
        "p4_route_zone_overlap_cells": overlap_cells,
        "p4_route_zone_penalty": route_zone_penalty,
        "p4_local_cluster_density": local_density,
        "p4_min_anchor_distance_to_prior": min_d,
        "p4_total_diversity_penalty": total,
        "gain_ratio_adjusted": gr_adj,
    }


def _build_p4_shadow_scan_shared(
    map_after_pass3: list[dict[str, Any]],
    *,
    want_role: str,
    is_external: Callable[[Coord], bool],
    outlets_order: list[Coord],
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
) -> _P4ShadowScanShared:
    raw = cells_dict_from_mining_map(map_after_pass3)
    cells = {k: dict(v) for k, v in raw.items()}
    probe_buildings: dict[Coord, str] = {
        c: str(cells.get(c, {}).get("role") or "layout_block") for c in _blocked_cells(cells)
    }
    transport_cells = _transport_role_dict_from_map(map_after_pass3)
    fixed_stubs = frozenset(outlets_order)
    anchor_cell = pick_pass3_anchor_transport_cell(
        cells,
        want_role=want_role,
        is_external=is_external,
    )
    existing_transport = _all_transport_cells(map_after_pass3)
    return _P4ShadowScanShared(
        cells=cells,
        probe_buildings=probe_buildings,
        transport_cells=transport_cells,
        fixed_stubs=fixed_stubs,
        mineable_cells=set(mineable),
        asteroid_cells=set(asteroid),
        anchor_cell=anchor_cell,
        existing_transport=existing_transport,
    )


def _evaluate_one_shadow_bundle(
    *,
    anchor: Coord,
    extension: Coord,
    rotation: int,
    map_after_pass3: list[dict[str, Any]],
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    mineable_cur: frozenset[Coord],
    final_route_cells: frozenset[Coord],
    hard_protected_corridors: frozenset[Coord],
    soft_protected_corridors: frozenset[Coord],
    want_role: str,
    is_external: Callable[[Coord], bool],
    outlets_order: list[Coord],
    internal_budget: int,
    pass3_raw_saved: int,
    spent_prior: int = 0,
    gain_slots: float,
    gain_ratio_threshold: float,
    shared: _P4ShadowScanShared | None = None,
    prior_reclaim_anchors: frozenset[Coord] | None = None,
    route_zone_cells_for_overlap: frozenset[Coord] | None = None,
) -> _P4BundleEval:
    """P4 shadow bundle 하나의 gain_ratio와 budget 적합성을 평가한다 (§12.2 Reclaim loop)."""
    if anchor not in mineable_cur or extension not in mineable_cur:
        return _p4_bundle_eval(
            gain=0.0,
            additional_route_cost=0.0,
            gain_ratio=0.0,
            incremental_internal_transport_added=0,
            rejected_reason=P4_REJECT_VALIDATION,
            accepted_shadow=False,
            anchor=anchor,
            extension=extension,
            rotation=rotation,
        )

    stub = shape_miner_output_cell(anchor, rotation)
    if stub is None:
        return _p4_bundle_eval(
            gain=gain_slots,
            additional_route_cost=0.0,
            gain_ratio=0.0,
            incremental_internal_transport_added=0,
            rejected_reason=P4_REJECT_NO_OUTPUT_STUB,
            accepted_shadow=False,
            anchor=anchor,
            extension=extension,
            rotation=rotation,
        )

    if stub in final_route_cells:
        return _p4_bundle_eval(
            gain=gain_slots,
            additional_route_cost=0.0,
            gain_ratio=0.0,
            incremental_internal_transport_added=0,
            rejected_reason=P4_REJECT_FINAL_ROUTE_OVERLAP,
            accepted_shadow=False,
            anchor=anchor,
            extension=extension,
            rotation=rotation,
        )
    if stub in hard_protected_corridors or anchor in hard_protected_corridors:
        return _p4_bundle_eval(
            gain=gain_slots,
            additional_route_cost=0.0,
            gain_ratio=0.0,
            incremental_internal_transport_added=0,
            rejected_reason=P4_REJECT_HARD_PROTECTED_CORRIDOR,
            accepted_shadow=False,
            anchor=anchor,
            extension=extension,
            rotation=rotation,
        )
    if extension in hard_protected_corridors:
        return _p4_bundle_eval(
            gain=gain_slots,
            additional_route_cost=0.0,
            gain_ratio=0.0,
            incremental_internal_transport_added=0,
            rejected_reason=P4_REJECT_HARD_PROTECTED_CORRIDOR,
            accepted_shadow=False,
            anchor=anchor,
            extension=extension,
            rotation=rotation,
        )
    if (
        stub in soft_protected_corridors
        or anchor in soft_protected_corridors
        or extension in soft_protected_corridors
    ):
        return _p4_bundle_eval(
            gain=gain_slots,
            additional_route_cost=0.0,
            gain_ratio=0.0,
            incremental_internal_transport_added=0,
            rejected_reason=P4_REJECT_SOFT_PROTECTED_CORRIDOR,
            accepted_shadow=False,
            anchor=anchor,
            extension=extension,
            rotation=rotation,
        )

    scan = shared
    if scan is None:
        scan = _build_p4_shadow_scan_shared(
            map_after_pass3,
            want_role=want_role,
            is_external=is_external,
            outlets_order=outlets_order,
            mineable=mineable,
            asteroid=asteroid,
        )
    if scan.anchor_cell is None:
        return _p4_bundle_eval(
            gain=gain_slots,
            additional_route_cost=0.0,
            gain_ratio=0.0,
            incremental_internal_transport_added=0,
            rejected_reason=P4_REJECT_NO_INCREMENTAL_ROUTE,
            accepted_shadow=False,
            anchor=anchor,
            extension=extension,
            rotation=rotation,
        )

    import django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow as _p4f  # noqa: E501

    path = _p4f.placement_stub_route_probe_path(
        outlet_stub=stub,
        anchor=scan.anchor_cell,
        asteroid_cells=scan.asteroid_cells,
        mineable_cells=scan.mineable_cells,
        buildings=scan.probe_buildings,
        transport_cells=scan.transport_cells,
        fixed_stubs=scan.fixed_stubs,
    )
    if path is None:
        return _p4_bundle_eval(
            gain=gain_slots,
            additional_route_cost=0.0,
            gain_ratio=0.0,
            incremental_internal_transport_added=0,
            rejected_reason=P4_REJECT_NO_INCREMENTAL_ROUTE,
            accepted_shadow=False,
            anchor=anchor,
            extension=extension,
            rotation=rotation,
        )

    route_path = tuple(path)

    add_cost = float(
        _p4f._path_additional_route_cost(
            path,
            asteroid_cells=scan.asteroid_cells,
            mineable_cells=scan.mineable_cells,
            buildings=scan.probe_buildings,
            transport_cells=scan.transport_cells,
            fixed_stubs=scan.fixed_stubs,
            outlet_stub=stub,
        )
    )
    if add_cost >= float(INF_COST):
        div_kw = _p4_reclaim_diversity_fields(
            anchor,
            0.0,
            prior_reclaim_anchors=prior_reclaim_anchors,
            route_zone_cells_for_overlap=route_zone_cells_for_overlap,
            shadow_route_path=route_path,
        )
        return _p4_bundle_eval(
            gain=gain_slots,
            additional_route_cost=add_cost,
            gain_ratio=0.0,
            incremental_internal_transport_added=0,
            rejected_reason=P4_REJECT_NO_INCREMENTAL_ROUTE,
            accepted_shadow=False,
            anchor=anchor,
            extension=extension,
            rotation=rotation,
            shadow_route_path=route_path,
            **div_kw,
        )

    incr = _incremental_internal_transport_on_path(
        path,
        mineable=mineable,
        asteroid=asteroid,
        existing_transport=scan.existing_transport,
    )

    if add_cost <= 0.0:
        gain_ratio = float("inf") if gain_slots > 0 else 0.0
    else:
        gain_ratio = gain_slots / add_cost

    div_kw = _p4_reclaim_diversity_fields(
        anchor,
        gain_ratio,
        prior_reclaim_anchors=prior_reclaim_anchors,
        route_zone_cells_for_overlap=route_zone_cells_for_overlap,
        shadow_route_path=route_path,
    )

    if not (math.isinf(gain_ratio) or gain_ratio >= gain_ratio_threshold):
        return _p4_bundle_eval(
            gain=gain_slots,
            additional_route_cost=add_cost,
            gain_ratio=gain_ratio,
            incremental_internal_transport_added=incr,
            rejected_reason=P4_REJECT_GAIN_RATIO,
            accepted_shadow=False,
            anchor=anchor,
            extension=extension,
            rotation=rotation,
            shadow_route_path=route_path,
            **div_kw,
        )

    projected = spent_prior + incr
    if projected > internal_budget:
        return _p4_bundle_eval(
            gain=gain_slots,
            additional_route_cost=add_cost,
            gain_ratio=gain_ratio,
            incremental_internal_transport_added=incr,
            rejected_reason=P4_REJECT_INTERNAL_TRANSPORT_BUDGET,
            accepted_shadow=False,
            anchor=anchor,
            extension=extension,
            rotation=rotation,
            shadow_route_path=route_path,
            **div_kw,
        )

    if pass3_raw_saved > 0 and (pass3_raw_saved - projected) <= 0:
        return _p4_bundle_eval(
            gain=gain_slots,
            additional_route_cost=add_cost,
            gain_ratio=gain_ratio,
            incremental_internal_transport_added=incr,
            rejected_reason=P4_REJECT_INTERNAL_TRANSPORT_BUDGET,
            accepted_shadow=False,
            anchor=anchor,
            extension=extension,
            rotation=rotation,
            shadow_route_path=route_path,
            **div_kw,
        )

    return _p4_bundle_eval(
        gain=gain_slots,
        additional_route_cost=add_cost,
        gain_ratio=gain_ratio,
        incremental_internal_transport_added=incr,
        rejected_reason=None,
        accepted_shadow=True,
        anchor=anchor,
        extension=extension,
        rotation=rotation,
        shadow_route_path=route_path,
        **div_kw,
    )
