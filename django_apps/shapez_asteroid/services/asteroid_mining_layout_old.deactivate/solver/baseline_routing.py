"""Counterfactual STEP4-style shortest routing baseline (sequential trunk v1).

See ``documents/Algorithm/mining_solver_counterfactual_baseline_2026-05-10.md``.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    OPTIMIZATION_COUNTERFACTUAL_AGGREGATION_SEQUENTIAL_TRUNK_V1,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    blocked_cells,
    collect_routing_jobs,
    mineable_and_asteroid_coords,
    want_role,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_timeline import (
    count_internal_transport_tiles_for_kind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_dijkstra import (
    dijkstra_route_step4,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_map_ops import (
    same_kind_transport_cells,
    surface_for_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    cells_dict_from_mining_map,
    transport_cells_reaching_external,
)

COUNTERFACTUAL_FAIL_NO_ROUTING_JOBS = "counterfactual_no_routing_jobs"
COUNTERFACTUAL_FAIL_MIXED_TRANSPORT_KIND = "counterfactual_mixed_transport_kind"
COUNTERFACTUAL_FAIL_TRANSPORT_KIND_MISMATCH = "counterfactual_transport_kind_mismatch"
COUNTERFACTUAL_FAIL_NO_ROUTE = "counterfactual_no_route_for_job"


def _strip_belt_pipe_cells(cells: dict[Coord, dict[str, Any]]) -> dict[Coord, dict[str, Any]]:
    out: dict[Coord, dict[str, Any]] = {}
    for c, row in cells.items():
        if row.get("role") in ("belt", "pipe"):
            continue
        out[c] = dict(row)
    return out


def _sort_jobs(
    jobs: list[tuple[Coord, Coord, str, str | None]],
) -> list[tuple[Coord, Coord, str, str | None]]:
    def key(j: tuple[Coord, Coord, str, str | None]) -> tuple[Any, ...]:
        ext, stub, _tk, pid = j
        pid_s = pid if isinstance(pid, str) else ""
        return (stub[0], stub[1], ext[0], ext[1], pid_s)

    return sorted(jobs, key=key)


@dataclass(frozen=True)
class BaselineRoutingJobTrace:
    extractor_cell: Coord
    stub_cell: Coord
    transport_kind: str
    placement_id: str | None
    ok: bool
    path: tuple[Coord, ...] | None


@dataclass(frozen=True)
class BaselineRoutingResult:
    internal_transport_count: int | None
    aggregation: str
    transport_kind: str | None
    per_job: tuple[BaselineRoutingJobTrace, ...]
    failure_reason: str | None


def _sequential_trunk_paint_jobs(
    cells_sim: dict[Coord, dict[str, Any]],
    *,
    jobs_sorted: list[tuple[Coord, Coord, str, str | None]],
    tk: str,
    want_r: str,
    surface: str,
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    is_external: Callable[[Coord], bool],
) -> tuple[list[BaselineRoutingJobTrace], str | None]:
    """Return ``(traces, failure_reason)``; ``failure_reason`` set iff a job has no route."""

    traces_out: list[BaselineRoutingJobTrace] = []
    for ext_cell, stub_cell, _tk_job, placement_id in jobs_sorted:
        cells_sim[stub_cell] = {
            "x": stub_cell[0],
            "y": stub_cell[1],
            "role": want_r,
            "surface": surface,
        }
        blocked_set = blocked_cells(cells_sim)
        blocked = frozenset(blocked_set)
        transport_now = same_kind_transport_cells(cells_sim, want_r)
        trunk_cells = frozenset(
            transport_cells_reaching_external(
                set(transport_now),
                set(blocked_set),
                is_external,
            )
        )
        path = dijkstra_route_step4(
            stub_cell,
            want_role=want_r,
            cells=cells_sim,
            blocked=blocked,
            mineable=mineable,
            asteroid=asteroid,
            is_external=is_external,
            trunk=trunk_cells,
        )
        if path is None:
            traces_out.append(
                BaselineRoutingJobTrace(
                    extractor_cell=ext_cell,
                    stub_cell=stub_cell,
                    transport_kind=tk,
                    placement_id=placement_id,
                    ok=False,
                    path=None,
                )
            )
            return traces_out, COUNTERFACTUAL_FAIL_NO_ROUTE

        for p in path:
            if p == stub_cell:
                continue
            row = cells_sim.get(p)
            if row is not None and row.get("role") == want_r:
                continue
            cells_sim[p] = {"x": p[0], "y": p[1], "role": want_r, "surface": surface}

        traces_out.append(
            BaselineRoutingJobTrace(
                extractor_cell=ext_cell,
                stub_cell=stub_cell,
                transport_kind=tk,
                placement_id=placement_id,
                ok=True,
                path=tuple(path),
            )
        )
    return traces_out, None


def compute_shortest_feasible_transport_baseline(
    *,
    mining_map: list[dict[str, Any]],
    routing_jobs: Sequence[tuple[Coord, Coord, str, str | None]] | None,
    transport_kind: str | None,
    final_mining_map: list[dict[str, Any]],
    is_external: Callable[[Coord], bool],
) -> BaselineRoutingResult:
    """Strip belt/pipe, then run STEP4 Dijkstra per job in fixed order with trunk refresh.

    ``routing_jobs``: ``None`` 또는 빈 시퀀스면 ``mining_map``(strip 전)에서
    ``collect_routing_jobs``로 채운다. 한 job이라도 경로를 못 찾으면
    ``internal_transport_count``는 ``None``이다.
    """

    raw = cells_dict_from_mining_map(mining_map)
    cells_orig = {k: dict(v) for k, v in raw.items()}
    jobs: list[tuple[Coord, Coord, str, str | None]] = (
        list(routing_jobs)
        if routing_jobs is not None and len(routing_jobs) > 0
        else collect_routing_jobs(cells_orig)
    )
    if not jobs:
        return BaselineRoutingResult(
            internal_transport_count=None,
            aggregation=OPTIMIZATION_COUNTERFACTUAL_AGGREGATION_SEQUENTIAL_TRUNK_V1,
            transport_kind=None,
            per_job=(),
            failure_reason=COUNTERFACTUAL_FAIL_NO_ROUTING_JOBS,
        )

    kinds = {j[2] for j in jobs}
    if len(kinds) != 1:
        traces = tuple(
            BaselineRoutingJobTrace(
                extractor_cell=ext,
                stub_cell=stub,
                transport_kind=tk,
                placement_id=pid,
                ok=False,
                path=None,
            )
            for ext, stub, tk, pid in _sort_jobs(list(jobs))
        )
        return BaselineRoutingResult(
            internal_transport_count=None,
            aggregation=OPTIMIZATION_COUNTERFACTUAL_AGGREGATION_SEQUENTIAL_TRUNK_V1,
            transport_kind=None,
            per_job=traces,
            failure_reason=COUNTERFACTUAL_FAIL_MIXED_TRANSPORT_KIND,
        )

    tk_inferred = next(iter(kinds))
    if transport_kind is not None and transport_kind != tk_inferred:
        return BaselineRoutingResult(
            internal_transport_count=None,
            aggregation=OPTIMIZATION_COUNTERFACTUAL_AGGREGATION_SEQUENTIAL_TRUNK_V1,
            transport_kind=tk_inferred,
            per_job=tuple(
                BaselineRoutingJobTrace(
                    extractor_cell=ext,
                    stub_cell=stub,
                    transport_kind=tk,
                    placement_id=pid,
                    ok=False,
                    path=None,
                )
                for ext, stub, tk, pid in _sort_jobs(list(jobs))
            ),
            failure_reason=COUNTERFACTUAL_FAIL_TRANSPORT_KIND_MISMATCH,
        )

    tk = tk_inferred
    want_r = want_role(tk)
    mineable, asteroid = mineable_and_asteroid_coords(final_mining_map)
    cells_sim = _strip_belt_pipe_cells(cells_orig)
    surface = surface_for_map(cells_sim)
    jobs_sorted = _sort_jobs(list(jobs))

    traces_out, fail = _sequential_trunk_paint_jobs(
        cells_sim,
        jobs_sorted=jobs_sorted,
        tk=tk,
        want_r=want_r,
        surface=surface,
        mineable=mineable,
        asteroid=asteroid,
        is_external=is_external,
    )
    if fail is not None:
        return BaselineRoutingResult(
            internal_transport_count=None,
            aggregation=OPTIMIZATION_COUNTERFACTUAL_AGGREGATION_SEQUENTIAL_TRUNK_V1,
            transport_kind=tk,
            per_job=tuple(traces_out),
            failure_reason=fail,
        )

    internal_n = count_internal_transport_tiles_for_kind(
        cells_sim,
        transport_kind=tk,
        is_external=is_external,
    )
    return BaselineRoutingResult(
        internal_transport_count=internal_n,
        aggregation=OPTIMIZATION_COUNTERFACTUAL_AGGREGATION_SEQUENTIAL_TRUNK_V1,
        transport_kind=tk,
        per_job=tuple(traces_out),
        failure_reason=None,
    )


__all__ = [
    "BaselineRoutingJobTrace",
    "BaselineRoutingResult",
    "COUNTERFACTUAL_FAIL_MIXED_TRANSPORT_KIND",
    "COUNTERFACTUAL_FAIL_NO_ROUTE",
    "COUNTERFACTUAL_FAIL_NO_ROUTING_JOBS",
    "COUNTERFACTUAL_FAIL_TRANSPORT_KIND_MISMATCH",
    "compute_shortest_feasible_transport_baseline",
]
