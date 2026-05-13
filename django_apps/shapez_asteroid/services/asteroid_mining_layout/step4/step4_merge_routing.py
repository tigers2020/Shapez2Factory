"""STEP4 merge-aware stub→external routing (Dijkstra) + placement commit FSM (P2-B).

Trunk seed / goal-set skeleton (§08): ``step4_goal_trunk_seed`` + per-job ``goal_cells``;
successful commits promote cells into ``committed_trunk_by_kind`` for subsequent merge goals.
On routing failure, cells are spatially restored from ``final_mining_map`` mineable rows; the FSM
passes through ``QUARANTINED_UNROUTED`` then is finalized to ``ROLLED_BACK`` so Pass3/guards never
see a non-terminal placement state on the returned map.

권한(셀 점유·목표 판정): ``step4_routing_permission``. 그래프 탐색: ``step4_dijkstra``.
P2-C 교정: ``step4_p2c_corrective``. 맵 조작·스냅샷: ``step4_map_ops``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.extractor_extension_group import (  # noqa: E501
    route_extractor_is_maximized_group,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitRecord,
    PlacementCommitState,
    placement_commit_counts_by_state,
    placement_record_to_failure_dict,
    transition_placement_record_to_rolled_back,
    unfinalized_placement_count_from_counts,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    blocked_cells as _blocked_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    collect_routing_jobs as _collect_routing_jobs,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    mineable_and_asteroid_coords,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    want_role as _want_role,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
    debug_log_event,
    trace_enabled,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_failed_pass2_route_recovery as _s4_p2_rec,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_hard_protected_no_route_diagnostics as _s4_hp_diag,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_local_bridge_recovery as _s4_lb,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_recovery_trigger as _s4_rt,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_route_failure_detail as _s4_fail_detail,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_search_diagnostics as _s4sd,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_contracts import (
    Step4Route,
    Step4RoutingResult,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_dijkstra import (
    DIJKSTRA_REACHABLE_GOAL_COUNT_KEY,
    dijkstra_route_step4,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_goal_trunk_seed import (  # noqa: E501
    build_step4_goal_set,
    build_trunk_seed_candidates_by_kind,
    exterior_margin_cells,
    trunk_seed_union_from_existing_layout,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_map_ops import (
    baseline_cells_copy as _baseline_cells_copy,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_map_ops import (
    rollback_placement_cells as _rollback_placement_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_map_ops import (
    rows_from_cells as _rows_from_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_map_ops import (
    same_kind_transport_cells as _same_kind_transport_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_map_ops import (
    stamp_placement_commit_on_map_rows as _stamp_placement_commit_on_map_rows,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_map_ops import (
    stub_reaches_external_trunk,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_map_ops import (
    surface_for_map as _surface_for_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_p2c_corrective import (
    p2c_revalidate_and_correct as _p2c_revalidate_and_correct,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_route_failure_detail import (  # noqa: E501
    _bfs_reachable_from_stub,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_route_failure_diagnostic import (  # noqa: E501
    build_step4_hard_protected_no_route_breakdown,
    build_step4_no_route_exhausted_breakdown,
    build_step4_route_failure_diagnostic,
    is_hard_protected_stub_ring_failure,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_routing_models import (
    Step4GoalSet,
    Step4MutableState,
    Step4RouteAttemptResult,
    Step4RouteJob,
    Step4RoutingContext,
    Step4SearchSnapshot,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_routing_state import (
    _routing_state_from_committed_routes,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_trunk_load import (
    accumulate_trunk_edge_load,
    build_step4_trunk_load_for_merge_state,
    build_step4_trunk_load_skipped,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    cells_dict_from_mining_map,
    transport_cells_reaching_external,
)

# Test / diagnostic patches: keep underscore aliases on this façade (see test_step4_merge_routing).
_dijkstra_route = dijkstra_route_step4
_stub_reaches_external_trunk = stub_reaches_external_trunk

__all__ = [
    "Step4Route",
    "Step4RoutingResult",
    "build_step4_goal_set",
    "build_trunk_seed_candidates_by_kind",
    "exterior_margin_cells",
    "run_step4_merge_aware_routing",
    "step4_routing_skipped_result",
    "trunk_seed_union_from_existing_layout",
]


def _margin_universe_extra_from_map_list(
    map_rows: list[dict[str, Any]],
    *,
    cells_keys: set[Coord],
) -> frozenset[Coord]:
    """Belt/pipe coords declared on ``map_after_pass2`` rows but absent from ``cells`` keys.

    Mirrors Pass2 ``build_pass2_step4_aligned_routing_goals`` (``pass12_route_probe``), which
    passes ``universe_extra=transport_cells_probe`` into :func:`exterior_margin_cells` so probe
    transport participates in the margin adjacency universe even when missing from the frozen
    ``cells`` dict (Algorithm ``08_step4_routing`` section 9.2: exterior margin and trunk seed).
    """

    out: set[Coord] = set()
    for row in map_rows:
        if row.get("role") not in ("belt", "pipe"):
            continue
        x, y = row.get("x"), row.get("y")
        if not isinstance(x, int) or not isinstance(y, int) or x == 0:
            continue
        c = (x, y)
        if c not in cells_keys:
            out.add(c)
    return frozenset(out)


def _step4_stub_min_margin_manhattan(
    stub: Coord,
    margin_cells: frozenset[Coord] | set[Coord],
) -> int:
    """Minimum Manhattan distance from ``stub`` to any exterior margin cell."""

    if not margin_cells:
        return 0
    sx, sy = stub
    best = 10**9
    for mx, my in margin_cells:
        d = abs(sx - mx) + abs(sy - my)
        if d < best:
            best = d
    return int(best)


def _step4_sort_routing_jobs_outside_in(
    jobs: list[tuple[Coord, Coord, str, str | None]],
    *,
    margin_cells: frozenset[Coord] | set[Coord],
) -> list[tuple[Coord, Coord, str, str | None]]:
    """Prefer routing stubs nearer the exterior margin first (§08 merge-aware ordering).

    ``collect_routing_jobs`` already applies a deterministic scan order; this reorders only
    when ``margin_cells`` is non-empty so merge-aware routing seeds shared trunk from the
    outside inward without changing the Dijkstra cost model.
    """

    if not jobs or not margin_cells:
        return jobs
    mc = margin_cells if isinstance(margin_cells, frozenset) else frozenset(margin_cells)
    return sorted(
        jobs,
        key=lambda j: (
            _step4_stub_min_margin_manhattan(j[1], mc),
            j[1][1],
            j[1][0],
            j[0][1],
            j[0][0],
        ),
    )


def _build_step4_ctx_state(
    map_after_pass2: list[dict[str, Any]],
    *,
    final_mining_map: list[dict[str, Any]],
    is_external: Callable[[Coord], bool],
    placement_records: dict[str, PlacementCommitRecord] | None,
    existing_layout_analysis: dict[str, Any] | None,
    hard_protected_cells: frozenset[Coord] | None,
    force_route_attempt_placement_ids: frozenset[str] | None,
) -> tuple[Step4RoutingContext, Step4MutableState]:
    mineable, asteroid = mineable_and_asteroid_coords(final_mining_map)
    raw_cells = cells_dict_from_mining_map(map_after_pass2)
    cells = {k: dict(v) for k, v in raw_cells.items()}
    final_cells = cells_dict_from_mining_map(final_mining_map)
    surface = _surface_for_map(cells)
    work_records: dict[str, PlacementCommitRecord] = {
        k: v for k, v in (placement_records or {}).items()
    }
    baseline_cells = _baseline_cells_copy(cells)
    baseline_wr = dict(work_records)

    jobs = _collect_routing_jobs(cells)
    want_role_global: str | None = None
    if jobs:
        want_role_global = _want_role(jobs[0][2])

    transport0 = _same_kind_transport_cells(cells, want_role_global) if want_role_global else set()
    blocked_set0 = _blocked_cells(cells)
    blocked0 = frozenset(blocked_set0)
    initial_trunk = frozenset(
        transport_cells_reaching_external(set(transport0), set(blocked0), is_external)
    )

    margin_universe_extra = _margin_universe_extra_from_map_list(
        map_after_pass2, cells_keys=set(cells.keys())
    )
    margin_cells = exterior_margin_cells(
        mineable=mineable,
        asteroid=asteroid,
        cells=cells,
        is_external=is_external,
        universe_extra=margin_universe_extra,
    )
    hint_union = trunk_seed_union_from_existing_layout(existing_layout_analysis)
    cheap_reuse_cells = frozenset(set(initial_trunk) | set(hint_union))
    trunk_seed_by_kind = build_trunk_seed_candidates_by_kind(
        exterior_margin=margin_cells,
        hint_union=hint_union,
        cells=cells,
    )
    jobs = _step4_sort_routing_jobs_outside_in(list(jobs), margin_cells=margin_cells)
    trunk_frozen = {k: frozenset(v) for k, v in trunk_seed_by_kind.items()}
    trunk_sets = {k: set(v) for k, v in trunk_seed_by_kind.items()}

    ctx = Step4RoutingContext(
        mineable=mineable,
        asteroid=asteroid,
        is_external=is_external,
        final_cells=final_cells,
        hard_extras=frozenset(hard_protected_cells or ()),
        existing_layout_analysis=existing_layout_analysis,
        surface=surface,
        margin_cells=frozenset(margin_cells),
        cheap_reuse_cells=cheap_reuse_cells,
        trunk_seed_by_kind=trunk_frozen,
        force_route_attempt_placement_ids=force_route_attempt_placement_ids,
    )
    state = Step4MutableState(
        cells=cells,
        work_records=work_records,
        baseline_cells=baseline_cells,
        baseline_wr=baseline_wr,
        jobs=jobs,
        initial_trunk=initial_trunk,
        trunk_seed_by_kind_sets=trunk_sets,
    )
    return ctx, state


def run_step4_merge_aware_routing(
    map_after_pass2: list[dict[str, Any]],
    *,
    final_mining_map: list[dict[str, Any]],
    is_external: Callable[[Coord], bool],
    placement_records: dict[str, PlacementCommitRecord] | None = None,
    force_route_attempt_placement_ids: frozenset[str] | None = None,
    mutate_input_map: bool = False,
    existing_layout_analysis: dict[str, Any] | None = None,
    hard_protected_cells: frozenset[Coord] | None = None,
    step4_reentry_index: int = 0,
) -> Step4RoutingResult:
    """Route each extractor stub; roll back failed ``placement_id`` bundles only (P2-B).

    ``force_route_attempt_placement_ids`` (optional): do not take the ``stub in trunk`` merge
    shortcut for these ids — forces a full Dijkstra attempt (unit tests / diagnostics).

    ``mutate_input_map``: when True, replace ``map_after_pass2`` rows in place with the routed
    layout on success (for ``SolverMutationTransaction`` / rollback on exception).
    On any exception, in-memory ``cells`` and ``work_records`` are restored to entry baselines
    before re-raising.

    ``existing_layout_analysis``: optional §E.3 payload; ``solver_hints.trunk_seed_cell_union``
    is merged into per-kind trunk seed candidates (never ``cleanup_candidate_cell_union`` /
    orphan/single-cell artifacts).

    ``hard_protected_cells``: optional frozen coords that may not be occupied or crossed
    (except the fixed output stub cell remains legal at path index 0).
    """

    ctx, state = _build_step4_ctx_state(
        map_after_pass2,
        final_mining_map=final_mining_map,
        is_external=is_external,
        placement_records=placement_records,
        existing_layout_analysis=existing_layout_analysis,
        hard_protected_cells=hard_protected_cells,
        force_route_attempt_placement_ids=force_route_attempt_placement_ids,
    )
    margin_cells_set = set(ctx.margin_cells)
    margin_cells = margin_cells_set
    mineable = ctx.mineable
    asteroid = ctx.asteroid
    is_external = ctx.is_external
    final_cells = ctx.final_cells
    surface = ctx.surface
    cheap_reuse_cells = ctx.cheap_reuse_cells
    hard_extras = ctx.hard_extras
    existing_layout_analysis = ctx.existing_layout_analysis
    cells = state.cells
    work_records = state.work_records
    jobs = state.jobs
    initial_trunk = state.initial_trunk
    trunk_seed_by_kind = state.trunk_seed_by_kind_sets
    committed_trunk_by_kind = state.committed_trunk_by_kind
    routes_by_placement_id = state.routes_by_placement_id
    goal_set_sizes = state.goal_set_sizes
    routes_out = state.routes_out
    failures = state.failures
    trunk_edge_hits = state.trunk.trunk_edge_hits
    trunk_edge_load_by_kind = state.trunk.trunk_edge_load_by_kind
    trunk_edge_load_maximized_by_kind = state.trunk.trunk_edge_load_maximized_by_kind
    maximized_extractor_cache = state.trunk.maximized_extractor_cache
    p2c_metrics = state.p2c_metrics
    rolled_back = state.rolled_back
    quarantined = state.quarantined

    recovery_attempted = 0
    recovery_success = 0
    recovery_rejected = 0
    recovery_last_error: str | None = None
    recovery_last_mode: str | None = None
    recovery_variant_eval_sum = 0
    lb_attempted = 0
    lb_success = 0
    lb_rejected = 0
    lb_failure_reasons: dict[str, int] = {}
    lb_samples: list[dict[str, Any]] = []
    search_diag_samples: list[dict[str, Any]] = []
    search_goal_ordering_applied_any = False
    search_goal_ordering_mode = "none"
    unrecoverable = False
    route_job_seq = 0

    try:
        for ext_cell, stub_cell, tk, placement_id in jobs:
            recovered = False
            want_role = _want_role(tk)
            blocked_set = set(_blocked_cells(cells)) | set(hard_extras)
            blocked_set.discard(stub_cell)
            blocked = frozenset(blocked_set)
            transport_now = _same_kind_transport_cells(cells, want_role)
            trunk_cells = frozenset(
                transport_cells_reaching_external(transport_now, set(blocked), is_external)
            )
            transport_before = frozenset(transport_now)

            force_attempt = (
                ctx.force_route_attempt_placement_ids is not None
                and placement_id is not None
                and placement_id in ctx.force_route_attempt_placement_ids
            )

            if stub_cell in trunk_cells and not force_attempt:
                routes_out.append(
                    Step4Route(
                        extractor_cell=ext_cell,
                        stub_cell=stub_cell,
                        transport_kind=tk,
                        path=(stub_cell,),
                        merged_to_existing=True,
                        reached_external=True,
                        placement_id=placement_id,
                    )
                )
                if placement_id is not None and placement_id in work_records:
                    rid = f"route-{placement_id}"
                    state.mark_routed_confirmed(
                        placement_id,
                        route_id=rid,
                        context="stub_in_trunk_merge_to_existing",
                    )
                    state.note_stub_in_trunk_merge(tk, stub_cell, placement_id)
                continue

            route_job_seq += 1
            rjob = Step4RouteJob(
                extractor_cell=ext_cell,
                stub_cell=stub_cell,
                transport_kind=tk,
                placement_id=placement_id,
                job_seq=route_job_seq,
                placement_commit_state_at_route_attempt=None,
            )

            raw_goal = build_step4_goal_set(
                tk,
                committed_trunk_by_kind=committed_trunk_by_kind,
                exterior_margin_cells=margin_cells,
                trunk_seed_candidates_by_kind=trunk_seed_by_kind,
            )
            # ``raw_goal`` = §08 trunk_seed∪margin (first phase) or committed∪margin (later).
            # ``merge_goal_union_meta`` adds live same-kind exterior-connected trunk cells so
            # Dijkstra can merge to preserved trunk before this run commits any path.
            goal_full, goal_order_meta = _s4sd.merge_goal_union_meta(
                stub_cell,
                raw_goal=set(raw_goal),
                trunk_cells=trunk_cells,
                margin_cells=margin_cells,
            )
            if goal_order_meta.get("applied"):
                search_goal_ordering_applied_any = True
                search_goal_ordering_mode = str(goal_order_meta.get("mode") or "none")

            search_stats: dict[str, Any] = {
                # ``search_mode`` names the goal-cell termination path; ``goal_ordering_mode`` is
                # the merge_goal_union_meta tier (see 15_step4_telemetry_field_semantics.md).
                "search_mode": "goal_cells_union_legacy",
                "step4_search_goal_priority_head": goal_order_meta.get("priority_head", ()),
                "exterior_fallback_considered": False,
                "exterior_fallback_activated": False,
                "exterior_fallback_reason": None,
                "primary_existing_trunk_reachable_count": None,
                "fallback_external_goal_count": 0,
            }
            search_stats["goal_ordering_mode"] = str(goal_order_meta.get("mode") or "none")

            fluid_primary_goals: frozenset[Coord] | None = None
            committed_kind = committed_trunk_by_kind.get(tk) or set()
            if tk == "fluid_pipe" and committed_kind:
                raw_primary = set(committed_kind)
                goal_primary, _pri_meta = _s4sd.merge_goal_union_meta(
                    stub_cell,
                    raw_goal=raw_primary,
                    trunk_cells=trunk_cells,
                    margin_cells=margin_cells,
                )
                fluid_primary_goals = goal_primary
                reachable_bfs = _bfs_reachable_from_stub(
                    stub_cell,
                    want_role=want_role,
                    blocked=blocked,
                    cells=cells,
                    mineable=mineable,
                    asteroid=asteroid,
                    is_external=is_external,
                    cheap_reuse_cells=cheap_reuse_cells,
                )
                pr = len(trunk_cells & reachable_bfs)
                margin_only = frozenset(margin_cells) - goal_primary
                search_stats["exterior_fallback_considered"] = True
                search_stats["primary_existing_trunk_reachable_count"] = pr
                search_stats["exterior_fallback_reason"] = "primary_trunk_only_goal_set"
                path = _dijkstra_route(
                    stub_cell,
                    want_role=want_role,
                    cells=cells,
                    blocked=blocked,
                    mineable=mineable,
                    asteroid=asteroid,
                    is_external=is_external,
                    trunk=trunk_cells,
                    goal_cells=goal_primary,
                    margin_cells=frozenset(margin_cells),
                    cheap_reuse_cells=cheap_reuse_cells,
                    search_stats=search_stats,
                )
                goal_cells = goal_primary
                if path is None and pr == 0 and margin_only:
                    search_stats["exterior_fallback_reason"] = (
                        "trunk_unreachable_reloading_exterior_margin_goals"
                    )
                    path = _dijkstra_route(
                        stub_cell,
                        want_role=want_role,
                        cells=cells,
                        blocked=blocked,
                        mineable=mineable,
                        asteroid=asteroid,
                        is_external=is_external,
                        trunk=trunk_cells,
                        goal_cells=goal_full,
                        margin_cells=frozenset(margin_cells),
                        cheap_reuse_cells=cheap_reuse_cells,
                        search_stats=search_stats,
                    )
                    goal_cells = goal_full
                    search_stats["exterior_fallback_activated"] = path is not None
                    search_stats["fallback_external_goal_count"] = len(margin_only)
                    if path is None:
                        search_stats["exterior_fallback_reason"] = (
                            "trunk_unreachable_margin_fallback_still_exhausted"
                        )
                elif path is None:
                    if pr > 0:
                        search_stats["exterior_fallback_reason"] = (
                            "stub_reaches_trunk_skip_margin_fallback"
                        )
                    elif not margin_only:
                        search_stats["exterior_fallback_reason"] = (
                            "no_margin_goals_beyond_primary_union"
                        )
                    else:
                        search_stats["exterior_fallback_reason"] = (
                            "primary_exhausted_no_margin_reload"
                        )
            else:
                path = _dijkstra_route(
                    stub_cell,
                    want_role=want_role,
                    cells=cells,
                    blocked=blocked,
                    mineable=mineable,
                    asteroid=asteroid,
                    is_external=is_external,
                    trunk=trunk_cells,
                    goal_cells=goal_full,
                    margin_cells=frozenset(margin_cells),
                    cheap_reuse_cells=cheap_reuse_cells,
                    search_stats=search_stats,
                )
                goal_cells = goal_full

            goal_set_dto = Step4GoalSet.from_merge_round(
                raw_goal=set(raw_goal),
                merged_union_cells=goal_full,
                goal_order_meta=goal_order_meta,
                fluid_primary_goal_cells=fluid_primary_goals,
            )

            goal_set_sizes.append(len(goal_cells))
            recovery_out = None
            recovery_eval_count = 0
            if path is None:
                bridge_out = None
                bridge_attempted_flag = False
                bridge_reason: str | None = None
                bridge_meta: dict[str, Any] | None = None
                pcs_at_attempt: str | None = None
                if placement_id is not None and placement_id in work_records:
                    pcs_at_attempt = work_records[placement_id].state.value
                ex_nodes0 = int(search_stats.get("expanded_nodes") or 0)
                d_rg0 = int(search_stats.get(DIJKSTRA_REACHABLE_GOAL_COUNT_KEY) or 0)
                step4_unreachable_trap = bool(ex_nodes0 > 0 and d_rg0 == 0)
                forced_err = "step4_unreachable_component" if step4_unreachable_trap else None
                routing_fail_reason = (
                    "step4_unreachable_component" if step4_unreachable_trap else "no_route"
                )
                placement_rollback_reason = routing_fail_reason
                placement_context = (
                    "step4_unreachable_component" if step4_unreachable_trap else "step4_no_route"
                )
                rjob = replace(
                    rjob,
                    placement_commit_state_at_route_attempt=pcs_at_attempt,
                )
                stub_job = rjob.as_stub_job()
                attempt = Step4RouteAttemptResult.capture(None, dict(search_stats))
                snap = Step4SearchSnapshot(
                    want_role=want_role,
                    blocked=blocked,
                    trunk_cells=trunk_cells,
                    goal_cells=goal_cells,
                    transport_now=frozenset(transport_now),
                    search_stats=search_stats,
                    goal_set=goal_set_dto,
                    attempt=attempt,
                )
                detail = _s4_fail_detail.build_step4_route_failure_detail_ctx(
                    ctx,
                    state,
                    rjob,
                    snap,
                    trunk_seed_candidate_count=len(trunk_seed_by_kind.get(tk, ())),
                    trunk_seed_cells=frozenset(trunk_seed_by_kind.get(tk, ())),
                    placement_commit_state_at_route_attempt=None,
                    forced_last_error=forced_err,
                )
                detail["step4_reentry_index"] = int(step4_reentry_index)
                rfd_detail = detail.get("routing_failure_detail")
                if isinstance(rfd_detail, dict):
                    rfd_detail["step4_reentry_index"] = int(step4_reentry_index)
                if len(search_diag_samples) < 8:
                    exn = int(search_stats.get("expanded_nodes") or 0)
                    smp: dict[str, Any] = {
                        "placement_id": placement_id,
                        "transport_kind": tk,
                        "expanded_nodes": exn,
                        "nearest_goal_distance_estimate": search_stats.get(
                            "nearest_goal_distance_estimate"
                        ),
                        "goal_count_by_distance_bucket": dict(
                            search_stats.get("goal_count_by_distance_bucket") or {}
                        ),
                        "first_goal_candidate": search_stats.get("first_goal_candidate"),
                        "max_frontier_size": search_stats.get("max_frontier_size"),
                        "frontier_stop_reason": search_stats.get("frontier_stop_reason"),
                        "wide_search_exhausted_guess": exn >= 20,
                    }
                    if tk == "fluid_pipe":
                        for k in (
                            "exterior_fallback_considered",
                            "exterior_fallback_activated",
                            "exterior_fallback_reason",
                            "primary_existing_trunk_reachable_count",
                            "fallback_external_goal_count",
                        ):
                            if k in search_stats:
                                smp[k] = search_stats[k]
                    search_diag_samples.append(smp)
                recovery_tried_pass2 = False
                job_recovery_last_mode: str | None = None
                job_recovery_last_err: str | None = None
                if placement_id is not None and placement_id in work_records:
                    rec0 = work_records[placement_id]
                    if (
                        rec0.placement_pass == "pass2"
                        and rec0.state == PlacementCommitState.PROVISIONAL_PLACED
                    ):
                        recovery_attempted += 1
                        recovery_tried_pass2 = True
                        recovery_out, recovery_eval_count = (
                            _s4_p2_rec.try_step4_failed_pass2_route_recovery_ctx(
                                ctx,
                                state,
                                stub_job,
                                raw_goal_primary=set(raw_goal),
                                dijkstra_fn=_dijkstra_route,
                            )
                        )
                        recovery_variant_eval_sum += recovery_eval_count
                        if recovery_out is not None:
                            recovery_success += 1
                            job_recovery_last_mode = recovery_out.recovery_search_mode
                            job_recovery_last_err = recovery_out.recovery_last_error
                            recovery_last_mode = job_recovery_last_mode
                            recovery_last_error = job_recovery_last_err
                            path = recovery_out.path
                            stub_cell = recovery_out.new_stub_cell
                            state.replace_provisional_stub(placement_id, stub_cell=stub_cell)
                            recovered = True
                        else:
                            recovery_rejected += 1
                            job_recovery_last_mode = "pass2_recovery:exhausted"
                            job_recovery_last_err = (
                                "step4_unreachable_component"
                                if step4_unreachable_trap
                                else str(detail.get("last_error") or "no_route")
                            )
                            recovery_last_mode = job_recovery_last_mode
                            recovery_last_error = job_recovery_last_err
                if not recovered and placement_id is not None and placement_id in work_records:
                    rec_bridge = work_records[placement_id]
                    if (
                        rec_bridge.placement_pass == "pass2"
                        and rec_bridge.state == PlacementCommitState.PROVISIONAL_PLACED
                    ):
                        bridge_out, bridge_reason, bridge_attempted_flag, bridge_meta = (
                            _s4_lb.try_step4_local_bridge_recovery_ctx(
                                ctx,
                                state,
                                stub_job,
                                blocked=blocked,
                                trunk_cells=trunk_cells,
                                goal_cells=goal_cells,
                                raw_goal=set(raw_goal),
                                want_role=want_role,
                                detail=detail,
                                search_stats=search_stats,
                                committed_trunk_for_kind=set(committed_trunk_by_kind.get(tk, ())),
                            )
                        )
                        if bridge_attempted_flag:
                            lb_attempted += 1
                        if bridge_out is not None:
                            lb_success += 1
                            recovery_out = bridge_out
                            path = bridge_out.path
                            stub_cell = bridge_out.new_stub_cell
                            recovered = True
                            job_recovery_last_mode = bridge_out.recovery_search_mode
                            job_recovery_last_err = None
                            recovery_last_mode = job_recovery_last_mode
                            recovery_last_error = job_recovery_last_err
                            recovery_variant_eval_sum += bridge_out.recovery_variant_eval_count
                        elif bridge_attempted_flag:
                            lb_rejected += 1
                            rk = bridge_reason or "unknown"
                            lb_failure_reasons[rk] = lb_failure_reasons.get(rk, 0) + 1
                            if len(lb_samples) < 8 and bridge_meta is not None:
                                smp = dict(bridge_meta)
                                smp["placement_id"] = placement_id
                                lb_samples.append(smp)
                if recovered and recovery_out is not None:
                    if recovery_out.recovery_search_mode.startswith("local_bridge"):
                        search_stats = {"search_mode": recovery_out.recovery_search_mode}
                    else:
                        search_stats = {
                            "search_mode": f"pass2_recovery:{recovery_out.recovery_search_mode}"
                        }
                if not recovered:
                    replacement_attempted = recovery_tried_pass2 or bridge_attempted_flag
                    if replacement_attempted:
                        _s4_fail_detail.apply_routing_failure_detail_lifecycle(
                            detail,
                            replacement_search_exhausted=True,
                        )
                    if placement_id is not None and placement_id in work_records:
                        rec = work_records[placement_id]
                        _rollback_placement_cells(cells, rec, final_cells, mineable)
                        state.mark_quarantined_unrouted(
                            placement_id,
                            rollback_reason=placement_rollback_reason,
                            context=placement_context,
                        )
                        quarantined.append(placement_id)
                        fd = placement_record_to_failure_dict(
                            work_records[placement_id],
                            reason=routing_fail_reason,
                        )
                        fd["step4_route_failure_detail"] = detail
                        fd["last_error"] = detail["last_error"]
                        fd["rejected_reason"] = routing_fail_reason
                        fd["rollback_reason"] = placement_rollback_reason
                        _s4_fail_detail.apply_routing_failure_detail_lifecycle(
                            detail,
                            quarantined=True,
                            placement_commit_state=work_records[placement_id].state.value,
                        )
                        rfd = detail.get("routing_failure_detail")
                        if isinstance(rfd, dict):
                            fd["routing_failure_detail"] = rfd
                        fd["step4_route_failure_diagnostic"] = build_step4_route_failure_diagnostic(
                            rec=work_records[placement_id],
                            extractor_cell=ext_cell,
                            stub_cell=stub_cell,
                            transport_kind=tk,
                            want_role=want_role,
                            raw_goal=set(raw_goal),
                            goal_cells=goal_cells,
                            trunk_cells=trunk_cells,
                            trunk_seed_candidates_by_kind=trunk_seed_by_kind,
                            margin_cells=margin_cells,
                            committed_trunk_for_kind=set(committed_trunk_by_kind.get(tk, ())),
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
                        fd["step4_failed_route_recovery"] = {
                            "attempted": recovery_tried_pass2,
                            "success": False,
                            "recovery_search_mode": job_recovery_last_mode,
                            "recovery_last_error": job_recovery_last_err,
                            "recovery_variant_eval_count": recovery_eval_count,
                        }
                        fd["step4_local_bridge_recovery"] = {
                            "attempted": bridge_attempted_flag,
                            "success": False,
                            "reason": bridge_reason,
                            "meta": bridge_meta,
                        }
                        if is_hard_protected_stub_ring_failure(detail):
                            fd["step4_hard_protected_no_route_trace"] = (
                                _s4_hp_diag.build_step4_hard_protected_ring_trace_fields(
                                    detail=detail,
                                    stub_cell=stub_cell,
                                    trunk_cells=trunk_cells,
                                    hard_extras=hard_extras,
                                    existing_layout_analysis=existing_layout_analysis,
                                )
                            )
                        failures.append(fd)
                    else:
                        unrecoverable = True
                        fd_unrec: dict[str, Any] = {
                            "extractor_cell": list(ext_cell),
                            "stub_cell": list(stub_cell),
                            "transport_kind": tk,
                            "reason": routing_fail_reason,
                            "unrecoverable": True,
                            "last_error": detail["last_error"],
                            "recovery_trigger": RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE,
                            "step4_route_failure_detail": detail,
                            "rejected_reason": routing_fail_reason,
                        }
                        rfd_u = detail.get("routing_failure_detail")
                        if isinstance(rfd_u, dict):
                            fd_unrec["routing_failure_detail"] = rfd_u
                        fd_unrec["step4_route_failure_diagnostic"] = (
                            build_step4_route_failure_diagnostic(
                                rec=None,
                                extractor_cell=ext_cell,
                                stub_cell=stub_cell,
                                transport_kind=tk,
                                want_role=want_role,
                                raw_goal=set(raw_goal),
                                goal_cells=goal_cells,
                                trunk_cells=trunk_cells,
                                trunk_seed_candidates_by_kind=trunk_seed_by_kind,
                                margin_cells=margin_cells,
                                committed_trunk_for_kind=set(committed_trunk_by_kind.get(tk, ())),
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
                        )
                        if is_hard_protected_stub_ring_failure(detail):
                            fd_unrec["step4_hard_protected_no_route_trace"] = (
                                _s4_hp_diag.build_step4_hard_protected_ring_trace_fields(
                                    detail=detail,
                                    stub_cell=stub_cell,
                                    trunk_cells=trunk_cells,
                                    hard_extras=hard_extras,
                                    existing_layout_analysis=existing_layout_analysis,
                                )
                            )
                        failures.append(fd_unrec)
                    continue

            assert path is not None

            if recovered:
                blocked_m = set(_blocked_cells(cells)) | set(hard_extras)
                blocked_m.discard(stub_cell)
                transport_m = _same_kind_transport_cells(cells, want_role)
                trunk_for_merge = frozenset(
                    transport_cells_reaching_external(
                        transport_m, set(frozenset(blocked_m)), is_external
                    )
                )
            else:
                trunk_for_merge = trunk_cells

            merged = any(p != stub_cell and p in transport_before for p in path) or bool(
                trunk_for_merge.intersection(path)
            )

            _s4_p2_rec.apply_pass2_recovery_path_paint(
                path=path,
                want_role=want_role,
                surface=surface,
                cells=cells,
                trunk_edge_hits=trunk_edge_hits,
            )

            routes_out.append(
                Step4Route(
                    extractor_cell=ext_cell,
                    stub_cell=stub_cell,
                    transport_kind=tk,
                    path=path,
                    merged_to_existing=merged,
                    reached_external=True,
                    placement_id=placement_id,
                )
            )
            state.note_route_path_committed(tk, path)
            if placement_id is not None:
                routes_by_placement_id[placement_id] = [[int(a), int(b)] for a, b in path]
            if placement_id is not None and placement_id in work_records:
                state.mark_routed_confirmed(
                    placement_id,
                    route_id=f"route-{placement_id}",
                    context="step4_path_routed",
                )

        routes_out, p2c_metrics = _p2c_revalidate_and_correct(
            cells,
            routes_out,
            work_records,
            mineable=mineable,
            asteroid=asteroid,
            final_cells=final_cells,
            is_external=is_external,
            surface=surface,
            failures=failures,
            trunk_edge_hits=trunk_edge_hits,
        )

        # Edge load is derived from final routes_out after P2-C corrections so
        # trunk_load/replay reflects returned route paths, not provisional commits.
        state.trunk.reset_edge_load_after_p2c()

        def _route_extractor_maximized(ext_cell: Coord, pid: str | None) -> bool:
            if ext_cell in maximized_extractor_cache:
                return maximized_extractor_cache[ext_cell]
            v = route_extractor_is_maximized_group(
                extractor_cell=ext_cell,
                placement_id=pid,
                placement_records=work_records,
                cells=cells,
            )
            maximized_extractor_cache[ext_cell] = v
            return bool(v)

        for rt in routes_out:
            accumulate_trunk_edge_load(trunk_edge_load_by_kind, rt.transport_kind, rt.path)
            if _route_extractor_maximized(rt.extractor_cell, rt.placement_id):
                accumulate_trunk_edge_load(
                    trunk_edge_load_maximized_by_kind, rt.transport_kind, rt.path
                )

        # QUARANTINED_UNROUTED is non-terminal (unfinalized_placement_count / STEP9). Spatial
        # rollback already ran; align FSM with P2-C cascade rollbacks — terminal ROLLED_BACK only.
        state.quarantined_placement_ids_peak = tuple(quarantined)
        if quarantined:
            for pid in list(quarantined):
                qrec = work_records.get(pid)
                if qrec is None or qrec.state != PlacementCommitState.QUARANTINED_UNROUTED:
                    continue
                work_records[pid] = transition_placement_record_to_rolled_back(qrec)
                rolled_back.append(pid)
            quarantined.clear()

        for fd in failures:
            eid = fd.get("extractor_id")
            if isinstance(eid, str) and eid in work_records:
                st = work_records[eid].state.value
                fd["final_state"] = st
                fd["state"] = st
                if st == PlacementCommitState.ROLLED_BACK.value:
                    _s4_fail_detail.patch_failure_row_routing_failure_detail_rolled_back(fd)
                _s4_fail_detail.sync_routing_failure_detail_placement_commit_state(fd, st)
                dig = fd.get("step4_route_failure_diagnostic")
                if isinstance(dig, dict):
                    dig["final_state"] = st

        per_pid_attempt: dict[str, int] = {}
        for fd in failures:
            det = fd.get("step4_route_failure_detail")
            if not isinstance(det, dict):
                continue
            eid = fd.get("extractor_id")
            if isinstance(eid, str):
                nxt = per_pid_attempt.get(eid, 0) + 1
                per_pid_attempt[eid] = nxt
                ai = nxt
            else:
                ai = 1
            _s4_fail_detail.stamp_final_step4_route_failure_detail_trace_from_fd(
                fd, attempt_index=ai
            )
            if trace_enabled():
                debug_log_event(
                    "django_apps.shapez_asteroid.services.asteroid_mining_layout."
                    "step4.step4_merge_routing",
                    "step4_route_failure_detail",
                    {"step4_route_failure_detail": det},
                )

        _stamp_placement_commit_on_map_rows(cells, work_records)

        out_rows = _rows_from_cells(cells)
        if mutate_input_map:
            map_after_pass2[:] = out_rows
            map_after_routing: list[dict[str, Any]] = map_after_pass2
        else:
            map_after_routing = out_rows
    except BaseException:
        state.cells.clear()
        state.cells.update(_baseline_cells_copy(state.baseline_cells))
        state.work_records.clear()
        state.work_records.update(state.baseline_wr)
        raise

    placement_commit_by_id = {pid: rec.state.value for pid, rec in work_records.items()}
    pcounts = placement_commit_counts_by_state(placement_commit_by_id)
    routing_failure_count = len(failures)
    rolled_back_n = len(rolled_back)
    complete_routing_success = (
        not unrecoverable and routing_failure_count == 0 and rolled_back_n == 0
    )
    committed = complete_routing_success
    step4_degraded = not unrecoverable and routing_failure_count == 0 and rolled_back_n > 0
    q_peak_n = len(state.quarantined_placement_ids_peak)

    # trunk_load schema: ``step4_trunk_load`` (route_metrics vs legacy aliases, per-kind blocks).
    trace_tl: dict[str, Any] = {
        "mode": "accumulate_only",
        "step4_route_count": len(routes_out),
        "step4_route_commit_count": len(routes_out),
        "step4_routing_failure_count": routing_failure_count,
        "initial_trunk_cells": len(initial_trunk),
        "placement_commit_counts": pcounts,
        "unfinalized_placement_count": unfinalized_placement_count_from_counts(pcounts),
        "step4_routed_count": pcounts.get(PlacementCommitState.ROUTED_CONFIRMED.value, 0),
        "step4_routed_stub_count": pcounts.get(PlacementCommitState.ROUTED_CONFIRMED.value, 0),
        "step4_total_stub_count": len(jobs),
        "step4_quarantined_peak_count": q_peak_n,
        "step4_quarantined_placement_ids_peak": list(state.quarantined_placement_ids_peak),
        "step4_quarantined_count": q_peak_n,
        "step4_quarantined_unrouted_count": q_peak_n,
        "step4_rolled_back_count": rolled_back_n,
        "step4_committed": committed,
        "step4_complete_routing_success": complete_routing_success,
        "step4_degraded": step4_degraded,
        "step4_state_source": {
            "committed_from": "step4_merge_routing",
            "trunk_load_mirrors_result": True,
        },
        "step4_trunk_seed_candidate_count_by_kind": {
            k: len(v) for k, v in trunk_seed_by_kind.items()
        },
        "step4_trunk_seed_candidate_count": max(
            (len(trunk_seed_by_kind.get(k, ())) for k in ("shape_belt", "fluid_pipe")),
            default=0,
        ),
        "step4_goal_set_size_peak": max(goal_set_sizes) if goal_set_sizes else 0,
        "step4_failed_route_recovery_attempted_count": recovery_attempted,
        "step4_failed_route_recovery_success_count": recovery_success,
        "step4_failed_route_recovery_rejected_count": recovery_rejected,
        "recovery_search_mode": recovery_last_mode,
        "recovery_last_error": recovery_last_error,
        "step4_failed_route_recovery_variant_eval_sum": recovery_variant_eval_sum,
        "routes_by_placement_id": dict(routes_by_placement_id),
        "step4_local_bridge_recovery_attempted_count": lb_attempted,
        "step4_local_bridge_recovery_success_count": lb_success,
        "step4_local_bridge_recovery_rejected_count": lb_rejected,
        "step4_local_bridge_recovery_failure_reasons": dict(lb_failure_reasons),
        "step4_local_bridge_recovery_samples": list(lb_samples),
        "step4_search_goal_ordering_applied": bool(search_goal_ordering_applied_any),
        "step4_search_goal_ordering_mode": search_goal_ordering_mode,
        "step4_search_diagnostics_samples": list(search_diag_samples),
        "step4_reentry_index": int(step4_reentry_index),
    }
    trace_tl["step4_no_route_exhausted_breakdown"] = build_step4_no_route_exhausted_breakdown(
        failures
    )
    trace_tl["step4_hard_protected_no_route_breakdown"] = (
        build_step4_hard_protected_no_route_breakdown(failures)
    )
    trunk_load = build_step4_trunk_load_for_merge_state(
        state,
        p2c_metrics=p2c_metrics,
        trace=trace_tl,
    )

    result = Step4RoutingResult(
        committed=committed,
        map_after_routing=map_after_routing,
        routes=tuple(routes_out),
        routing_failures=tuple(failures),
        trunk_load=trunk_load,
        routing_state=_routing_state_from_committed_routes(
            tuple(routes_out),
            cells=cells,
            is_external=is_external,
            existing_layout_analysis=existing_layout_analysis,
        ),
        placement_commit_by_id=dict(placement_commit_by_id),
        rolled_back_placement_ids=tuple(rolled_back),
        quarantined_placement_ids=state.quarantined_placement_ids_peak,
        complete_routing_success=complete_routing_success,
        degraded=step4_degraded,
        quarantined_placement_ids_peak=state.quarantined_placement_ids_peak,
    )
    tid = _s4_rt.step4_primary_recovery_trigger_from_result(result)
    if tid is not None:
        tl_m = dict(result.trunk_load)
        tl_m["step4_primary_recovery_trigger"] = tid
        return replace(result, trunk_load=tl_m)
    return result


def step4_routing_skipped_result(map_after_pass2: list[dict[str, Any]]) -> Step4RoutingResult:
    """Timeline/summary contract when Pass12 skipped mixed surface (no STEP4 work)."""

    return Step4RoutingResult(
        committed=True,
        map_after_routing=[dict(r) for r in map_after_pass2],
        routes=tuple(),
        routing_failures=tuple(),
        trunk_load=build_step4_trunk_load_skipped(),
        routing_state=None,
        placement_commit_by_id={},
        rolled_back_placement_ids=tuple(),
        quarantined_placement_ids=tuple(),
        complete_routing_success=True,
        degraded=False,
        quarantined_placement_ids_peak=tuple(),
    )
