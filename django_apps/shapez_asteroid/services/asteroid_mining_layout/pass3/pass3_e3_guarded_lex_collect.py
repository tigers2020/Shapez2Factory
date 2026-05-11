"""Lex + greedy replacement collection for P3-E3 guarded atomic candidate."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    P3E3_REJECT_PRECHECK_NO_CANDIDATE,
    P3E3_REJECT_PRECHECK_NO_REPLACEMENT_ROUTE,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_greedy_core import (
    placement_stub_route_probe_path,
)


def _p3e3_collect_guarded_lex_replacement(
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
    trunk_load: dict[str, Any] | None = None,
) -> tuple[
    frozenset[Coord],
    frozenset[Coord],
    int | None,
    int | None,
    frozenset[Coord],
    frozenset[Coord],
    str | None,
]:
    """Per-outlet lex paths + unions of adapter hard/soft cells; mirrors P3-E2 shadow loop."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.lexicographic_router import (  # noqa: E501
        find_lexicographic_route,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.route_adapter import (
        build_route_adapter_output,
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
    edge_congestion_weights = pass3_edge_congestion_weights_from_trunk_load(
        trunk_load, transport_kind=transport_kind
    )

    replacement_union: set[Coord] = set()
    hard_u: set[Coord] = set()
    soft_u: set[Coord] = set()
    sum_lex_len = 0
    sum_gr_len = 0
    lex_ok_for_all = True
    greedy_ok_for_all = True

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
        hard_u |= set(rad_in.hard_protected_cells)
        soft_u |= set(rad_in.soft_protected_cells)
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
        )
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
            greedy_ok_for_all = False
            if not lex_res.found:
                lex_ok_for_all = False
            continue
        sum_gr_len += len(g_path)
        if not lex_res.found:
            lex_ok_for_all = False
            continue
        lp = lex_res.path
        sum_lex_len += len(lp)
        replacement_union |= set(lp)

    if not greedy_ok_for_all:
        return (
            frozenset(),
            frozenset(),
            None,
            None,
            frozenset(hard_u),
            frozenset(soft_u),
            P3E3_REJECT_PRECHECK_NO_REPLACEMENT_ROUTE,
        )
    if not lex_ok_for_all or not replacement_union:
        return (
            frozenset(),
            frozenset(),
            None,
            None,
            frozenset(hard_u),
            frozenset(soft_u),
            P3E3_REJECT_PRECHECK_NO_CANDIDATE,
        )

    current_tc = frozenset(transport_cells.keys())
    cells_to_remove = frozenset(current_tc - frozenset(replacement_union) - fixed_stubs - {anchor})
    return (
        cells_to_remove,
        frozenset(replacement_union),
        sum_gr_len,
        sum_lex_len,
        frozenset(hard_u),
        frozenset(soft_u),
        None,
    )
