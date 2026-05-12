"""STEP4 P2-C: reconnect ROUTED stubs after rollbacks (cascade reroute / rollback)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitRecord,
    PlacementCommitState,
    placement_record_to_failure_dict,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    blocked_cells as _blocked_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    want_role as _want_role,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import (
    solver_replay_events as _solver_replay_events,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_contracts import (
    Step4Route,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_map_ops import (
    rollback_placement_cells,
    same_kind_transport_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_route_failure_diagnostic import (  # noqa: E501
    build_step4_route_failure_diagnostic_p2c,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    transport_cells_reaching_external,
)

_MAX_P2C_CORRECTIVE_ATTEMPTS = 64


def _path_cells_diff_xy(
    old_path: tuple[Coord, ...], new_path: tuple[Coord, ...]
) -> tuple[list[list[int]], list[list[int]], list[list[int]]]:
    """JSON-friendly cell lists for replay v5 ``route_replaced`` (deterministic sort)."""

    old_s = frozenset(old_path)
    new_s = frozenset(new_path)
    removed = sorted(old_s - new_s)
    added = sorted(new_s - old_s)
    kept = sorted(old_s & new_s)
    return (
        [[c[0], c[1]] for c in removed],
        [[c[0], c[1]] for c in added],
        [[c[0], c[1]] for c in kept],
    )


def _facade_dijkstra(*args: Any, **kwargs: Any) -> tuple[Coord, ...] | None:
    """Delegate to ``step4_merge_routing._dijkstra_route`` so unit tests can patch the façade."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
        step4_merge_routing as step4_facade,
    )

    return step4_facade._dijkstra_route(*args, **kwargs)


def _facade_stub_reaches_external_trunk(*args: Any, **kwargs: Any) -> bool:
    """Delegate to ``step4_merge_routing._stub_reaches_external_trunk`` for patch targets."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
        step4_merge_routing as step4_facade,
    )

    return step4_facade._stub_reaches_external_trunk(*args, **kwargs)


def p2c_reroute_apply_path(
    path: tuple[Coord, ...],
    *,
    stub_cell: Coord,
    want_role: str,
    cells: dict[Coord, dict[str, Any]],
    surface: str,
    transport_before: frozenset[Coord],
    trunk_cells: frozenset[Coord],
    trunk_edge_hits: dict[str, int],
) -> tuple[bool, bool]:
    """Paint path cells; update trunk_edge_hits. Returns merged and reached_external flags."""

    merged = any(p != stub_cell and p in transport_before for p in path) or bool(
        trunk_cells.intersection(path)
    )
    for p in path:
        if p == stub_cell:
            continue
        row = cells.get(p)
        if row is not None and row.get("role") == want_role:
            key = f"{p[0]},{p[1]}"
            trunk_edge_hits[key] = trunk_edge_hits.get(key, 0) + 1
            continue
        cells[p] = {"x": p[0], "y": p[1], "role": want_role, "surface": surface}
    reached_external = True
    return merged, reached_external


def p2c_revalidate_and_correct(
    cells: dict[Coord, dict[str, Any]],
    routes_out: list[Step4Route],
    work_records: dict[str, PlacementCommitRecord],
    *,
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    final_cells: dict[Coord, dict[str, Any]],
    is_external: Callable[[Coord], bool],
    surface: str,
    failures: list[dict[str, Any]],
    trunk_edge_hits: dict[str, int],
) -> tuple[list[Step4Route], dict[str, Any]]:
    """Reconnect ROUTED stubs after rollbacks; reroute or cascade-rollback (P2-C)."""

    metrics: dict[str, Any] = {
        "route_revalidation_passed": True,
        "broken_routed_route_count": 0,
        "cascade_corrective_attempts": 0,
        "cascade_reroute_count": 0,
        "cascade_rollback_count": 0,
        "cascade_rolled_back_placement_ids": tuple(),
        "cascade_route_replay_detail": [],
    }
    replay_rows: list[dict[str, Any]] = metrics["cascade_route_replay_detail"]
    cascade_ids: list[str] = []
    attempts = 0
    max_broken = 0
    route_budget = max(4, len(routes_out) * 2)
    attempt_cap = min(_MAX_P2C_CORRECTIVE_ATTEMPTS, route_budget)

    while attempts < attempt_cap:
        broken: list[Step4Route] = []
        for rt in routes_out:
            pid = rt.placement_id
            if pid is None:
                continue
            rec = work_records.get(pid)
            if rec is None or rec.state != PlacementCommitState.ROUTED_CONFIRMED:
                continue
            wr = _want_role(rt.transport_kind)
            if _facade_stub_reaches_external_trunk(
                rt.stub_cell, cells=cells, want_role=wr, is_external=is_external
            ):
                continue
            broken.append(rt)

        if not broken:
            metrics["route_revalidation_passed"] = True
            metrics["broken_routed_route_count"] = max_broken
            metrics["cascade_corrective_attempts"] = attempts
            metrics["cascade_rolled_back_placement_ids"] = tuple(cascade_ids)
            return routes_out, metrics

        metrics["route_revalidation_passed"] = False
        max_broken = max(max_broken, len(broken))
        progress = False

        for br in broken:
            if attempts >= attempt_cap:
                break
            attempts += 1
            wr = _want_role(br.transport_kind)
            blocked = frozenset(_blocked_cells(cells))
            transport_now = same_kind_transport_cells(cells, wr)
            transport_before = frozenset(transport_now)
            trunk_cells = frozenset(
                transport_cells_reaching_external(transport_now, set(blocked), is_external)
            )
            path = _facade_dijkstra(
                br.stub_cell,
                want_role=wr,
                cells=cells,
                blocked=blocked,
                mineable=mineable,
                asteroid=asteroid,
                is_external=is_external,
                trunk=trunk_cells,
            )
            pid = br.placement_id
            if path is not None:
                merged, reached = p2c_reroute_apply_path(
                    path,
                    stub_cell=br.stub_cell,
                    want_role=wr,
                    cells=cells,
                    surface=surface,
                    transport_before=transport_before,
                    trunk_cells=trunk_cells,
                    trunk_edge_hits=trunk_edge_hits,
                )
                new_rt = Step4Route(
                    extractor_cell=br.extractor_cell,
                    stub_cell=br.stub_cell,
                    transport_kind=br.transport_kind,
                    path=path,
                    merged_to_existing=merged,
                    reached_external=reached,
                    placement_id=pid,
                )
                for i, r in enumerate(routes_out):
                    if r.placement_id == pid:
                        routes_out[i] = new_rt
                        break
                metrics["cascade_reroute_count"] += 1
                old_rid = (
                    work_records[pid].route_id if pid is not None and pid in work_records else None
                )
                stable_rid = f"route-{pid}" if pid is not None else None
                cells_removed, cells_added, cells_kept = _path_cells_diff_xy(br.path, path)
                replay_rows.append(
                    {
                        "placement_id": pid,
                        "old_route_id": old_rid or stable_rid,
                        "new_route_id": stable_rid,
                        "reason": "p2c_cascade_reroute",
                        "replacement_reason": "p2c_cascade_reroute",
                        "old_path_cell_count": len(br.path),
                        "new_path_cell_count": len(path),
                        "replacement_search_mode": "p2c_dijkstra_trunk",
                        "replacement_connectivity_preserved": bool(new_rt.reached_external),
                        "replacement_path_cell_delta": len(path) - len(br.path),
                        "replacement_cost_delta": None,
                        "cells_removed": cells_removed,
                        "cells_added": cells_added,
                        "cells_kept": cells_kept,
                        "transport_kind": _solver_replay_events.normalize_replay_transport_kind(
                            br.transport_kind
                        ),
                    }
                )
                progress = True
                continue

            if pid is not None and pid in work_records:
                rec = work_records[pid]
                rollback_placement_cells(cells, rec, final_cells, mineable)
                work_records[pid] = replace(
                    rec,
                    state=PlacementCommitState.ROLLED_BACK,
                    rollback_reason="p2c_trunk_disconnect",
                    route_id=None,
                )
                cascade_ids.append(pid)
                metrics["cascade_rollback_count"] += 1
                failures.append(
                    placement_record_to_failure_dict(
                        work_records[pid], reason="p2c_trunk_disconnect"
                    )
                    | {
                        "step4_route_failure_diagnostic": build_step4_route_failure_diagnostic_p2c(
                            rec=work_records[pid],
                            reason="p2c_trunk_disconnect",
                            final_state=PlacementCommitState.ROLLED_BACK.value,
                        ),
                    }
                )
                routes_out = [x for x in routes_out if x.placement_id != pid]
                progress = True

        if not progress:
            metrics["broken_routed_route_count"] = max_broken
            metrics["cascade_corrective_attempts"] = attempts
            metrics["cascade_rolled_back_placement_ids"] = tuple(cascade_ids)
            return routes_out, metrics

    metrics["broken_routed_route_count"] = max_broken
    metrics["cascade_corrective_attempts"] = attempts
    metrics["cascade_rolled_back_placement_ids"] = tuple(cascade_ids)
    return routes_out, metrics
