"""§14.3 soft-corridor atomic replace (shared routing; P4 reclaim, future Pass3/recovery)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    P4_REJECT_HARD_PROTECTED_CORRIDOR,
    P4_SOFT_REPLACE_REJECT_NO_REPLACEMENT_ROUTE,
    P4_SOFT_REPLACE_REJECT_NO_ROUTING_JOB,
    P4_SOFT_REPLACE_REJECT_OLD_NOT_SOFT_PROTECTED,
    P4_SOFT_REPLACE_REJECT_OLD_NOT_TRANSPORT,
    P4_SOFT_REPLACE_REJECT_REPLACEMENT_NOT_CONNECTED,
    P4_SOFT_REPLACE_REJECT_VALIDATION,
    P4_SOFT_REPLACE_ROUTE_PLACEMENT_ID,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_greedy_core import (
    pick_pass3_anchor_transport_cell,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_corridors import (
    protected_corridors_read_for_reclaim,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_map_ops import (
    _rebuild_mining_map_from_cells,
    _transport_role_dict_from_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_soft_replace_trace import (  # noqa: E501
    p4_soft_replace_neutral_trace,
    replacement_probe_path_cardinally_connected,
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


def _p4_soft_replace_neutral_trace(
    *,
    attempted: bool = False,
    committed: bool = False,
    rejected_reason: str | None = None,
    old_cells: list[list[int]] | None = None,
    new_cells: list[list[int]] | None = None,
    connected: bool | None = None,
    job_count: int = 0,
    jobs_attempted: int = 0,
    selected_job_index: int | None = None,
    rejected_reasons_by_job: list[str] | None = None,
) -> dict[str, Any]:
    """§14.3 trace keys for soft-corridor atomic replace (no commit / reject / neutral)."""

    return p4_soft_replace_neutral_trace(
        attempted=attempted,
        committed=committed,
        rejected_reason=rejected_reason,
        old_cells=old_cells,
        new_cells=new_cells,
        connected=connected,
        job_count=job_count,
        jobs_attempted=jobs_attempted,
        selected_job_index=selected_job_index,
        rejected_reasons_by_job=rejected_reasons_by_job,
    )


def _replacement_probe_path_cardinally_connected(path: list[Coord]) -> bool:
    """Stub→anchor replacement path must be a cardinal polyline (connectivity pre-gate)."""

    return replacement_probe_path_cardinally_connected(path)


def try_atomic_replace_soft_corridor(
    mining_map: list[dict[str, Any]],
    *,
    final_mining_map: list[dict[str, Any]],
    pass3_trace: dict[str, Any],
    solver_routing_state: Mapping[str, object] | None,
    old_soft_corridor_cells: list[Coord] | tuple[Coord, ...] | frozenset[Coord],
    is_external: Callable[[Coord], bool],
    existing_layout_solver_hints: Mapping[str, object] | None = None,
) -> tuple[list[dict[str, Any]] | None, dict[str, Any]]:
    """§14.3: compute replacement route while old soft corridor remains, validate, then swap.

    Returns ``(committed_map, trace)`` on success; ``(None, trace)`` on failure so the
    caller keeps the original ``mining_map`` unchanged. Never removes old corridor before a
    validated replacement exists.

    If ``old_soft_corridor_cells`` intersects the read hard pool, rejects with
    ``P4_REJECT_HARD_PROTECTED_CORRIDOR`` before the soft-pool subset check (§14.3).
    """

    def _cells_coord_list(cells: frozenset[Coord] | set[Coord]) -> list[list[int]]:
        ordered = sorted(cells, key=lambda p: (p[1], p[0]))
        return [[int(p[0]), int(p[1])] for p in ordered]

    old_set = frozenset(old_soft_corridor_cells)
    if not old_set:
        return None, _p4_soft_replace_neutral_trace(
            attempted=False,
            committed=False,
            rejected_reason=None,
            old_cells=[],
            new_cells=[],
            connected=None,
        )

    corridors = protected_corridors_read_for_reclaim(
        pass3_trace=pass3_trace,
        solver_routing_state=solver_routing_state,
        existing_layout_solver_hints=existing_layout_solver_hints,
    )
    if old_set & corridors.hard:
        return None, _p4_soft_replace_neutral_trace(
            attempted=True,
            committed=False,
            rejected_reason=P4_REJECT_HARD_PROTECTED_CORRIDOR,
            old_cells=_cells_coord_list(old_set),
            new_cells=[],
            connected=None,
        )
    if not old_set <= corridors.soft:
        return None, _p4_soft_replace_neutral_trace(
            attempted=True,
            committed=False,
            rejected_reason=P4_SOFT_REPLACE_REJECT_OLD_NOT_SOFT_PROTECTED,
            old_cells=_cells_coord_list(old_set),
            new_cells=[],
            connected=None,
        )

    raw = cells_dict_from_mining_map(mining_map)
    for c in old_set:
        row = raw.get(c)
        if row is None or row.get("role") not in ("belt", "pipe"):
            return None, _p4_soft_replace_neutral_trace(
                attempted=True,
                committed=False,
                rejected_reason=P4_SOFT_REPLACE_REJECT_OLD_NOT_TRANSPORT,
                old_cells=_cells_coord_list(old_set),
                new_cells=[],
                connected=None,
            )

    cells: dict[Coord, dict[str, Any]] = {k: dict(v) for k, v in raw.items()}
    jobs = _collect_routing_jobs(cells)
    if not jobs:
        return None, _p4_soft_replace_neutral_trace(
            attempted=True,
            committed=False,
            rejected_reason=P4_SOFT_REPLACE_REJECT_NO_ROUTING_JOB,
            old_cells=_cells_coord_list(old_set),
            new_cells=[],
            connected=None,
        )

    mineable, asteroid = _mineable_and_asteroid_coords(final_mining_map)
    probe_buildings: dict[Coord, str] = {
        c: str(cells.get(c, {}).get("role") or "layout_block") for c in _blocked_cells(cells)
    }
    for c in old_set:
        probe_buildings[c] = "layout_block"

    transport_cells = _transport_role_dict_from_map(mining_map)
    outlets_order = [j[1] for j in jobs]
    fixed_stubs = frozenset(outlets_order)
    final_cells = cells_dict_from_mining_map(final_mining_map)
    rejected_reasons_by_job: list[str] = []

    import django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow as _p4f  # noqa: E501

    for job_index, (_ext_cell, stub, tk, _placement_id) in enumerate(jobs):
        want_role_str = _want_role(tk)
        anchor_cell = pick_pass3_anchor_transport_cell(
            cells,
            want_role=want_role_str,
            is_external=is_external,
        )
        if anchor_cell is None:
            rejected_reasons_by_job.append(P4_SOFT_REPLACE_REJECT_NO_REPLACEMENT_ROUTE)
            continue

        path = _p4f.placement_stub_route_probe_path(
            outlet_stub=stub,
            anchor=anchor_cell,
            asteroid_cells=set(asteroid),
            mineable_cells=set(mineable),
            buildings=probe_buildings,
            transport_cells=transport_cells,
            fixed_stubs=fixed_stubs,
        )
        if path is None or len(path) < 2 or path[0] != stub:
            rejected_reasons_by_job.append(P4_SOFT_REPLACE_REJECT_NO_REPLACEMENT_ROUTE)
            continue

        connected_ok = _replacement_probe_path_cardinally_connected(path)
        if not connected_ok:
            rejected_reasons_by_job.append(P4_SOFT_REPLACE_REJECT_REPLACEMENT_NOT_CONNECTED)
            continue

        cells_try: dict[Coord, dict[str, Any]] = {k: dict(v) for k, v in cells.items()}
        for c in old_set:
            base = final_cells.get(c)
            if isinstance(base, dict):
                cells_try[c] = dict(base)
            else:
                cells_try[c] = {"x": c[0], "y": c[1], "role": "inferred"}

        stub_row = cells_try.get(stub)
        surface = str(
            (stub_row or {}).get("surface") or ("shape" if tk == "shape_belt" else "fluid")
        )

        new_added: list[list[int]] = []
        path_valid = True
        for p in path[1:]:
            row = cells_try.get(p)
            if row is not None and row.get("role") == want_role_str:
                continue
            if row is not None and row.get("role") in ("belt", "pipe"):
                if row.get("role") != want_role_str:
                    path_valid = False
                    break
                continue
            cells_try[p] = {
                "x": p[0],
                "y": p[1],
                "role": want_role_str,
                "surface": surface,
                "placement_id": P4_SOFT_REPLACE_ROUTE_PLACEMENT_ID,
            }
            new_added.append([p[0], p[1]])
        if not path_valid:
            rejected_reasons_by_job.append(P4_SOFT_REPLACE_REJECT_VALIDATION)
            continue

        map_try = _rebuild_mining_map_from_cells(cells_try)
        report = _p4f.validate_final_mining_layout(map_try)
        if not (report.geometry_valid and report.connectivity_valid):
            rejected_reasons_by_job.append(P4_SOFT_REPLACE_REJECT_VALIDATION)
            continue

        trace = _p4_soft_replace_neutral_trace(
            attempted=True,
            committed=True,
            rejected_reason=None,
            old_cells=_cells_coord_list(old_set),
            new_cells=new_added,
            connected=True,
            job_count=len(jobs),
            jobs_attempted=job_index + 1,
            selected_job_index=job_index,
            rejected_reasons_by_job=rejected_reasons_by_job,
        )
        return map_try, trace

    rejected_reason = (
        rejected_reasons_by_job[-1]
        if rejected_reasons_by_job
        else P4_SOFT_REPLACE_REJECT_NO_REPLACEMENT_ROUTE
    )
    return None, _p4_soft_replace_neutral_trace(
        attempted=True,
        committed=False,
        rejected_reason=rejected_reason,
        old_cells=_cells_coord_list(old_set),
        new_cells=[],
        connected=None,
        job_count=len(jobs),
        jobs_attempted=len(jobs),
        selected_job_index=None,
        rejected_reasons_by_job=rejected_reasons_by_job,
    )


__all__ = ["_p4_soft_replace_neutral_trace", "try_atomic_replace_soft_corridor"]
