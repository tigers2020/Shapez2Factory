"""Counterfactual sequential-trunk baseline routing (solver.baseline_routing)."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation import (
    constants as fc,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.baseline_routing import (
    COUNTERFACTUAL_FAIL_NO_ROUTE,
    COUNTERFACTUAL_FAIL_NO_ROUTING_JOBS,
    compute_shortest_feasible_transport_baseline,
)


def _inf(x: int, y: int) -> dict[str, Any]:
    return {
        "x": x,
        "y": y,
        "role": "inferred",
        "layout_kind": "asteroid_field",
        "surface": "shape",
    }


def _is_ext_x_gt(limit: int):
    def _pred(c: tuple[int, int]) -> bool:
        return c[0] > limit

    return _pred


def _north_south_extension_walls(rows: list[dict[str, Any]], x_lo: int, x_hi: int) -> None:
    """Strip-proof walls so Dijkstra cannot use cheap void rows at y=±1."""

    for x in range(x_lo, x_hi + 1):
        rows.append(
            {
                "x": x,
                "y": -1,
                "role": "occupied",
                "layout_kind": "extension",
                "surface": "shape",
            }
        )
        rows.append(
            {
                "x": x,
                "y": 1,
                "role": "occupied",
                "layout_kind": "extension",
                "surface": "shape",
            }
        )


def test_counterfactual_single_miner_shortest_path_count() -> None:
    """Strip stub belt; Dijkstra repaints shortest corridor to external (east)."""

    rows: list[dict[str, Any]] = [_inf(x, 0) for x in range(12, 27)]
    _north_south_extension_walls(rows, 8, 29)
    rows.append(
        {
            "x": 10,
            "y": 0,
            "role": "occupied",
            "layout_kind": "miner",
            "surface": "shape",
            "r": 0,
        }
    )
    rows.append({"x": 11, "y": 0, "role": "belt", "surface": "shape"})
    final_map = list(rows)
    res = compute_shortest_feasible_transport_baseline(
        mining_map=rows,
        routing_jobs=None,
        transport_kind=None,
        final_mining_map=final_map,
        is_external=_is_ext_x_gt(26),
    )
    assert res.failure_reason is None
    assert res.transport_kind == "shape_belt"
    assert res.aggregation == fc.OPTIMIZATION_COUNTERFACTUAL_AGGREGATION_SEQUENTIAL_TRUNK_V1
    assert len(res.per_job) == 1
    assert res.per_job[0].ok is True
    assert res.internal_transport_count == 15


def test_counterfactual_no_jobs() -> None:
    res = compute_shortest_feasible_transport_baseline(
        mining_map=[_inf(5, 0)],
        routing_jobs=None,
        transport_kind=None,
        final_mining_map=[_inf(5, 0)],
        is_external=_is_ext_x_gt(20),
    )
    assert res.internal_transport_count is None
    assert res.failure_reason == COUNTERFACTUAL_FAIL_NO_ROUTING_JOBS


def test_counterfactual_no_route_blocked_stub() -> None:
    """Extension east of stub plus north/south walls leave no feasible route."""

    rows: list[dict[str, Any]] = [_inf(x, 0) for x in range(13, 20)]
    _north_south_extension_walls(rows, 8, 22)
    rows.append(
        {
            "x": 10,
            "y": 0,
            "role": "occupied",
            "layout_kind": "miner",
            "surface": "shape",
            "r": 0,
        }
    )
    rows.append({"x": 11, "y": 0, "role": "belt", "surface": "shape"})
    rows.append(
        {
            "x": 12,
            "y": 0,
            "role": "occupied",
            "layout_kind": "extension",
            "surface": "shape",
        }
    )
    final_map = list(rows)
    res = compute_shortest_feasible_transport_baseline(
        mining_map=rows,
        routing_jobs=None,
        transport_kind=None,
        final_mining_map=final_map,
        is_external=_is_ext_x_gt(25),
    )
    assert res.internal_transport_count is None
    assert res.failure_reason == COUNTERFACTUAL_FAIL_NO_ROUTE
    assert len(res.per_job) == 1
    assert res.per_job[0].ok is False


def test_counterfactual_two_jobs_sequential_trunk() -> None:
    """Two miners eastbound; second stub may merge into first trunk (path length 1)."""

    rows = [_inf(x, 0) for x in range(12, 28)]
    rows.append(
        {
            "x": 10,
            "y": 0,
            "role": "occupied",
            "layout_kind": "miner",
            "surface": "shape",
            "r": 0,
            "placement_id": "p-a",
        }
    )
    rows.append({"x": 11, "y": 0, "role": "belt", "surface": "shape", "placement_id": "p-a"})
    rows.append(
        {
            "x": 18,
            "y": 0,
            "role": "occupied",
            "layout_kind": "miner",
            "surface": "shape",
            "r": 0,
            "placement_id": "p-b",
        }
    )
    rows.append({"x": 19, "y": 0, "role": "belt", "surface": "shape", "placement_id": "p-b"})
    final_map = list(rows)
    res = compute_shortest_feasible_transport_baseline(
        mining_map=rows,
        routing_jobs=None,
        transport_kind=None,
        final_mining_map=final_map,
        is_external=_is_ext_x_gt(27),
    )
    assert res.failure_reason is None
    assert len(res.per_job) == 2
    assert res.per_job[0].ok and res.per_job[1].ok
    assert res.per_job[0].path is not None and len(res.per_job[0].path) > 1
    assert res.per_job[1].path is not None and len(res.per_job[1].path) == 1
    assert isinstance(res.internal_transport_count, int)
    assert res.internal_transport_count < 25
