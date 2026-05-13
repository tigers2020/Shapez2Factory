"""STEP4 unreachable-component trap classification + failure row namespaces."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from unittest.mock import patch

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitRecord,
    PlacementCommitState,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_merge_routing as s4mr,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_dijkstra import (
    DIJKSTRA_REACHABLE_GOAL_COUNT_KEY,
    DIJKSTRA_REACHABLE_MARGIN_GOAL_COUNT_KEY,
    DIJKSTRA_REACHABLE_TRUNK_GOAL_COUNT_KEY,
)


def _trapped_east_stub_fixture() -> tuple[list[dict], list[dict], Callable[[Coord], bool]]:
    """Same geometry as test_step4_failed_pass2_route_recovery (single pass2 provisional)."""

    surface = "shape"
    rows: list[dict] = []

    def is_external(c: Coord) -> bool:
        return c == (8, 9)

    for x in range(8, 19):
        rows.append(
            {
                "x": x,
                "y": 10,
                "role": "inferred",
                "layout_kind": "asteroid_field",
                "surface": surface,
            }
        )

    rows.append(
        {
            "x": 15,
            "y": 10,
            "role": "occupied",
            "layout_kind": "miner",
            "surface": surface,
            "r": 0,
            "placement_id": "p2-000001",
        }
    )
    for belt_x in (16, 14):
        rows.append(
            {
                "x": belt_x,
                "y": 10,
                "role": "belt",
                "surface": surface,
                "placement_id": "p2-000001",
            }
        )
    for bx, by in ((17, 10), (16, 9), (16, 11)):
        rows.append({"x": bx, "y": by, "role": "pipe", "surface": "fluid"})

    final_rows = [dict(r) for r in rows]
    return rows, final_rows, is_external


def _fake_dijkstra_trap(
    *_args: Any,
    search_stats: dict[str, Any] | None = None,
    **_kwargs: Any,
) -> tuple[Coord, ...] | None:
    if search_stats is not None:
        search_stats["expanded_nodes"] = 10
        search_stats["heap_pops"] = 12
        search_stats["stop_reason"] = "exhausted"
        search_stats["frontier_stop_reason"] = "exhausted"
        search_stats[DIJKSTRA_REACHABLE_GOAL_COUNT_KEY] = 0
        search_stats[DIJKSTRA_REACHABLE_TRUNK_GOAL_COUNT_KEY] = 0
        search_stats[DIJKSTRA_REACHABLE_MARGIN_GOAL_COUNT_KEY] = 0
    return None


def test_step4_isolated_component_trap_records_zero_reachable_goals() -> None:
    """expanded_nodes>0 with zero Dijkstra goal hits → step4_unreachable_component + rollback."""

    rows, final_rows, is_external = _trapped_east_stub_fixture()
    pr: dict[str, PlacementCommitRecord] = {
        "p2-000001": PlacementCommitRecord(
            placement_id="p2-000001",
            placement_pass="pass2",
            extractor_cell=(15, 10),
            extension_cells=(),
            stub_cell=(16, 10),
            transport_kind="shape_belt",
            state=PlacementCommitState.PROVISIONAL_PLACED,
        )
    }
    with patch.object(s4mr, "_dijkstra_route", side_effect=_fake_dijkstra_trap):
        r = s4mr.run_step4_merge_aware_routing(
            rows,
            final_mining_map=final_rows,
            is_external=is_external,
            placement_records=pr,
            step4_reentry_index=3,
        )
    assert r.complete_routing_success is False
    assert r.rolled_back_placement_ids
    reasons = {f.get("reason") for f in r.routing_failures}
    assert "step4_unreachable_component" in reasons
    det = next(
        f["step4_route_failure_detail"]
        for f in r.routing_failures
        if f.get("reason") == "step4_unreachable_component"
    )
    assert int(det.get("expanded_nodes") or 0) > 0
    assert int(det.get("dijkstra_reachable_goal_count") or 0) == 0
    assert det.get("last_error") == "step4_unreachable_component"
    assert det.get("step4_reentry_index") == 3
    assert (det.get("routing_failure_detail") or {}).get("step4_reentry_index") == 3
    assert r.trunk_load.get("step4_reentry_index") == 3


def test_recovery_reason_namespaces_do_not_cross() -> None:
    """Failed routing rows use reject/rollback fields; no successful commit_reason."""

    rows, final_rows, is_external = _trapped_east_stub_fixture()
    pr: dict[str, PlacementCommitRecord] = {
        "p2-000001": PlacementCommitRecord(
            placement_id="p2-000001",
            placement_pass="pass2",
            extractor_cell=(15, 10),
            extension_cells=(),
            stub_cell=(16, 10),
            transport_kind="shape_belt",
            state=PlacementCommitState.PROVISIONAL_PLACED,
        )
    }
    with patch.object(s4mr, "_dijkstra_route", side_effect=_fake_dijkstra_trap):
        r = s4mr.run_step4_merge_aware_routing(
            rows,
            final_mining_map=final_rows,
            is_external=is_external,
            placement_records=pr,
        )
    for fd in r.routing_failures:
        assert "commit_reason" not in fd
        if fd.get("reason") == "step4_unreachable_component":
            assert fd.get("rejected_reason") == "step4_unreachable_component"
            assert fd.get("rollback_reason") == "step4_unreachable_component"
