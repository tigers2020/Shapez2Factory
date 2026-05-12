"""STEP4 structured routing-failure diagnostics (``step4_route_failure_diagnostic``)."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass1_timeline_integration import (  # noqa: E501
    integrate_pass12_placement_into_working_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitState,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_merge_routing as step4_mod,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_merge_routing import (
    run_step4_merge_aware_routing,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_route_failure_diagnostic import (  # noqa: E501
    Step4RouteFailureReason,
    build_step4_route_failure_diagnostic,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    cells_dict_from_mining_map,
    external_predicate_for_mining_map,
)
from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline
from tests.unit.shapez_asteroid.test_step4_merge_routing import (
    _decoded_shape_miners_with_belt_escape,
)


def test_step4_route_failure_diagnostic_empty_goal_counts() -> None:
    """When ``goal_count`` is zero, exterior and trunk_seed counts are still emitted (ints)."""

    detail: dict[str, Any] = {
        "nearest_existing_transport_distance": None,
        "blocked_reason_near_stub": [],
        "last_error": "no_route",
    }
    d = build_step4_route_failure_diagnostic(
        rec=None,
        extractor_cell=(1, 1),
        stub_cell=(2, 2),
        transport_kind="shape_belt",
        want_role="belt",
        raw_goal=set(),
        goal_cells=frozenset(),
        trunk_cells=frozenset(),
        trunk_seed_candidates_by_kind={"shape_belt": set(), "fluid_pipe": set()},
        margin_cells=set(),
        committed_trunk_for_kind=set(),
        blocked=frozenset(),
        hard_extras=frozenset(),
        cells={(2, 2): {"x": 2, "y": 2, "role": "belt"}},
        mineable=frozenset(),
        asteroid=frozenset(),
        is_external=lambda c: False,
        cheap_reuse_cells=None,
        search_stats={"stop_reason": "exhausted", "search_mode": "goal_cells_union_legacy"},
        detail=detail,
        final_state=None,
    )
    assert d["goal_count"] == 0
    assert d["exterior_goal_count"] == 0
    assert d["trunk_seed_goal_count"] == 0
    assert d["failure_reason"] == Step4RouteFailureReason.empty_goal_set.value


def test_merge_routing_failure_includes_step4_route_failure_diagnostic() -> None:
    decoded = _decoded_shape_miners_with_belt_escape()
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    _p1, m2, stats = integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    pr = stats.get("placement_records") or {}
    if len(pr) < 2:
        pytest.skip("fixture placed fewer than two bundles")
    jobs = step4_mod._collect_routing_jobs(dict(cells_dict_from_mining_map(m2)))
    if len(jobs) < 2:
        pytest.skip("fewer than two routing jobs")
    fail_stub = jobs[-1][1]
    real = step4_mod._dijkstra_route

    def wrapped(stub_cell: Coord, *args: Any, **kwargs: Any) -> tuple[Coord, ...] | None:
        if stub_cell == fail_stub:
            return None
        return real(stub_cell, *args, **kwargs)

    with patch.object(step4_mod, "_dijkstra_route", new=wrapped):
        r = run_step4_merge_aware_routing(
            m2, final_mining_map=fm, is_external=is_ext, placement_records=pr
        )
    if not r.rolled_back_placement_ids:
        pytest.skip("target stub still trunk-connected; Dijkstra not invoked for failure path")

    fail = r.routing_failures[0]
    dig = fail.get("step4_route_failure_diagnostic")
    assert isinstance(dig, dict)
    assert dig["placement_id"] == fail.get("extractor_id")
    assert dig["stub_cell"] == fail.get("stub_cell")
    assert dig["transport_kind"] == fail.get("transport_kind")
    assert dig["last_error"]
    assert dig["search_mode"] == "goal_cells_union_legacy"
    assert isinstance(dig.get("search_time_ms"), float)
    assert dig["final_state"] == PlacementCommitState.ROLLED_BACK.value
    assert dig["failure_reason"] in {e.value for e in Step4RouteFailureReason}
    assert isinstance(dig.get("expanded_nodes"), int)
    assert isinstance(dig.get("search_exhausted"), bool)
    assert dig.get("route_length_ratio_limit") is not None
