"""Lexicographic grid routing for Pass3 (P3-E1).

Wired from ``pass3_e2_shadow`` and ``pass3_e3_guarded``.
"""

from __future__ import annotations

import heapq
from collections.abc import Mapping, Set

from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    MINING_OPPORTUNITY_LOSS_PER_CANDIDATE,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.lexicographic_router_contracts import (  # noqa: E501
    LexTuple,
    RouteSearchResult,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.route_zone import (
    KIND_COST_MULTIPLIER,
    ROUTE_ZONE_COST,
    RouteZone,
    TransportKind,
    route_zone_for_cell,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_trunk_load import (
    canonical_trunk_edge_key,
)

# (current cell, previous cell on the path). ``previous is None`` only for the start state.
type SearchState = tuple[Coord, Coord | None]


def _turn_delta(prev: Coord | None, cur: Coord, nxt: Coord) -> int:
    """이전 heading과 다음 heading의 turn cost 증가분을 계산한다 (§11.1 lex 차원 순서)."""
    if prev is None:
        return 0
    v1 = (cur[0] - prev[0], cur[1] - prev[1])
    v2 = (nxt[0] - cur[0], nxt[1] - cur[1])
    return 1 if v1 != v2 else 0


def _build_path_from_state(
    end_state: SearchState, parent: dict[SearchState, SearchState | None]
) -> tuple[Coord, ...]:
    """SearchState parent chain에서 route path를 복원한다 (§11.1 lexicographic Dijkstra)."""
    out: list[Coord] = []
    s: SearchState | None = end_state
    while s is not None:
        out.append(s[0])
        s = parent.get(s)
    out.reverse()
    return tuple(out)


def _step_deltas(
    *,
    prev: Coord | None,
    cur: Coord,
    nxt: Coord,
    route_zone_map: Mapping[Coord, RouteZone],
    transport_kind: TransportKind,
    existing_transport_cells: Set[Coord],
    placement_candidate_cells: Set[Coord],
    congestion_step: int,
) -> tuple[int, int, int, int, int, int]:
    """Per-step deltas: internal, opportunity, route_cost, congestion, turn, +1 path cell."""

    mult = KIND_COST_MULTIPLIER[transport_kind]
    zone = route_zone_for_cell(nxt, route_zone_map)
    internal_step = (
        1 if zone is RouteZone.ASTEROID_INTERIOR and nxt not in existing_transport_cells else 0
    )
    opp_step = (
        MINING_OPPORTUNITY_LOSS_PER_CANDIDATE
        if nxt in placement_candidate_cells and nxt not in existing_transport_cells
        else 0
    )
    route_step = ROUTE_ZONE_COST[zone] * mult
    turn_step = _turn_delta(prev, cur, nxt)
    return internal_step, opp_step, route_step, congestion_step, turn_step, 1


def _add_lex_prefix(
    a: LexTuple, di: int, dop: int, dr: int, dc: int, dt: int, dlen: int, nxt: Coord
) -> LexTuple:
    """lexicographic priority tuple에 한 step 비용을 누적한다 (§11.1 lex 차원 순서)."""
    return (
        a[0] + di,
        a[1] + dop,
        a[2] + dr,
        a[3] + dc,
        a[4] + dt,
        a[5] + dlen,
        nxt[0],
        nxt[1],
    )


def find_lexicographic_route(
    *,
    start: Coord,
    goals: Set[Coord],
    route_zone_map: Mapping[Coord, RouteZone],
    transport_kind: TransportKind,
    blocked_cells: Set[Coord],
    existing_transport_cells: Set[Coord],
    asteroid_cells: Set[Coord],
    placement_candidate_cells: Set[Coord],
    max_expanded_nodes: int = 20_000,
    allowed_cells: Set[Coord] | None = None,
    edge_congestion_weights: Mapping[str, int] | None = None,
) -> RouteSearchResult:
    """Minimize lexicographic path cost (internal, opportunity, route, congestion, turns, …).

    ``path[0]`` is always ``start`` (fixed stub). Lex index 3 is **congestion**: per-step
    weight from ``edge_congestion_weights`` keyed by :func:`canonical_trunk_edge_key` for
    ``(cur, nxt)`` when a mapping is provided; otherwise 0.

    The last two tuple components are the path tip coordinates (the goal when found).

    If ``allowed_cells`` is set, only those cells may be entered (bounded search).

    Search state is ``(cell, previous_cell)`` so cumulative turn cost depends on the
    incoming direction (same cell reached from different headings may continue with
    different turn penalties).
    """

    _ = asteroid_cells
    ecw: Mapping[str, int] | None = (
        edge_congestion_weights if isinstance(edge_congestion_weights, Mapping) else None
    )

    if start in blocked_cells and start not in goals:
        return RouteSearchResult(
            found=False,
            path=(),
            priority=None,
            expanded_nodes=0,
            search_mode="lexicographic_dijkstra",
            fallback_reason="start_blocked",
            optimality_guarantee=True,
        )

    start_state: SearchState = (start, None)
    start_key: LexTuple = (0, 0, 0, 0, 0, 1, start[0], start[1])
    best: dict[SearchState, LexTuple] = {start_state: start_key}
    parent: dict[SearchState, SearchState | None] = {start_state: None}
    pop_gen: dict[SearchState, int] = {start_state: 0}

    heap: list[tuple[LexTuple, int, Coord, Coord | None]] = [
        (start_key, pop_gen[start_state], start, None)
    ]

    best_goal: LexTuple | None = None
    best_goal_state: SearchState | None = None
    best_goal_path: tuple[Coord, ...] | None = None
    if start in goals:
        best_goal = start_key
        best_goal_state = start_state
        best_goal_path = (start,)

    expanded_nodes = 0
    budget_hit = False

    while heap:
        if best_goal is not None and heap[0][0] >= best_goal:
            break

        t_cur, gen_cur, cur, p_prev = heapq.heappop(heap)
        cur_state: SearchState = (cur, p_prev)
        if gen_cur != pop_gen.get(cur_state, 0) or t_cur != best.get(cur_state):
            continue

        expanded_nodes += 1
        if expanded_nodes > max_expanded_nodes:
            budget_hit = True
            break

        if cur in goals:
            cand_path = _build_path_from_state(cur_state, parent)
            if (
                best_goal is None
                or t_cur < best_goal
                or (
                    t_cur == best_goal and best_goal_path is not None and cand_path < best_goal_path
                )
            ):
                best_goal = t_cur
                best_goal_state = cur_state
                best_goal_path = cand_path

        for nxt in neighbors4(cur[0], cur[1]):
            if nxt in blocked_cells:
                continue
            if allowed_cells is not None and nxt not in allowed_cells:
                continue
            if nxt == start:
                continue

            dc_step = 0
            if ecw is not None:
                dc_step = int(ecw.get(canonical_trunk_edge_key(cur, nxt), 0))
            di, dop, dr, dc, dt, dlen = _step_deltas(
                prev=p_prev,
                cur=cur,
                nxt=nxt,
                route_zone_map=route_zone_map,
                transport_kind=transport_kind,
                existing_transport_cells=existing_transport_cells,
                placement_candidate_cells=placement_candidate_cells,
                congestion_step=dc_step,
            )
            new_t = _add_lex_prefix(t_cur, di, dop, dr, dc, dt, dlen, nxt)

            nxt_state: SearchState = (nxt, cur)
            old_t = best.get(nxt_state)
            if old_t is None or new_t < old_t:
                best[nxt_state] = new_t
                parent[nxt_state] = cur_state
                pop_gen[nxt_state] = pop_gen.get(nxt_state, 0) + 1
                heapq.heappush(heap, (new_t, pop_gen[nxt_state], nxt, cur))
                continue

            if new_t > old_t:
                continue

            path_old = _build_path_from_state(nxt_state, parent)
            path_new = _build_path_from_state(cur_state, parent) + (nxt,)
            if path_new >= path_old:
                continue

            best[nxt_state] = new_t
            parent[nxt_state] = cur_state
            pop_gen[nxt_state] = pop_gen.get(nxt_state, 0) + 1
            heapq.heappush(heap, (new_t, pop_gen[nxt_state], nxt, cur))

    if budget_hit:
        return RouteSearchResult(
            found=False,
            path=(),
            priority=None,
            expanded_nodes=expanded_nodes,
            search_mode="lexicographic_dijkstra",
            fallback_reason="expanded_node_budget_exceeded",
            optimality_guarantee=False,
        )

    if best_goal is None or best_goal_path is None or best_goal_state is None:
        return RouteSearchResult(
            found=False,
            path=(),
            priority=None,
            expanded_nodes=expanded_nodes,
            search_mode="lexicographic_dijkstra",
            fallback_reason="no_route_to_goals",
            optimality_guarantee=True,
        )

    if best_goal_path[0] != start:
        return RouteSearchResult(
            found=False,
            path=(),
            priority=None,
            expanded_nodes=expanded_nodes,
            search_mode="lexicographic_dijkstra",
            fallback_reason="internal_path_reconstruction_error",
            optimality_guarantee=False,
        )

    return RouteSearchResult(
        found=True,
        path=best_goal_path,
        priority=best_goal,
        expanded_nodes=expanded_nodes,
        search_mode="lexicographic_dijkstra",
        fallback_reason=None,
        optimality_guarantee=True,
    )
