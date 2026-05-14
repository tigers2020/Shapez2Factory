"""P3-E2 shadow lex vs greedy probe (observe-only)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    CORRIDOR_LIFECYCLE_DISCARDED,
    MAX_ROUTE_LENGTH_RATIO,
    P3E2_GUARD_EMPTY_POOL_NOT_WIRED,
    P3E2_GUARD_FROM_ADAPTER_INPUT,
    P3E2_GUARD_FROM_ROUTING_CORRIDOR_POOL,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_greedy_core import (
    placement_stub_route_probe_path,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_corridor_read_factory import (  # noqa: E501
    protected_corridors_read_from_routing_state,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_corridors import (
    merge_step4_corridor_routing_mapping,
)


def _p3e2_shadow_trace(
    *,
    mining_map: list[dict[str, Any]],
    cells: dict[Coord, dict[str, Any]],
    transport_cells: dict[Coord, str],
    outlets_order: list[Coord],
    anchor: Coord,
    transport_kind: str,
    asteroid_cells: set[Coord],
    mineable_f: frozenset[Coord],
    asteroid_f: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    shadow_enabled: bool,
    trunk_load: dict[str, Any] | None = None,
    routing_state_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Lex vs mining-priority greedy stub→anchor (per outlet); observation-only (P3-E2).

    ``p3e2_shadow_would_commit`` is a guarded-commit *preview* for a future P3-E3 step; it must
    not be interpreted as safe to apply lex routes or replace greedy Pass3 until that phase
    wires validation, protected corridors, and rollback.
    """

    base: dict[str, Any] = {
        "p3e2_shadow_enabled": shadow_enabled,
        "p3e2_lex_found": False,
        "p3e2_lex_internal_transport_count": 0,
        "p3e2_lex_path_length": 0,
        "p3e2_lex_search_time_ms_total": None,
        "p3e2_lex_expanded_nodes_total": None,
        "p3e2_lex_search_mode": None,
        "p3e2_lex_fallback_reason_last": None,
        "p3e2_lex_optimality_guarantee_last": None,
        "p3e2_greedy_internal_transport_count": 0,
        "p3e2_greedy_path_length": 0,
        "p3e2_shadow_would_commit": False,
        "p3e2_shadow_rejected_reason": "shadow_disabled" if not shadow_enabled else None,
        "p3e2_outlet_count": 0,
        "p3e2_lex_success_count": 0,
        "p3e2_greedy_success_count": 0,
        "p3e2_hard_protected_guard_state": None,
        "p3e2_step4_trunk_edge_congestion_wired": False,
    }
    if not shadow_enabled:
        return base

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.lexicographic_router import (  # noqa: E501
        find_lexicographic_route,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.route_adapter import (
        build_route_adapter_output,
        count_internal_new_transport_steps_on_path,
        route_adapter_input_for_pass3_stub,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.route_zone import (
        transport_kind_from_solver_value,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
        blocked_cells,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_trunk_load import (  # noqa: E501
        pass3_edge_congestion_weights_from_trunk_load,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
        transport_cells_reaching_external,
    )

    edge_congestion_weights = pass3_edge_congestion_weights_from_trunk_load(
        trunk_load, transport_kind=transport_kind
    )

    corridor_mapping = merge_step4_corridor_routing_mapping(
        routing_state=routing_state_summary if isinstance(routing_state_summary, dict) else None,
        trunk_load=trunk_load if isinstance(trunk_load, dict) else None,
    )
    corridor_dto = protected_corridors_read_from_routing_state(corridor_mapping)

    if not outlets_order:
        base.update(
            {
                "p3e2_lex_found": False,
                "p3e2_shadow_would_commit": False,
                "p3e2_shadow_rejected_reason": "no_outlets",
                "p3e2_hard_protected_guard_state": P3E2_GUARD_EMPTY_POOL_NOT_WIRED,
            }
        )
        return base

    blocked_layout = frozenset(blocked_cells(cells))
    probe_buildings: dict[Coord, str] = {
        c: str(cells.get(c, {}).get("role") or "layout_block") for c in blocked_layout
    }
    trunk_cells = frozenset(
        transport_cells_reaching_external(
            set(transport_cells.keys()),
            set(blocked_layout),
            is_external,
        )
    )
    fixed_stubs = frozenset(outlets_order)
    tk_enum = transport_kind_from_solver_value(transport_kind)
    mineable_s = set(mineable_f)

    sum_lex_internal = 0
    sum_lex_len = 0
    sum_lex_search_ms = 0.0
    sum_lex_expanded = 0
    lex_search_mode_last: str | None = None
    lex_fallback_last: str | None = None
    lex_optimality_last: bool | None = None
    sum_gr_internal = 0
    sum_gr_len = 0
    all_lex_ok = True
    greedy_outlets_ok = 0
    lex_outlets_ok = 0
    reject_reason: str | None = None
    hard_guard_state = (
        P3E2_GUARD_FROM_ROUTING_CORRIDOR_POOL
        if corridor_dto.hard
        else P3E2_GUARD_EMPTY_POOL_NOT_WIRED
    )
    discarded_probe_stub_cells: list[list[int]] = []

    for stub in outlets_order:
        rad_in = route_adapter_input_for_pass3_stub(
            mining_map_rows=mining_map,
            cells=cells,
            mineable_cells=mineable_f,
            asteroid_cells=asteroid_f,
            fixed_output_stub=stub,
            anchor=anchor,
            transport_kind=transport_kind,
            same_kind_transport_cells=frozenset(transport_cells.keys()),
            trunk_cells=trunk_cells,
        )
        if rad_in.hard_protected_cells:
            hard_guard_state = P3E2_GUARD_FROM_ADAPTER_INPUT
        ad_out = build_route_adapter_output(rad_in)
        lex_res = find_lexicographic_route(
            start=ad_out.start_stub,
            goals=set(ad_out.goal_cells),
            route_zone_map=ad_out.zone_by_cell,
            transport_kind=tk_enum,
            blocked_cells=set(ad_out.blocked_cells),
            existing_transport_cells=set(transport_cells.keys()),
            asteroid_cells=set(asteroid_f),
            placement_candidate_cells=mineable_s,
            allowed_cells=set(ad_out.allowed_cells),
            edge_congestion_weights=edge_congestion_weights,
            interior_depth_by_cell=ad_out.interior_depth_by_cell,
        )
        st_ms = lex_res.search_time_ms
        if st_ms is not None:
            sum_lex_search_ms += float(st_ms)
        sum_lex_expanded += int(lex_res.expanded_nodes)
        lex_search_mode_last = lex_res.search_mode
        lex_fallback_last = lex_res.fallback_reason
        lex_optimality_last = lex_res.optimality_guarantee
        if lex_res.found:
            lex_outlets_ok += 1

        g_path = placement_stub_route_probe_path(
            outlet_stub=stub,
            anchor=anchor,
            asteroid_cells=asteroid_cells,
            mineable_cells=set(mineable_f),
            buildings=probe_buildings,
            transport_cells=transport_cells,
            fixed_stubs=fixed_stubs,
        )

        if g_path is None:
            discarded_probe_stub_cells.append([int(stub[0]), int(stub[1])])
            if reject_reason is None:
                reject_reason = "no_greedy_baseline"
            if not lex_res.found:
                all_lex_ok = False
            continue

        greedy_outlets_ok += 1
        gp = tuple(g_path)
        sum_gr_len += len(gp)
        sum_gr_internal += count_internal_new_transport_steps_on_path(
            gp,
            route_zone_map=ad_out.zone_by_cell,
            transport_kind=tk_enum,
            existing_transport_cells=set(transport_cells.keys()),
            placement_candidate_cells=mineable_s,
        )

        if not lex_res.found:
            all_lex_ok = False
            if reject_reason is None:
                reject_reason = "lex_not_found"
        else:
            lp = lex_res.path
            sum_lex_internal += count_internal_new_transport_steps_on_path(
                lp,
                route_zone_map=ad_out.zone_by_cell,
                transport_kind=tk_enum,
                existing_transport_cells=set(transport_cells.keys()),
                placement_candidate_cells=mineable_s,
            )
            sum_lex_len += len(lp)
            if lp[0] != stub and reject_reason is None:
                reject_reason = "lex_stub_mismatch"
            hard = frozenset(rad_in.hard_protected_cells)
            if hard.intersection(lp) and reject_reason is None:
                reject_reason = "lex_hard_protected_hit"
            bl_hit = set(lp).intersection(ad_out.blocked_cells)
            if bl_hit - {stub} and reject_reason is None:
                reject_reason = "lex_blocked_cell_on_path"
            max_len = float(len(gp)) * MAX_ROUTE_LENGTH_RATIO
            if len(lp) > max_len and reject_reason is None:
                reject_reason = "lex_length_over_ratio_vs_greedy"

    n_out = len(outlets_order)
    greedy_complete = greedy_outlets_ok == n_out
    if not greedy_complete and reject_reason is None:
        reject_reason = "no_greedy_baseline"

    would_commit = (
        all_lex_ok
        and greedy_complete
        and reject_reason is None
        and sum_lex_internal < sum_gr_internal
    )
    if not would_commit and reject_reason is None:
        if greedy_complete and all_lex_ok and sum_lex_internal >= sum_gr_internal:
            reject_reason = "no_internal_transport_improvement"
        elif not all_lex_ok and greedy_complete:
            reject_reason = "lex_not_found"
    base.update(
        {
            "p3e2_lex_found": all_lex_ok,
            "p3e2_lex_internal_transport_count": sum_lex_internal,
            "p3e2_lex_path_length": sum_lex_len,
            "p3e2_lex_search_time_ms_total": sum_lex_search_ms,
            "p3e2_lex_expanded_nodes_total": sum_lex_expanded,
            "p3e2_lex_search_mode": lex_search_mode_last,
            "p3e2_lex_fallback_reason_last": lex_fallback_last,
            "p3e2_lex_optimality_guarantee_last": lex_optimality_last,
            "p3e2_greedy_internal_transport_count": sum_gr_internal,
            "p3e2_greedy_path_length": sum_gr_len,
            "p3e2_shadow_would_commit": would_commit,
            "p3e2_shadow_rejected_reason": None if would_commit else reject_reason,
            "p3e2_outlet_count": n_out,
            "p3e2_lex_success_count": lex_outlets_ok,
            "p3e2_greedy_success_count": greedy_outlets_ok,
            "p3e2_hard_protected_guard_state": hard_guard_state,
            "p3e2_step4_trunk_edge_congestion_wired": edge_congestion_weights is not None,
            "corridor_probe_discarded_cells": discarded_probe_stub_cells,
            "corridor_probe_lifecycle": (
                CORRIDOR_LIFECYCLE_DISCARDED if discarded_probe_stub_cells else None
            ),
        }
    )
    return base
