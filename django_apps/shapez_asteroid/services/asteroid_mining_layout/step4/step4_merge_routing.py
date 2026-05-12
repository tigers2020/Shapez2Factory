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

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.extractor_extension_group import (  # noqa: E501
    route_extractor_is_maximized_group,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitRecord,
    PlacementCommitState,
    placement_commit_counts_by_state,
    placement_record_to_failure_dict,
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
    step4_route_failure_detail as _s4_fail_detail,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_contracts import (
    Step4Route,
    Step4RoutingResult,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_dijkstra import (
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
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_route_failure_diagnostic import (  # noqa: E501
    build_step4_no_route_exhausted_breakdown,
    build_step4_route_failure_diagnostic,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_routing_state import (
    _routing_state_from_committed_routes,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_trunk_load import (
    accumulate_trunk_edge_load,
    build_step4_trunk_load,
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

    margin_cells = exterior_margin_cells(
        mineable=mineable, asteroid=asteroid, cells=cells, is_external=is_external
    )
    hint_union = trunk_seed_union_from_existing_layout(existing_layout_analysis)
    cheap_reuse_cells = frozenset(set(initial_trunk) | set(hint_union))
    trunk_seed_by_kind = build_trunk_seed_candidates_by_kind(
        exterior_margin=margin_cells,
        hint_union=hint_union,
        cells=cells,
    )
    committed_trunk_by_kind: dict[str, set[Coord]] = {}
    final_route_cells: set[Coord] = set()
    route_visits_by_kind: dict[str, int] = {}
    unique_cells_by_kind: dict[str, set[Coord]] = {}
    routes_by_placement_id: dict[str, list[list[int]]] = {}
    goal_set_sizes: list[int] = []
    # Sum of len(path) over committed routes (merge stub counts as 1); shared cells double-count.
    accumulated_route_cell_visits = 0
    hard_extras = frozenset(hard_protected_cells or ())

    routes_out: list[Step4Route] = []
    failures: list[dict[str, Any]] = []
    trunk_edge_hits: dict[str, int] = {}
    trunk_edge_load_by_kind: dict[str, dict[str, int]] = {}
    trunk_edge_load_maximized_by_kind: dict[str, dict[str, int]] = {}
    maximized_extractor_cache: dict[Coord, bool] = {}
    p2c_metrics: dict[str, Any] = {
        "route_revalidation_passed": True,
        "broken_routed_route_count": 0,
        "cascade_corrective_attempts": 0,
        "cascade_reroute_count": 0,
        "cascade_rollback_count": 0,
        "cascade_rolled_back_placement_ids": tuple(),
        "cascade_route_replay_detail": [],
    }
    rolled_back: list[str] = []
    quarantined: list[str] = []
    quarantined_placement_ids_peak: tuple[str, ...] = ()
    unrecoverable = False
    recovery_attempted = 0
    recovery_success = 0
    recovery_rejected = 0
    recovery_last_error: str | None = None
    recovery_last_mode: str | None = None
    recovery_variant_eval_sum = 0

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
                force_route_attempt_placement_ids is not None
                and placement_id is not None
                and placement_id in force_route_attempt_placement_ids
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
                    work_records[placement_id] = replace(
                        work_records[placement_id],
                        state=PlacementCommitState.ROUTED_CONFIRMED,
                        route_id=rid,
                    )
                    committed_trunk_by_kind.setdefault(tk, set()).add(stub_cell)
                    final_route_cells.add(stub_cell)
                    routes_by_placement_id[placement_id] = [list(stub_cell)]
                    accumulated_route_cell_visits += 1
                    route_visits_by_kind[tk] = route_visits_by_kind.get(tk, 0) + 1
                    unique_cells_by_kind.setdefault(tk, set()).add(stub_cell)
                continue

            raw_goal = build_step4_goal_set(
                tk,
                committed_trunk_by_kind=committed_trunk_by_kind,
                exterior_margin_cells=margin_cells,
                trunk_seed_candidates_by_kind=trunk_seed_by_kind,
            )
            goal_cells = frozenset(raw_goal | set(trunk_cells))
            goal_set_sizes.append(len(goal_cells))

            search_stats: dict[str, Any] = {"search_mode": "goal_cells_union_legacy"}
            path = _dijkstra_route(
                stub_cell,
                want_role=want_role,
                cells=cells,
                blocked=blocked,
                mineable=mineable,
                asteroid=asteroid,
                is_external=is_external,
                trunk=trunk_cells,
                goal_cells=goal_cells,
                cheap_reuse_cells=cheap_reuse_cells,
                search_stats=search_stats,
            )
            recovery_out = None
            recovery_eval_count = 0
            if path is None:
                detail = _s4_fail_detail.build_step4_route_failure_detail(
                    placement_id=placement_id,
                    extractor_cell=ext_cell,
                    stub_cell=stub_cell,
                    transport_kind=tk,
                    want_role=want_role,
                    blocked=blocked,
                    hard_extras=hard_extras,
                    trunk_cells=trunk_cells,
                    goal_cells=goal_cells,
                    margin_cells=margin_cells,
                    transport_now=transport_now,
                    cells=cells,
                    mineable=mineable,
                    asteroid=asteroid,
                    is_external=is_external,
                    cheap_reuse_cells=cheap_reuse_cells,
                    search_stats=search_stats,
                )
                if trace_enabled():
                    debug_log_event(
                        "django_apps.shapez_asteroid.services.asteroid_mining_layout."
                        "step4.step4_merge_routing",
                        "step4_route_failure_detail",
                        {"step4_route_failure_detail": detail},
                    )
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
                            _s4_p2_rec.try_step4_failed_pass2_route_recovery(
                                ext_cell=ext_cell,
                                stub_cell=stub_cell,
                                tk=tk,
                                rec=rec0,
                                cells=cells,
                                final_cells=final_cells,
                                mineable=mineable,
                                asteroid=asteroid,
                                is_external=is_external,
                                committed_trunk_by_kind=committed_trunk_by_kind,
                                margin_cells=margin_cells,
                                trunk_seed_by_kind=trunk_seed_by_kind,
                                cheap_reuse_cells=cheap_reuse_cells,
                                hard_extras=hard_extras,
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
                            work_records[placement_id] = replace(
                                rec0,
                                stub_cell=stub_cell,
                            )
                            recovered = True
                        else:
                            recovery_rejected += 1
                            job_recovery_last_mode = "pass2_recovery:exhausted"
                            job_recovery_last_err = str(detail.get("last_error") or "no_route")
                            recovery_last_mode = job_recovery_last_mode
                            recovery_last_error = job_recovery_last_err
                if recovered and recovery_out is not None:
                    search_stats = {
                        "search_mode": f"pass2_recovery:{recovery_out.recovery_search_mode}"
                    }
                if not recovered:
                    if placement_id is not None and placement_id in work_records:
                        rec = work_records[placement_id]
                        _rollback_placement_cells(cells, rec, final_cells, mineable)
                        work_records[placement_id] = replace(
                            rec,
                            state=PlacementCommitState.QUARANTINED_UNROUTED,
                            rollback_reason="no_route",
                        )
                        quarantined.append(placement_id)
                        fd = placement_record_to_failure_dict(
                            work_records[placement_id],
                            reason="no_route",
                        )
                        fd["step4_route_failure_detail"] = detail
                        fd["last_error"] = detail["last_error"]
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
                        failures.append(fd)
                    else:
                        unrecoverable = True
                        fd_unrec: dict[str, Any] = {
                            "extractor_cell": list(ext_cell),
                            "stub_cell": list(stub_cell),
                            "transport_kind": tk,
                            "reason": "no_route",
                            "unrecoverable": True,
                            "last_error": detail["last_error"],
                            "step4_route_failure_detail": detail,
                        }
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
            committed_trunk_by_kind.setdefault(tk, set()).update(path)
            final_route_cells.update(path)
            accumulated_route_cell_visits += len(path)
            route_visits_by_kind[tk] = route_visits_by_kind.get(tk, 0) + len(path)
            unique_cells_by_kind.setdefault(tk, set()).update(path)
            if placement_id is not None:
                routes_by_placement_id[placement_id] = [[int(a), int(b)] for a, b in path]
            if placement_id is not None and placement_id in work_records:
                work_records[placement_id] = replace(
                    work_records[placement_id],
                    state=PlacementCommitState.ROUTED_CONFIRMED,
                    route_id=f"route-{placement_id}",
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
        trunk_edge_load_by_kind.clear()
        trunk_edge_load_maximized_by_kind.clear()
        maximized_extractor_cache.clear()

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
            return v

        for rt in routes_out:
            accumulate_trunk_edge_load(trunk_edge_load_by_kind, rt.transport_kind, rt.path)
            if _route_extractor_maximized(rt.extractor_cell, rt.placement_id):
                accumulate_trunk_edge_load(
                    trunk_edge_load_maximized_by_kind, rt.transport_kind, rt.path
                )

        # QUARANTINED_UNROUTED is non-terminal (unfinalized_placement_count / STEP9). Spatial
        # rollback already ran; align FSM with P2-C cascade rollbacks — terminal ROLLED_BACK only.
        quarantined_placement_ids_peak = tuple(quarantined)
        if quarantined:
            for pid in list(quarantined):
                qrec = work_records.get(pid)
                if qrec is None or qrec.state != PlacementCommitState.QUARANTINED_UNROUTED:
                    continue
                work_records[pid] = replace(
                    qrec,
                    state=PlacementCommitState.ROLLED_BACK,
                    route_id=None,
                )
                rolled_back.append(pid)
            quarantined.clear()

        for fd in failures:
            eid = fd.get("extractor_id")
            if isinstance(eid, str) and eid in work_records:
                st = work_records[eid].state.value
                fd["final_state"] = st
                fd["state"] = st
                dig = fd.get("step4_route_failure_diagnostic")
                if isinstance(dig, dict):
                    dig["final_state"] = st

        _stamp_placement_commit_on_map_rows(cells, work_records)

        out_rows = _rows_from_cells(cells)
        if mutate_input_map:
            map_after_pass2[:] = out_rows
            map_after_routing: list[dict[str, Any]] = map_after_pass2
        else:
            map_after_routing = out_rows
    except BaseException:
        cells.clear()
        cells.update(_baseline_cells_copy(baseline_cells))
        work_records.clear()
        work_records.update(baseline_wr)
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
    q_peak_n = len(quarantined_placement_ids_peak)

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
        "step4_quarantined_placement_ids_peak": list(quarantined_placement_ids_peak),
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
    }
    trace_tl["step4_no_route_exhausted_breakdown"] = build_step4_no_route_exhausted_breakdown(
        failures
    )
    trunk_load = build_step4_trunk_load(
        trunk_edge_hits=trunk_edge_hits,
        route_cell_visits=accumulated_route_cell_visits,
        final_route_cells=final_route_cells,
        committed_trunk_by_kind=committed_trunk_by_kind,
        route_visits_by_kind=route_visits_by_kind,
        unique_cells_by_kind=unique_cells_by_kind,
        p2c_metrics=p2c_metrics,
        trace=trace_tl,
        trunk_edge_load_by_kind=trunk_edge_load_by_kind,
        trunk_edge_load_maximized_by_kind=trunk_edge_load_maximized_by_kind,
    )

    return Step4RoutingResult(
        committed=committed,
        map_after_routing=map_after_routing,
        routes=tuple(routes_out),
        routing_failures=tuple(failures),
        trunk_load=trunk_load,
        routing_state=_routing_state_from_committed_routes(
            tuple(routes_out),
            cells=cells,
            is_external=is_external,
        ),
        placement_commit_by_id=dict(placement_commit_by_id),
        rolled_back_placement_ids=tuple(rolled_back),
        quarantined_placement_ids=quarantined_placement_ids_peak,
        complete_routing_success=complete_routing_success,
        degraded=step4_degraded,
        quarantined_placement_ids_peak=quarantined_placement_ids_peak,
    )


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
