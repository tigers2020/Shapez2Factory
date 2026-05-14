"""P4-B2 incremental route commit on top of B1 trial map."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.extraction.shape_miner_rotation import shape_miner_output_cell
from django_apps.shapez_asteroid.services.asteroid_mining_layout.dto.reclaim_shadow_types import (
    _P4BundleEval,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    INF_COST,
    MAX_RECLAIM_INCREMENTAL_ROUTE_LENGTH_RATIO,
    P4_RECLAIM_INCREMENTAL_ROUTE_PLACEMENT_ID,
    P4_REJECT_INCREMENTAL_ROUTE_LENGTH_RATIO,
    P4_REJECT_INTERNAL_TRANSPORT_BUDGET,
    P4_REJECT_NO_INCREMENTAL_ROUTE,
    P4_REJECT_NO_OUTPUT_STUB,
    P4_REJECT_VALIDATION,
    P4_ROLLBACK_AFTER_INCREMENTAL_ROUTE_FAILED,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_greedy_core import (
    pick_pass3_anchor_transport_cell,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_map_ops import (
    _all_transport_cells,
    _allowed_internal_transport_budget,
    _rebuild_mining_map_from_cells,
    _transport_role_dict_from_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_route_metrics import (  # noqa: E501
    _incremental_internal_transport_on_path,
    _p4_zone_trace_from_path,
    _path_additional_route_cost_detail,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    blocked_cells as _blocked_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    collect_routing_jobs as _collect_routing_jobs,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    mineable_and_asteroid_coords as _mineable_and_asteroid_coords,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    want_role as _want_role,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    cells_dict_from_mining_map,
)

from .reclaim_shadow_commit_trace import p4_b2_incremental_route_neutral_trace


def _p4_b2_try_commit_incremental_route(
    trial_map: list[dict[str, Any]],
    *,
    picked: _P4BundleEval,
    transport_kind: str,
    pass3_trace: dict[str, Any],
    final_mining_map: list[dict[str, Any]],
    is_external: Callable[[Coord], bool],
    reclaim_internal_transport_spent_prior: int = 0,
    pass3_internal_transport_saved_for_budget: int | None = None,
) -> tuple[list[dict[str, Any]] | None, dict[str, Any]]:
    """P4-B2: reprobe stub→trunk path on the B1 map, paint belt/pipe cells, validate."""

    import django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow as _p4f  # noqa: E501

    spent_prior = max(0, int(reclaim_internal_transport_spent_prior))

    def _fail(reason: str) -> tuple[list[dict[str, Any]] | None, dict[str, Any]]:
        """P4 incremental route 실패 payload를 공통 형태로 만든다 (§12.2 budget)."""
        return (
            None,
            {
                **p4_b2_incremental_route_neutral_trace(
                    attempted=True,
                    rollback_performed=True,
                    rollback_reason=reason,
                ),
            },
        )

    mineable, asteroid = _mineable_and_asteroid_coords(final_mining_map)
    raw = cells_dict_from_mining_map(trial_map)
    cells: dict[Coord, dict[str, Any]] = {k: dict(v) for k, v in raw.items()}
    jobs = _collect_routing_jobs(cells)
    if not jobs:
        return _fail(P4_REJECT_NO_INCREMENTAL_ROUTE)

    want_role_str = _want_role(transport_kind)
    anchor_cell = pick_pass3_anchor_transport_cell(
        cells,
        want_role=want_role_str,
        is_external=is_external,
    )
    if anchor_cell is None:
        return _fail(P4_REJECT_NO_INCREMENTAL_ROUTE)

    stub = shape_miner_output_cell(picked.anchor, picked.rotation)
    if stub is None:
        return _fail(P4_REJECT_NO_OUTPUT_STUB)

    probe_buildings: dict[Coord, str] = {
        c: str(cells.get(c, {}).get("role") or "layout_block") for c in _blocked_cells(cells)
    }
    transport_cells = _transport_role_dict_from_map(trial_map)
    outlets_order = [j[1] for j in jobs]
    fixed_stubs = frozenset(outlets_order)

    path = _p4f.placement_stub_route_probe_path(
        outlet_stub=stub,
        anchor=anchor_cell,
        asteroid_cells=set(asteroid),
        mineable_cells=set(mineable),
        buildings=probe_buildings,
        transport_cells=transport_cells,
        fixed_stubs=fixed_stubs,
    )
    if path is None or not path or path[0] != stub:
        return _fail(P4_REJECT_NO_INCREMENTAL_ROUTE)

    if pass3_internal_transport_saved_for_budget is not None:
        pass3_saved = max(0, int(pass3_internal_transport_saved_for_budget))
    else:
        raw_sv = pass3_trace.get("pass3_internal_transport_saved")
        pass3_saved = (
            max(0, int(raw_sv)) if isinstance(raw_sv, int) and not isinstance(raw_sv, bool) else 0
        )
        if pass3_saved == 0:
            implied = pass3_trace.get("pass3_internal_transport_saved_implied")
            if isinstance(implied, int) and not isinstance(implied, bool) and implied >= 0:
                pass3_saved = int(implied)
    internal_budget = _allowed_internal_transport_budget(pass3_saved)
    pass3_raw_saved = pass3_saved

    shadow_path = picked.shadow_route_path
    baseline_len = len(shadow_path) if shadow_path else len(path)
    max_len = max(
        1, int(math.ceil(float(baseline_len) * float(MAX_RECLAIM_INCREMENTAL_ROUTE_LENGTH_RATIO)))
    )
    if len(path) > max_len:
        return _fail(P4_REJECT_INCREMENTAL_ROUTE_LENGTH_RATIO)

    tot_cost, first_hop, after_stub = _path_additional_route_cost_detail(
        path,
        asteroid_cells=set(asteroid),
        mineable_cells=set(mineable),
        buildings=probe_buildings,
        transport_cells=transport_cells,
        fixed_stubs=fixed_stubs,
        outlet_stub=stub,
    )
    add_cost = float(tot_cost)
    if add_cost >= float(INF_COST):
        return _fail(P4_REJECT_NO_INCREMENTAL_ROUTE)

    existing_tc = _all_transport_cells(trial_map)
    incr = _incremental_internal_transport_on_path(
        path,
        mineable=mineable,
        asteroid=asteroid,
        existing_transport=existing_tc,
    )

    projected = spent_prior + incr
    if projected > internal_budget:
        return _fail(P4_REJECT_INTERNAL_TRANSPORT_BUDGET)
    if pass3_raw_saved > 0 and (pass3_raw_saved - projected) <= 0:
        return _fail(P4_REJECT_INTERNAL_TRANSPORT_BUDGET)

    stub_row = cells.get(stub)
    surface = str(
        (stub_row or {}).get("surface") or ("shape" if transport_kind == "shape_belt" else "fluid")
    )

    added_cells: list[list[int]] = []
    for p in path[1:]:
        row = cells.get(p)
        if row is not None and row.get("role") == want_role_str:
            continue
        if row is not None and row.get("role") in ("belt", "pipe"):
            if row.get("role") != want_role_str:
                return _fail(P4_REJECT_VALIDATION)
            continue
        cells[p] = {
            "x": p[0],
            "y": p[1],
            "role": want_role_str,
            "surface": surface,
            "placement_id": P4_RECLAIM_INCREMENTAL_ROUTE_PLACEMENT_ID,
        }
        added_cells.append([p[0], p[1]])

    merged_map = _rebuild_mining_map_from_cells(cells)
    report = _p4f.validate_final_mining_layout(merged_map)
    if not (report.geometry_valid and report.connectivity_valid):
        return _fail(P4_ROLLBACK_AFTER_INCREMENTAL_ROUTE_FAILED)

    path_cells = [[int(c[0]), int(c[1])] for c in path]
    zone_tr = _p4_zone_trace_from_path(path, mineable=mineable, asteroid=asteroid)
    return merged_map, {
        "p4_reclaim_incremental_route_attempted": True,
        "p4_reclaim_incremental_route_committed": True,
        "p4_reclaim_incremental_route_rollback_performed": False,
        "p4_reclaim_incremental_route_rollback_reason": None,
        "p4_reclaim_incremental_route_skip_reason": None,
        "p4_reclaim_incremental_route_path_cells": path_cells,
        "p4_reclaim_incremental_route_cells_added": added_cells,
        "p4_reclaim_incremental_route_b2_internal_transport_added": incr,
        "p4_reclaim_incremental_route_baseline_length": baseline_len,
        "p4_reclaim_incremental_route_max_length_allowed": max_len,
        "p4_reclaim_route_cost_including_stub": add_cost,
        "p4_reclaim_route_cost_first_hop_from_stub": float(first_hop),
        "p4_reclaim_route_cost_after_stub": float(after_stub),
        **zone_tr,
    }
