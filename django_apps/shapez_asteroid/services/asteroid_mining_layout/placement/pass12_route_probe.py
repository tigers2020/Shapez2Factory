"""Pass1/Pass2 bundle stub→external route probe gate (Stabilization-P1)."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_mining_layout.dto.mining_map_cell import (
    MiningMapCellsByCoord,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.dto.pass12_probe_types import (
    Pass2GoalTraceWire,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.route_probe import (
    probe_stub_cheap_escape_to_external_detail,
    probe_stub_to_external_detail,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
    trace_bundle_reject_no_route,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_goal_trunk_seed as s4_goal,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_route_failure_diagnostic as s4frd,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
    final_validation as finval,
)

Pass2RouteProbeOutcome = Literal["routed", "uncertain"]


def _min_manhattan_between_sets(a: set[Coord], b: frozenset[Coord]) -> int | None:
    best: int | None = None
    for ca in a:
        ax, ay = ca
        for cb in b:
            d = abs(int(ax) - int(cb[0])) + abs(int(ay) - int(cb[1]))
            if best is None or d < best:
                best = d
    return best


def _bfs_transport_component(
    seed: Coord,
    transport_cells: frozenset[Coord],
    blocked_cells: frozenset[Coord],
    *,
    blocked_exempt: Coord,
) -> set[Coord]:
    """4-neighbor flood on ``transport_cells``; ``blocked_cells`` except at ``blocked_exempt``."""

    q: deque[Coord] = deque([seed])
    visited: set[Coord] = {seed}
    while q:
        c = q.popleft()
        x, y = c
        for nxt in neighbors4(x, y):
            if nxt in blocked_cells and nxt != blocked_exempt:
                continue
            if nxt not in transport_cells or nxt in visited:
                continue
            visited.add(nxt)
            q.append(nxt)
    return visited


def _stub_component_frontier_detail(
    visited: set[Coord],
    stub_cell: Coord,
    blocked_cells: frozenset[Coord],
    exterior_reachable: frozenset[Coord],
) -> tuple[int, float, int | None]:
    frontier_blocked = 0
    frontier_total = 0
    for c in visited:
        cx, cy = c
        for nxt in neighbors4(cx, cy):
            if nxt in visited:
                continue
            frontier_total += 1
            if nxt in blocked_cells and nxt != stub_cell:
                frontier_blocked += 1
    ratio = frontier_blocked / max(1, frontier_total)
    nearest = _min_manhattan_between_sets(visited, exterior_reachable)
    return (
        int(len(visited)),
        float(ratio),
        int(nearest) if nearest is not None else None,
    )


def pass2_transport_stub_reaches_exterior_reachable_transport(
    stub_cell: Coord,
    *,
    transport_cells: frozenset[Coord],
    blocked_cells: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    reachable_goal_count: int,
    step4_goal_count: int = 0,
    pass2_precheck_reachable_goal_count: int = 0,
) -> tuple[bool, dict[str, Any]]:
    """True iff ``stub_cell``'s transport-only component intersects exterior-reachable transport.

    Uses the same exterior-reachable flood as
    :func:`final_validation.transport_cells_reaching_external` on the merged probe transport graph
    (Pass2 scratch geometry only; no STEP4 routing).

    When there is no exterior-reachable transport yet (e.g. first-route island: merged graph has
    only this stub fragment), returns True and ``reject_reason``
    ``skipped_no_exterior_reachable_transport`` **only** if STEP4 goal count is zero or the bounded
    precheck saw at least one reachable goal. If ``step4_goal_count > 0`` and the precheck found
    ``pass2_precheck_reachable_goal_count == 0``, returns False: interior transport must not mask
    a disconnected stub when goals exist (Algorithm §07/§08).
    """

    detail: dict[str, Any] = {
        "component_probe_kind": "transport_exterior_reachable_overlap",
        "reachable_goal_count": int(reachable_goal_count),
        "step4_goal_count": int(step4_goal_count),
        "pass2_precheck_reachable_goal_count": int(pass2_precheck_reachable_goal_count),
    }
    exterior_reachable = frozenset(
        finval.transport_cells_reaching_external(
            set(transport_cells), set(blocked_cells), is_external
        )
    )
    detail["exterior_reachable_transport_cell_count"] = int(len(exterior_reachable))
    if stub_cell not in transport_cells:
        detail["reject_reason"] = "stub_not_in_transport"
        detail["candidate_component_size"] = 0
        detail["frontier_blocked_ratio"] = 0.0
        detail["nearest_external_distance"] = None
        return False, detail
    if not exterior_reachable:
        others = transport_cells - {stub_cell}
        visited = _bfs_transport_component(
            stub_cell,
            transport_cells,
            blocked_cells,
            blocked_exempt=stub_cell,
        )
        sz, ratio, nearest = _stub_component_frontier_detail(
            visited, stub_cell, blocked_cells, exterior_reachable
        )
        detail["candidate_component_size"] = sz
        detail["frontier_blocked_ratio"] = ratio
        detail["nearest_external_distance"] = nearest
        if not others:
            if step4_goal_count > 0 and pass2_precheck_reachable_goal_count == 0:
                detail["reject_reason"] = "step4_unreachable_component"
                return False, detail
            detail["reject_reason"] = "skipped_no_exterior_reachable_transport"
            return True, detail
        if not (visited & others):
            detail["reject_reason"] = "step4_unreachable_component_no_goals"
            return False, detail
        if step4_goal_count > 0 and pass2_precheck_reachable_goal_count == 0:
            detail["reject_reason"] = "step4_unreachable_component"
            return False, detail
        detail["reject_reason"] = "skipped_no_exterior_reachable_transport"
        return True, detail

    visited = _bfs_transport_component(
        stub_cell,
        transport_cells,
        blocked_cells,
        blocked_exempt=stub_cell,
    )

    overlap = bool(visited & exterior_reachable)
    sz, ratio, nearest = _stub_component_frontier_detail(
        visited, stub_cell, blocked_cells, exterior_reachable
    )
    detail["candidate_component_size"] = sz
    detail["frontier_blocked_ratio"] = ratio
    detail["nearest_external_distance"] = nearest
    if overlap:
        detail["reject_reason"] = None
        return True, detail
    detail["reject_reason"] = "step4_unreachable_component"
    return False, detail


def _mineable_asteroid_bbox(
    mineable: frozenset[Coord], asteroid: frozenset[Coord]
) -> dict[str, int] | None:
    cells = (*mineable, *asteroid)
    if not cells:
        return None
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    return {"x_min": min(xs), "x_max": max(xs), "y_min": min(ys), "y_max": max(ys)}


_PASS2_MARGIN_DIAG_NEIGHBOR_CAP = 512


def _neighbor_in_expanded_mineable_shell(
    n: Coord, *, shell_bbox: tuple[int, int, int, int], margin: int
) -> bool:
    """True iff ``n`` is inside the inclusive §15 expanded rectangle (non-external shell)."""

    x, y = n
    x_min, x_max, y_min, y_max = shell_bbox
    return bool(x_min - margin <= x <= x_max + margin and y_min - margin <= y <= y_max + margin)


def _build_pass2_external_margin_diagnostic(
    *,
    universe: set[Coord],
    margin: set[Coord],
    is_external: Callable[[Coord], bool],
    bbox: dict[str, int] | None,
    is_external_shell_bbox: tuple[int, int, int, int] | None = None,
    is_external_shell_margin: int | None = None,
) -> dict[str, Any]:
    """Bounded ``is_external`` sampling to explain ``exterior_margin_cell_count == 0``."""

    u_count = len(universe)
    eligible_cells = {c for c in universe if c[0] != 0}
    eligible_n = len(eligible_cells)
    neighbor_coords: list[Coord] = []
    seen_n: set[Coord] = set()
    for c in sorted(eligible_cells, key=lambda p: (p[1], p[0])):
        cx, cy = c
        for n in neighbors4(cx, cy):
            if n in seen_n:
                continue
            seen_n.add(n)
            neighbor_coords.append(n)
            if len(neighbor_coords) >= _PASS2_MARGIN_DIAG_NEIGHBOR_CAP:
                break
        if len(neighbor_coords) >= _PASS2_MARGIN_DIAG_NEIGHBOR_CAP:
            break
    ext_true = 0
    ext_false = 0
    n_in_u = 0
    n_out_u = 0
    shell_x0 = 0
    shell_inside = 0
    shell_outside = 0
    shell_unknown = 0
    shell_known = (
        is_external_shell_bbox is not None
        and is_external_shell_margin is not None
        and len(is_external_shell_bbox) == 4
    )
    for n in neighbor_coords:
        if is_external(n):
            ext_true += 1
        else:
            ext_false += 1
        if n in universe:
            n_in_u += 1
        else:
            n_out_u += 1
        if shell_known:
            assert is_external_shell_bbox is not None
            assert is_external_shell_margin is not None
            _sh_bb = is_external_shell_bbox
            _sh_mg = is_external_shell_margin
            nx, _ny = n
            if nx == 0:
                shell_x0 += 1
            elif _neighbor_in_expanded_mineable_shell(n, shell_bbox=_sh_bb, margin=_sh_mg):
                shell_inside += 1
            else:
                shell_outside += 1
        else:
            shell_unknown += 1
    bbox_w: int | None = None
    bbox_h: int | None = None
    if bbox and all(k in bbox for k in ("x_min", "x_max", "y_min", "y_max")):
        bbox_w = int(bbox["x_max"]) - int(bbox["x_min"]) + 1
        bbox_h = int(bbox["y_max"]) - int(bbox["y_min"]) + 1
    reasons: list[str] = []
    if len(margin) == 0:
        if u_count == 0:
            reasons.append("empty_universe")
        elif eligible_n == 0:
            reasons.append("skipped_x0_only_universe")
        elif neighbor_coords and ext_true == 0:
            reasons.append("is_external_never_true_on_sampled_neighbors")
            if shell_known and shell_outside == 0 and neighbor_coords:
                reasons.append("all_sampled_neighbors_inside_predicate_shell_or_x0")
            # Universe 밖 이웃이 있어도 ``is_external``은 bbox±margin 기준이라
            # 빈 칸(void)이 셸 안에 있으면 여전히 False일 수 있다.
            if shell_known and n_out_u > 0 and shell_outside == 0:
                reasons.append("outside_universe_neighbors_inside_predicate_shell_padding")
        elif not neighbor_coords and eligible_n > 0:
            reasons.append("no_neighbor_coords_sampled")
    out: dict[str, Any] = {
        "universe_scan_cell_count": u_count,
        "margin_eligible_universe_cell_count": eligible_n,
        "neighbor_sample_cap": _PASS2_MARGIN_DIAG_NEIGHBOR_CAP,
        "sampled_neighbor_coord_count": len(neighbor_coords),
        "is_external_true_neighbor_sample_count": ext_true,
        "is_external_false_neighbor_sample_count": ext_false,
        "sampled_neighbor_in_universe_count": n_in_u,
        "sampled_neighbor_outside_universe_count": n_out_u,
        "bbox_width": bbox_w,
        "bbox_height": bbox_h,
    }
    if shell_known and is_external_shell_bbox is not None and is_external_shell_margin is not None:
        sx_min, sx_max, sy_min, sy_max = is_external_shell_bbox
        out["is_external_predicate_mineable_bbox"] = {
            "x_min": int(sx_min),
            "x_max": int(sx_max),
            "y_min": int(sy_min),
            "y_max": int(sy_max),
        }
        out["is_external_predicate_margin"] = int(is_external_shell_margin)
    else:
        out["is_external_predicate_mineable_bbox"] = None
        out["is_external_predicate_margin"] = None
    out["sampled_neighbor_shell_breakdown"] = {
        "predicate_shell_unknown_neighbor_count": shell_unknown,
        "sampled_neighbor_x_eq_0_count": shell_x0,
        "sampled_neighbor_inside_expanded_mineable_bbox_count": shell_inside,
        "sampled_neighbor_outside_expanded_mineable_bbox_count": shell_outside,
    }
    if reasons:
        out["margin_generation_reason_if_zero"] = reasons
    return out


def new_pass2_route_probe_stats_sink() -> dict[str, Any]:
    """Default counters merged into Pass12 stats (Pass2 STEP4-aligned probe gate)."""

    return {
        "pass2_probe_goal_set_kind_counts": {"first_route": 0, "subsequent_route": 0},
        "pass2_probe_goal_set_kind": "none",
        "pass2_probe_goal_count": 0,
        "pass2_probe_goal_count_max": 0,
        "pass2_probe_goal_count_sum": 0,
        "pass2_probe_last_final_goal_count": None,
        "pass2_probe_last_goal_trace": None,
        "pass2_probe_empty_goal_set_count": 0,
        "pass2_probe_goal_eval_count": 0,
        "pass2_route_uncertain_count": 0,
        "pass2_provisional_unrouted_count": 0,
        "pass2_hard_geometry_reject_count": 0,
        "pass2_reject_step4_stub_isolated_count": 0,
        "pass2_reject_step4_unreachable_stub_count": 0,
        "pass2_reject_step4_unreachable_fluid_stub_count": 0,
        "pass2_reject_step4_unreachable_component_count": 0,
        "reachable_component_sample_by_size": {},
    }


@dataclass(frozen=True)
class Pass2RouteProbePack:
    """Context for Pass2 route gate aligned with STEP4 goal-set (merge-aware routing prep)."""

    mineable: frozenset[Coord]
    asteroid: frozenset[Coord]
    cells: MiningMapCellsByCoord
    existing_layout_analysis: dict[str, Any] | None
    stats_sink: dict[str, Any]
    #: Same mineable bbox + margin as :func:`final_validation.external_predicate_for_mining_map`.
    is_external_shell_bbox: tuple[int, int, int, int] | None = None
    is_external_shell_margin: int | None = None


def build_pass2_step4_aligned_routing_goals(
    *,
    transport_kind: str,
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    cells: MiningMapCellsByCoord,
    is_external: Callable[[Coord], bool],
    existing_layout_analysis: dict[str, Any] | None,
    transport_cells_before: frozenset[Coord],
    transport_cells_probe: frozenset[Coord],
    blocked_for_probe: frozenset[Coord],
    stats_sink: dict[str, Any] | None = None,
    is_external_shell_bbox: tuple[int, int, int, int] | None = None,
    is_external_shell_margin: int | None = None,
) -> tuple[frozenset[Coord], Literal["first_route", "subsequent_route"], int, dict[str, Any]]:
    """Return ``(goal_cells, goal_set_kind, final_goal_count, trace)`` aligned with STEP4 §3.2.

    ``transport_cells_probe`` is the merged transport graph for the candidate under probe (Pass2
    commit snapshot). Exterior margin uses the same predicate as STEP4, plus ``universe_extra`` so
    probe-time belt coordinates participate even when absent from the frozen Pass1 ``cells``
    dict. Like ``step4_merge_routing`` per-job goals, ``raw_goal ∪ trunk_reaching(probe)`` is used
    (trunk slice is a no-op for first-route void assist when those cells are already transport).

    Orphan / non-exterior-reachable prior transport is never promoted into ``full_goal``; only
    exterior-reachable prior same-kind trunk (``existing_reaching``) feeds committed goals. If the
    union is empty, ``full_goal`` stays empty and Pass2 bundle commit rejects island-only prior
    transport before uncertain followup can mask it.
    """

    margin = s4_goal.exterior_margin_cells(
        mineable=mineable,
        asteroid=asteroid,
        cells=cells,
        is_external=is_external,
        universe_extra=transport_cells_probe,
    )
    hint_union = s4_goal.trunk_seed_union_from_existing_layout(existing_layout_analysis)
    trunk_seed_by_kind = s4_goal.build_trunk_seed_candidates_by_kind(
        exterior_margin=margin,
        hint_union=hint_union,
        cells=cells,
    )
    existing_reaching = finval.transport_cells_reaching_external(
        set(transport_cells_before), set(blocked_for_probe), is_external
    )
    if existing_reaching:
        goal_set_kind: Literal["first_route", "subsequent_route"] = "subsequent_route"
        committed: dict[str, set[Coord]] = {transport_kind: set(existing_reaching)}
    else:
        goal_set_kind = "first_route"
        committed = {}
    raw_goal = s4_goal.build_step4_goal_set(
        transport_kind,
        committed_trunk_by_kind=committed,
        exterior_margin_cells=margin,
        trunk_seed_candidates_by_kind=trunk_seed_by_kind,
    )
    trunk_now = finval.transport_cells_reaching_external(
        set(transport_cells_probe), set(blocked_for_probe), is_external
    )
    full_goal = frozenset(set(raw_goal) | trunk_now)
    seeds_for_kind = set(trunk_seed_by_kind.get(transport_kind, ()))
    universe_for_probe = (
        set(cells.keys()) | set(mineable) | set(asteroid) | set(transport_cells_probe)
    )
    bbox_ma = _mineable_asteroid_bbox(mineable, asteroid)
    trace: Pass2GoalTraceWire = {
        "goal_set_kind": goal_set_kind,
        "exterior_margin_cell_count": len(margin),
        "trunk_seed_candidate_count": len(seeds_for_kind),
        "same_kind_trunk_seed_count": len(seeds_for_kind - margin),
        "existing_trunk_goal_count": len(existing_reaching),
        "raw_goal_count": len(raw_goal),
        "trunk_reaching_probe_count": len(trunk_now),
        "final_goal_count": len(full_goal),
        "transport_cells_before_count": len(transport_cells_before),
        "external_reachable_transport_before_count": len(existing_reaching),
        "external_margin_bbox_source": "universe_keys_mineable_asteroid_probe_transport_union",
        "universe_cell_count": len(universe_for_probe),
        "mineable_cell_count": len(mineable),
        "asteroid_cell_count": len(asteroid),
        "mineable_asteroid_bbox": bbox_ma,
        "rejected_reason": None,
        "pass2_external_margin_diagnostic": _build_pass2_external_margin_diagnostic(
            universe=universe_for_probe,
            margin=margin,
            is_external=is_external,
            bbox=bbox_ma,
            is_external_shell_bbox=is_external_shell_bbox,
            is_external_shell_margin=is_external_shell_margin,
        ),
    }
    if not full_goal:
        prior_n = len(transport_cells_before)
        reach_n = len(existing_reaching)
        trace["pass2_prior_transport_all_orphan"] = bool(prior_n > 0 and reach_n == 0)
        trace["pass2_empty_goal_nonempty_universe"] = bool(
            len(universe_for_probe) > 0 and len(margin) == 0 and len(full_goal) == 0
        )
        if (
            goal_set_kind == "first_route"
            and len(margin) == 0
            and len(raw_goal) == 0
            and len(trunk_now) == 0
        ):
            trace["rejected_reason"] = str(
                s4frd.Step4RouteFailureReason.no_exterior_margin_for_probe
            )
        else:
            trace["rejected_reason"] = str(s4frd.Step4RouteFailureReason.empty_goal_set)
    if stats_sink is not None:
        stats_sink["pass2_probe_last_goal_trace"] = dict(trace)
    return full_goal, goal_set_kind, len(full_goal), dict(trace)


def _pass2_stats_touch_goal_eval(
    stats_sink: dict[str, Any], *, goal_kind: str, goal_count: int
) -> None:
    counts = stats_sink.setdefault("pass2_probe_goal_set_kind_counts", {})
    counts[goal_kind] = int(counts.get(goal_kind, 0)) + 1
    stats_sink["pass2_probe_goal_eval_count"] = (
        int(stats_sink.get("pass2_probe_goal_eval_count", 0)) + 1
    )
    stats_sink["pass2_probe_goal_count_max"] = max(
        int(stats_sink.get("pass2_probe_goal_count_max", 0)), int(goal_count)
    )
    stats_sink["pass2_probe_goal_count_sum"] = int(
        stats_sink.get("pass2_probe_goal_count_sum", 0)
    ) + int(goal_count)
    stats_sink["pass2_probe_last_final_goal_count"] = int(goal_count)


def _pass2_stats_note_transport_failure(
    stats_sink: dict[str, Any], transport_diag: dict[str, Any]
) -> None:
    tp = transport_diag.get("transport_probe")
    if not isinstance(tp, dict):
        return
    n = tp.get("reachable_cells_in_component")
    if not isinstance(n, int):
        return
    hist = stats_sink.setdefault("reachable_component_sample_by_size", {})
    key = str(n)
    hist[key] = int(hist.get(key, 0)) + 1


def finalize_pass2_route_probe_stats(stats_sink: dict[str, Any]) -> None:
    counts = stats_sink.get("pass2_probe_goal_set_kind_counts")
    total = 0
    if isinstance(counts, dict):
        total = sum(int(v) for v in counts.values() if isinstance(v, int))
    if not isinstance(counts, dict) or total == 0:
        stats_sink["pass2_probe_goal_set_kind"] = "none"
    else:
        dominant = max(counts.items(), key=lambda kv: (kv[1], kv[0]))[0]
        stats_sink["pass2_probe_goal_set_kind"] = dominant
    last = stats_sink.get("pass2_probe_last_final_goal_count")
    if isinstance(last, int):
        stats_sink["pass2_probe_goal_count"] = last
    else:
        stats_sink["pass2_probe_goal_count"] = int(stats_sink.get("pass2_probe_goal_count_max", 0))
    lt = stats_sink.get("pass2_probe_last_goal_trace")
    if isinstance(lt, dict) and "pass2_external_margin_diagnostic" not in lt:
        bbox_raw = lt.get("mineable_asteroid_bbox")
        bbox_ma = bbox_raw if isinstance(bbox_raw, dict) else None
        diagnostic = _build_pass2_external_margin_diagnostic(
            universe=set(),
            margin=set(),
            is_external=lambda _c: False,
            bbox=bbox_ma,
            is_external_shell_bbox=None,
            is_external_shell_margin=None,
        )
        diagnostic["solver_summary_gap_fill"] = True
        diagnostic["trace_universe_cell_count"] = lt.get("universe_cell_count")
        diagnostic["trace_final_goal_count"] = lt.get("final_goal_count")
        lt["pass2_external_margin_diagnostic"] = diagnostic


def _pass2_stub_adjacent_baseline_trunk_reaches_external(
    stub_cell: Coord,
    *,
    transport_cells: frozenset[Coord],
    blocked_cells: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    adjacent_preserve_trunk_baseline_cells: frozenset[Coord],
) -> tuple[bool, dict[str, Any]]:
    """True when stub 4-neighbors a Pass2-entry baseline trunk cell that reaches external."""

    sx, sy = stub_cell
    for nxt in neighbors4(sx, sy):
        if nxt not in adjacent_preserve_trunk_baseline_cells or nxt not in transport_cells:
            continue
        ok, det = probe_stub_to_external_detail(
            stub_cell=nxt,
            transport_cells=transport_cells,
            blocked_cells=blocked_cells,
            is_external=is_external,
        )
        if ok:
            out = {
                "pass2_preserve_merge_probe": {
                    "via_baseline_trunk_cell": [int(nxt[0]), int(nxt[1])],
                    "stub_cell": [int(sx), int(sy)],
                }
            }
            out.update(det)
            return True, out
    return False, {
        "pass2_preserve_merge_probe": {
            "failure": "no_baseline_adjacent_trunk_path_to_external",
            "stub_cell": [int(sx), int(sy)],
        }
    }


def pass2_bundle_route_probe_decision(
    stub_cell: Coord,
    *,
    transport_cells: frozenset[Coord],
    blocked_cells: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    routing_goal_cells: frozenset[Coord],
    goal_set_kind: str,
    goal_count: int,
    adjacent_preserve_trunk_baseline_cells: frozenset[Coord] | None,
    stats_sink: dict[str, Any] | None,
    goal_build_trace: dict[str, Any] | None = None,
) -> tuple[Pass2RouteProbeOutcome, dict[str, Any]]:
    """Pass2 gate: ``routed`` when a definite reach exists; else ``uncertain`` (STEP4 decides).

    Uses STEP4-aligned void envelope only (``routing_goal_cells - transport``), not Pass1
    cheap-escape envelopes. ``cheap_escape_probe`` may be ``skipped`` without implying reject.
    """

    if stats_sink is not None:
        _pass2_stats_touch_goal_eval(stats_sink, goal_kind=goal_set_kind, goal_count=goal_count)
        if goal_count == 0:
            stats_sink["pass2_probe_empty_goal_set_count"] = (
                int(stats_sink.get("pass2_probe_empty_goal_set_count", 0)) + 1
            )

    ok_transport, transport_diag = probe_stub_to_external_detail(
        stub_cell=stub_cell,
        transport_cells=transport_cells,
        blocked_cells=blocked_cells,
        is_external=is_external,
    )
    if ok_transport:
        out = dict(transport_diag)
        if goal_build_trace is not None:
            out["pass2_goal_set_trace"] = dict(goal_build_trace)
        return "routed", out

    if stats_sink is not None:
        _pass2_stats_note_transport_failure(stats_sink, transport_diag)

    goal_void_cells = frozenset(
        c for c in routing_goal_cells if c not in transport_cells and c not in blocked_cells
    )
    ok_goal_void, goal_void_diag = probe_stub_cheap_escape_to_external_detail(
        stub_cell=stub_cell,
        transport_cells=transport_cells,
        blocked_cells=blocked_cells,
        is_external=is_external,
        allowed_void_cells=goal_void_cells,
    )
    merged_goal = dict(transport_diag)
    if goal_build_trace is not None:
        merged_goal["pass2_goal_set_trace"] = dict(goal_build_trace)
    merged_goal["pass2_goal_assisted_probe"] = {
        "allowed_goal_void_cell_count": len(goal_void_cells),
        "success": ok_goal_void,
    }
    merged_goal.update(goal_void_diag)
    if ok_goal_void:
        return "routed", merged_goal

    merge_diag: dict[str, Any]
    if adjacent_preserve_trunk_baseline_cells:
        ok_merge, merge_diag = _pass2_stub_adjacent_baseline_trunk_reaches_external(
            stub_cell,
            transport_cells=transport_cells,
            blocked_cells=blocked_cells,
            is_external=is_external,
            adjacent_preserve_trunk_baseline_cells=adjacent_preserve_trunk_baseline_cells,
        )
        merged_goal.update(merge_diag)
        if ok_merge:
            return "routed", merged_goal
    else:
        merge_diag = {
            "pass2_preserve_merge_probe": {
                "skipped": True,
                "reason": "no_pass2_baseline_trunk_context",
            }
        }
        merged_goal.update(merge_diag)

    merged_goal["cheap_escape_probe"] = {
        "skipped": True,
        "reason": "pass2_no_p1_cheap_escape_envelope",
        "note": "skipped_is_not_hard_reject_pass2_defers_to_step4",
    }
    if stats_sink is not None:
        stats_sink["pass2_route_uncertain_count"] = (
            int(stats_sink.get("pass2_route_uncertain_count", 0)) + 1
        )
    return "uncertain", merged_goal


def bundle_route_probe_or_reject(
    stub_cell: Coord,
    *,
    transport_cells: frozenset[Coord],
    blocked_cells: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    trace_location: str,
    bundle_hint: dict[str, Any] | None = None,
    pass1_allow_cheap_escape: bool = False,
    p1_cheap_void_cells: frozenset[Coord] | None = None,
    pass2_adjacent_preserve_trunk_baseline_cells: frozenset[Coord] | None = None,
) -> bool:
    """Return True when ``stub_cell`` reaches an external cell; else trace reject and False.

    Used as a **Pass1/Pass2 placement commit safety gate** when Pass2 pack is absent; it does not
    establish STEP4 final merge-aware routes.

    When ``pass1_allow_cheap_escape`` is True (Pass1 only), void tiles inside
    ``p1_cheap_void_cells`` may be used for feasibility; they are **not** committed as transport.
    """

    ok_transport, transport_diag = probe_stub_to_external_detail(
        stub_cell=stub_cell,
        transport_cells=transport_cells,
        blocked_cells=blocked_cells,
        is_external=is_external,
    )
    if ok_transport:
        return True
    merge_diag: dict[str, Any]
    if pass2_adjacent_preserve_trunk_baseline_cells:
        ok_merge, merge_diag = _pass2_stub_adjacent_baseline_trunk_reaches_external(
            stub_cell,
            transport_cells=transport_cells,
            blocked_cells=blocked_cells,
            is_external=is_external,
            adjacent_preserve_trunk_baseline_cells=pass2_adjacent_preserve_trunk_baseline_cells,
        )
        if ok_merge:
            return True
    else:
        merge_diag = {
            "pass2_preserve_merge_probe": {
                "skipped": True,
                "reason": "no_pass2_baseline_trunk_context",
            }
        }
    cheap_diag: dict[str, Any]
    if pass1_allow_cheap_escape and p1_cheap_void_cells is not None:
        ok_cheap, cheap_diag = probe_stub_cheap_escape_to_external_detail(
            stub_cell=stub_cell,
            transport_cells=transport_cells,
            blocked_cells=blocked_cells,
            is_external=is_external,
            allowed_void_cells=p1_cheap_void_cells,
        )
        if ok_cheap:
            return True
    else:
        cheap_diag = {
            "cheap_escape_probe": {
                "skipped": True,
                "reason": "pass2_gate_or_no_void_envelope",
                "pass1_allow_cheap_escape": pass1_allow_cheap_escape,
                "has_void_envelope": p1_cheap_void_cells is not None,
            }
        }
    data = dict(bundle_hint or {})
    data["stub_cell"] = stub_cell
    data["route_probe_context"] = {
        "transport_cell_count": len(transport_cells),
        "blocked_cell_count": len(blocked_cells),
    }
    data.update(transport_diag)
    data.update(merge_diag)
    data.update(cheap_diag)
    trace_bundle_reject_no_route(trace_location, data)
    return False
