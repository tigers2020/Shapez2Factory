"""Bounded STEP4 local bridge: subset-goal Dijkstra after Pass2 recovery exhausts."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitRecord,
    PlacementCommitState,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_route_failure_diagnostic as _s4_diag,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_dijkstra import (
    dijkstra_route_step4,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_failed_pass2_route_recovery import (  # noqa: E501
    Pass2RouteRecoveryOutcome,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_routing_models import (
    Step4MutableState,
    Step4RoutingContext,
    Step4StubRouteJob,
)

Step4RouteFailureReason = _s4_diag.Step4RouteFailureReason
breaker_category_for_no_route_exhausted = _s4_diag.breaker_category_for_no_route_exhausted
build_step4_route_failure_diagnostic = _s4_diag.build_step4_route_failure_diagnostic

_ALLOWED_BREAKERS = frozenset(
    {
        "trunk_union_goals_unreachable_from_stub",
        "stub_local_geometry_or_corridor",
        "narrow_search_exhausted",
    }
)
_K_TRUNK = 12
_K_EXT = 4
_PATH_LEN_MARGIN = 6
_LOCAL_BRIDGE_MAX_HEAP_POPS = 8000


def _manhattan(a: Coord, b: Coord) -> int:
    return abs(int(a[0]) - int(b[0])) + abs(int(a[1]) - int(b[1]))


def bridge_goal_subset_for_local_recovery(
    stub_cell: Coord,
    *,
    trunk_cells: frozenset[Coord],
    goal_cells: frozenset[Coord],
    margin_cells: set[Coord],
) -> frozenset[Coord]:
    """Nearest trunk + margin∩goal cells (deterministic sort)."""

    trunk_sorted = sorted(
        trunk_cells,
        key=lambda c: (_manhattan(stub_cell, c), c[1], c[0]),
    )
    ext_cells = frozenset(goal_cells & margin_cells)
    ext_sorted = sorted(
        ext_cells,
        key=lambda c: (_manhattan(stub_cell, c), c[1], c[0]),
    )
    g_trunk = frozenset(trunk_sorted[:_K_TRUNK])
    g_ext = frozenset(ext_sorted[:_K_EXT])
    return frozenset(g_trunk | g_ext)


def try_step4_local_bridge_recovery(
    *,
    ext_cell: Coord,
    stub_cell: Coord,
    tk: str,
    rec: PlacementCommitRecord,
    cells: dict[Coord, dict[str, Any]],
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    blocked: frozenset[Coord],
    trunk_cells: frozenset[Coord],
    goal_cells: frozenset[Coord],
    raw_goal: set[Coord],
    margin_cells: set[Coord],
    trunk_seed_by_kind: dict[str, set[Coord]],
    committed_trunk_by_kind: dict[str, set[Coord]],
    cheap_reuse_cells: frozenset[Coord],
    hard_extras: frozenset[Coord],
    detail: dict[str, Any],
    search_stats: dict[str, Any],
    want_role: str,
    committed_trunk_for_kind: set[Coord],
) -> tuple[Pass2RouteRecoveryOutcome | None, str | None, bool, dict[str, Any] | None]:
    """Return ``(outcome, reject_reason, attempted, meta)``.

    ``meta`` holds telemetry keys when ``attempted`` is True (success or reject).
    """

    if rec.placement_pass != "pass2" or rec.state != PlacementCommitState.PROVISIONAL_PLACED:
        return None, None, False, None
    if cells.get(stub_cell) is None:
        return None, "missing_stub_cell", True, {"reject": "missing_stub_cell"}

    prediag = build_step4_route_failure_diagnostic(
        rec=rec,
        extractor_cell=ext_cell,
        stub_cell=stub_cell,
        transport_kind=tk,
        want_role=want_role,
        raw_goal=set(raw_goal),
        goal_cells=goal_cells,
        trunk_cells=trunk_cells,
        trunk_seed_candidates_by_kind=trunk_seed_by_kind,
        margin_cells=margin_cells,
        committed_trunk_for_kind=set(committed_trunk_for_kind),
        blocked=blocked,
        hard_extras=hard_extras,
        cells=cells,
        mineable=mineable,
        asteroid=asteroid,
        is_external=is_external,
        cheap_reuse_cells=cheap_reuse_cells,
        search_stats=search_stats,
        detail=detail,
        final_state=None,
    )
    if prediag.get("failure_reason") != Step4RouteFailureReason.no_route_exhausted.value:
        return None, "not_no_route_exhausted", True, {"reject": "not_no_route_exhausted"}

    breaker = breaker_category_for_no_route_exhausted(prediag, detail)
    if breaker not in _ALLOWED_BREAKERS:
        return (
            None,
            "breaker_out_of_scope",
            True,
            {
                "reject": "breaker_out_of_scope",
                "breaker_category": breaker,
            },
        )

    g_bridge = bridge_goal_subset_for_local_recovery(
        stub_cell,
        trunk_cells=trunk_cells,
        goal_cells=goal_cells,
        margin_cells=margin_cells,
    )
    if not g_bridge:
        return (
            None,
            "no_bridge_goals",
            True,
            {
                "reject": "no_bridge_goals",
                "breaker_category": breaker,
                "g_bridge_size": 0,
            },
        )

    nh_raw = detail.get("nearest_existing_transport_distance")
    nh = int(nh_raw) if isinstance(nh_raw, int) and not isinstance(nh_raw, bool) else None
    max_edges = min(96, max((nh + _PATH_LEN_MARGIN) if nh is not None else 64, 1))
    max_pops = min(_LOCAL_BRIDGE_MAX_HEAP_POPS, 200 * max(len(g_bridge), 1))

    bridge_stats: dict[str, Any] = {"search_mode": "local_bridge:subset_goals"}
    path = dijkstra_route_step4(
        stub_cell,
        want_role=want_role,
        cells=cells,
        blocked=blocked,
        mineable=mineable,
        asteroid=asteroid,
        is_external=is_external,
        trunk=trunk_cells,
        goal_cells=g_bridge,
        margin_cells=frozenset(margin_cells),
        cheap_reuse_cells=cheap_reuse_cells,
        search_stats=bridge_stats,
        max_heap_pops=max_pops,
    )
    if path is None:
        sr = bridge_stats.get("stop_reason")
        if sr == "budget":
            return (
                None,
                "budget",
                True,
                {
                    "reject": "budget",
                    "breaker_category": breaker,
                    "g_bridge_size": len(g_bridge),
                    "stop_reason": sr,
                    "expanded_nodes": bridge_stats.get("expanded_nodes"),
                },
            )
        return (
            None,
            "exhausted",
            True,
            {
                "reject": "exhausted",
                "breaker_category": breaker,
                "g_bridge_size": len(g_bridge),
                "stop_reason": sr,
                "expanded_nodes": bridge_stats.get("expanded_nodes"),
            },
        )
    if len(path) - 1 > max_edges:
        return (
            None,
            "path_length_cap",
            True,
            {
                "reject": "path_length_cap",
                "breaker_category": breaker,
                "g_bridge_size": len(g_bridge),
                "path_len": len(path),
                "max_edges": max_edges,
            },
        )

    return (
        Pass2RouteRecoveryOutcome(
            path=path,
            recovery_search_mode="local_bridge:subset_goals",
            recovery_variant_eval_count=1,
            new_rotation_r=None,
            new_stub_cell=stub_cell,
            recovery_last_error=None,
        ),
        None,
        True,
        {
            "success": True,
            "breaker_category": breaker,
            "g_bridge_size": len(g_bridge),
            "stop_reason": bridge_stats.get("stop_reason"),
            "expanded_nodes": bridge_stats.get("expanded_nodes"),
        },
    )


def try_step4_local_bridge_recovery_ctx(
    ctx: Step4RoutingContext,
    state: Step4MutableState,
    job: Step4StubRouteJob,
    *,
    blocked: frozenset[Coord],
    trunk_cells: frozenset[Coord],
    goal_cells: frozenset[Coord],
    raw_goal: set[Coord],
    want_role: str,
    detail: dict[str, Any],
    search_stats: dict[str, Any],
    committed_trunk_for_kind: set[Coord],
) -> tuple[Pass2RouteRecoveryOutcome | None, str | None, bool, dict[str, Any] | None]:
    """Bundle local bridge recovery inputs from STEP4 merge ``ctx`` / ``state``."""

    pid = job.placement_id
    if pid is None or pid not in state.work_records:
        return None, None, False, None
    return try_step4_local_bridge_recovery(
        ext_cell=job.extractor_cell,
        stub_cell=job.stub_cell,
        tk=job.transport_kind,
        rec=state.work_records[pid],
        cells=state.cells,
        mineable=ctx.mineable,
        asteroid=ctx.asteroid,
        is_external=ctx.is_external,
        blocked=blocked,
        trunk_cells=trunk_cells,
        goal_cells=goal_cells,
        raw_goal=raw_goal,
        margin_cells=set(ctx.margin_cells),
        trunk_seed_by_kind=state.trunk_seed_by_kind_sets,
        committed_trunk_by_kind=state.committed_trunk_by_kind,
        cheap_reuse_cells=ctx.cheap_reuse_cells,
        hard_extras=ctx.hard_extras,
        detail=detail,
        search_stats=search_stats,
        want_role=want_role,
        committed_trunk_for_kind=committed_trunk_for_kind,
    )
