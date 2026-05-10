"""STEP4 merge-aware stub→external routing (Dijkstra) + placement commit FSM (P2-B).

Routes each Pass12 ``placement_id`` bundle; failures quarantine then roll back that bundle
only (extractor, extensions, output stub) while keeping other routes.

권한(셀 점유·목표 판정): ``step4_routing_permission``. 그래프 탐색: ``step4_dijkstra``.
P2-C 교정: ``step4_p2c_corrective``. 맵 조작·스냅샷: ``step4_map_ops``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Any

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
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_contracts import (
    Step4Route,
    Step4RoutingResult,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_dijkstra import (
    dijkstra_route_step4,
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
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_routing_state import (
    _routing_state_from_committed_routes,
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
    "run_step4_merge_aware_routing",
    "step4_routing_skipped_result",
]


def run_step4_merge_aware_routing(
    map_after_pass2: list[dict[str, Any]],
    *,
    final_mining_map: list[dict[str, Any]],
    is_external: Callable[[Coord], bool],
    placement_records: dict[str, PlacementCommitRecord] | None = None,
    force_route_attempt_placement_ids: frozenset[str] | None = None,
    mutate_input_map: bool = False,
) -> Step4RoutingResult:
    """Route each extractor stub; roll back failed ``placement_id`` bundles only (P2-B).

    ``force_route_attempt_placement_ids`` (optional): do not take the ``stub in trunk`` merge
    shortcut for these ids — forces a full Dijkstra attempt (unit tests / diagnostics).

    ``mutate_input_map``: when True, replace ``map_after_pass2`` rows in place with the routed
    layout on success (for ``SolverMutationTransaction`` / rollback on exception).
    On any exception, in-memory ``cells`` and ``work_records`` are restored to entry baselines
    before re-raising.
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
    blocked_set = _blocked_cells(cells)
    blocked = frozenset(blocked_set)
    initial_trunk = frozenset(
        transport_cells_reaching_external(set(transport0), set(blocked), is_external)
    )

    routes_out: list[Step4Route] = []
    failures: list[dict[str, Any]] = []
    trunk_edge_hits: dict[str, int] = {}
    rolled_back: list[str] = []
    quarantined: list[str] = []
    unrecoverable = False

    try:
        for ext_cell, stub_cell, tk, placement_id in jobs:
            want_role = _want_role(tk)
            blocked = frozenset(_blocked_cells(cells))
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
                continue

            path = _dijkstra_route(
                stub_cell,
                want_role=want_role,
                cells=cells,
                blocked=blocked,
                mineable=mineable,
                asteroid=asteroid,
                is_external=is_external,
                trunk=trunk_cells,
            )
            if path is None:
                if placement_id is not None and placement_id in work_records:
                    rec = work_records[placement_id]
                    work_records[placement_id] = replace(
                        rec,
                        state=PlacementCommitState.QUARANTINED_UNROUTED,
                        rollback_reason="no_route",
                    )
                    quarantined.append(placement_id)
                    _rollback_placement_cells(cells, rec, final_cells, mineable)
                    work_records[placement_id] = replace(
                        work_records[placement_id],
                        state=PlacementCommitState.ROLLED_BACK,
                        rollback_reason="no_route",
                    )
                    rolled_back.append(placement_id)
                    failures.append(
                        placement_record_to_failure_dict(
                            work_records[placement_id],
                            reason="no_route",
                        )
                    )
                else:
                    unrecoverable = True
                    failures.append(
                        {
                            "extractor_cell": list(ext_cell),
                            "stub_cell": list(stub_cell),
                            "transport_kind": tk,
                            "reason": "no_route",
                            "unrecoverable": True,
                        }
                    )
                continue

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

    trunk_load: dict[str, Any] = {
        "mode": "accumulate_only",
        "edges": dict(sorted(trunk_edge_hits.items())),
        "step4_route_count": len(routes_out),
        "step4_routing_failure_count": len(failures),
        "initial_trunk_cells": len(initial_trunk),
        "placement_commit_counts": pcounts,
        "unfinalized_placement_count": unfinalized_placement_count_from_counts(pcounts),
        "step4_routed_count": pcounts.get(PlacementCommitState.ROUTED_CONFIRMED.value, 0),
        "step4_rolled_back_count": len(rolled_back),
        "step4_quarantined_count": len(quarantined),
        **p2c_metrics,
    }

    committed = not unrecoverable

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
        quarantined_placement_ids=tuple(quarantined),
    )


def step4_routing_skipped_result(map_after_pass2: list[dict[str, Any]]) -> Step4RoutingResult:
    """Timeline/summary contract when Pass12 skipped mixed surface (no STEP4 work)."""

    return Step4RoutingResult(
        committed=True,
        map_after_routing=[dict(r) for r in map_after_pass2],
        routes=tuple(),
        routing_failures=tuple(),
        trunk_load={
            "mode": "accumulate_only",
            "edges": {},
            "step4_route_count": 0,
            "step4_routing_failure_count": 0,
            "skipped": True,
            "placement_commit_counts": placement_commit_counts_by_state({}),
            "unfinalized_placement_count": 0,
            "step4_routed_count": 0,
            "step4_rolled_back_count": 0,
            "step4_quarantined_count": 0,
            "route_revalidation_passed": True,
            "broken_routed_route_count": 0,
            "cascade_corrective_attempts": 0,
            "cascade_reroute_count": 0,
            "cascade_rollback_count": 0,
            "cascade_rolled_back_placement_ids": tuple(),
            "cascade_route_replay_detail": [],
        },
        routing_state=None,
        placement_commit_by_id={},
        rolled_back_placement_ids=tuple(),
        quarantined_placement_ids=tuple(),
    )
