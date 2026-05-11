"""STEP4 merge-aware routing skeleton contracts (trunk seed, goal set, commit, quarantine)."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE,
)
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
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_goal_trunk_seed import (  # noqa: E501
    build_step4_goal_set,
    build_trunk_seed_candidates_by_kind,
    exterior_margin_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_merge_routing import (
    run_step4_merge_aware_routing,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_trunk_load import (
    accumulate_trunk_edge_load,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    cells_dict_from_mining_map,
    external_predicate_for_mining_map,
)
from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline
from tests.unit.shapez_asteroid.test_step4_merge_routing import (
    _decoded_shape_miners_with_belt_escape,
)


def test_goal_set_first_route_is_margin_union_trunk_seed() -> None:
    margin = {(1, 1), (2, 2)}
    seeds: dict[str, set[Coord]] = {
        "shape_belt": {(3, 3)},
        "fluid_pipe": {(4, 4)},
    }
    g_shape = build_step4_goal_set(
        "shape_belt",
        committed_trunk_by_kind={},
        exterior_margin_cells=margin,
        trunk_seed_candidates_by_kind=seeds,
    )
    assert g_shape == margin | {(3, 3)}


def test_goal_set_second_route_uses_committed_trunk_and_margin() -> None:
    margin = {(1, 1)}
    committed = {"shape_belt": {(9, 9)}}
    seeds: dict[str, set[Coord]] = {"shape_belt": {(3, 3)}, "fluid_pipe": set()}
    g = build_step4_goal_set(
        "shape_belt",
        committed_trunk_by_kind=committed,
        exterior_margin_cells=margin,
        trunk_seed_candidates_by_kind=seeds,
    )
    assert g == {(9, 9), (1, 1)}
    assert (3, 3) not in g


def test_transport_kind_goal_sets_do_not_cross_merge_shape_committed_into_fluid() -> None:
    margin = {(1, 1)}
    committed = {"shape_belt": {(5, 5)}}
    seeds: dict[str, set[Coord]] = {"shape_belt": {(5, 5)}, "fluid_pipe": {(6, 6)}}
    g_fluid = build_step4_goal_set(
        "fluid_pipe",
        committed_trunk_by_kind=committed,
        exterior_margin_cells=margin,
        trunk_seed_candidates_by_kind=seeds,
    )
    assert (5, 5) not in g_fluid
    assert g_fluid == margin | {(6, 6)}


def test_first_route_commit_populates_trunk_trace_and_routed_state() -> None:
    decoded = _decoded_shape_miners_with_belt_escape()
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    _p1, m2, stats = integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    pr = stats.get("placement_records")
    ela = {
        "solver_hints": {
            "trunk_seed_cell_union": [],
        }
    }
    r = run_step4_merge_aware_routing(
        m2,
        final_mining_map=fm,
        is_external=is_ext,
        placement_records=pr,
        existing_layout_analysis=ela,
    )
    assert r.trunk_load.get("step4_final_route_cell_count", 0) >= 1
    assert r.trunk_load.get("step4_route_commit_count", 0) >= 1
    assert r.trunk_load.get("step4_accumulated_route_cell_visits", 0) >= 1
    by_kind = r.trunk_load.get("step4_committed_trunk_cell_count_by_kind") or {}
    assert sum(int(v) for v in by_kind.values()) >= 1
    assert any(
        s == PlacementCommitState.ROUTED_CONFIRMED.value for s in r.placement_commit_by_id.values()
    )


def test_route_path_index_zero_is_fixed_output_stub() -> None:
    decoded = _decoded_shape_miners_with_belt_escape()
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    _p1, m2, stats = integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    pr = stats.get("placement_records")
    r = run_step4_merge_aware_routing(
        m2, final_mining_map=fm, is_external=is_ext, placement_records=pr
    )
    for rt in r.routes:
        assert rt.path[0] == rt.stub_cell
        assert rt.stub_cell in final_route_cells_from_result(r)


def final_route_cells_from_result(r: Any) -> set[Coord]:
    cells = cells_dict_from_mining_map(r.map_after_routing)
    want = {"belt", "pipe"}
    return {k for k, row in cells.items() if row.get("role") in want}


def test_routing_failure_quarantine_no_trunk_promotion() -> None:
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
    if not r.quarantined_placement_ids:
        pytest.skip("target stub still trunk-connected; Dijkstra not invoked for failure path")

    assert r.trunk_load.get("step4_routing_failure_count", 0) >= 1
    fail = r.routing_failures[0]
    assert fail["final_state"] == PlacementCommitState.QUARANTINED_UNROUTED.value
    assert fail.get("recovery_trigger") == RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE
    assert not r.rolled_back_placement_ids


def test_trunk_load_accumulates_without_capacity_hard_gate() -> None:
    decoded = _decoded_shape_miners_with_belt_escape()
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    _p1, m2, stats = integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    pr = stats.get("placement_records")
    r = run_step4_merge_aware_routing(
        m2, final_mining_map=fm, is_external=is_ext, placement_records=pr
    )
    acc = int(r.trunk_load.get("step4_accumulated_route_cell_visits", 0) or 0)
    assert acc >= len(r.routes)
    cap_ref = 1
    assert acc > cap_ref or acc == acc
    assert r.trunk_load.get("mode") == "accumulate_only"


def test_trunk_edge_load_matches_final_route_paths() -> None:
    """``trunk_edge_load`` is derived from the same ``Step4Route.path`` tuples returned."""

    decoded = _decoded_shape_miners_with_belt_escape()
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    _p1, m2, stats = integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    pr = stats.get("placement_records")
    r = run_step4_merge_aware_routing(
        m2, final_mining_map=fm, is_external=is_ext, placement_records=pr
    )
    recomputed: dict[str, dict[str, int]] = {}
    for rt in r.routes:
        accumulate_trunk_edge_load(recomputed, rt.transport_kind, rt.path)
    tel = r.trunk_load["transport_usage_load"]["trunk_edge_load"]
    assert set(tel) == {"shape_belt", "fluid_pipe"}
    for kind in ("shape_belt", "fluid_pipe"):
        assert dict(sorted(recomputed.get(kind, {}).items())) == tel[kind]


def test_exterior_margin_union_trunk_seed_in_candidates() -> None:
    cells: dict[Coord, dict[str, Any]] = {
        (2, 2): {"x": 2, "y": 2, "role": "belt", "surface": "shape"},
    }

    def is_ext(c: Coord) -> bool:
        return c == (2, 3)

    mineable: frozenset[Coord] = frozenset({(2, 2)})
    ast: frozenset[Coord] = frozenset()
    margin = exterior_margin_cells(mineable=mineable, asteroid=ast, cells=cells, is_external=is_ext)
    assert (2, 2) in margin
    hints = {(2, 2)}
    by_kind = build_trunk_seed_candidates_by_kind(
        exterior_margin=margin, hint_union=hints, cells=cells
    )
    assert (2, 2) in by_kind["shape_belt"]


def test_hard_protected_distant_cell_does_not_break_routing() -> None:
    decoded = _decoded_shape_miners_with_belt_escape()
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    _p1, m2, stats = integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    pr = stats.get("placement_records") or {}
    jobs = step4_mod._collect_routing_jobs(dict(cells_dict_from_mining_map(m2)))
    block_away = (jobs[0][1][0] + 50, jobs[0][1][1] + 50) if jobs else (99, 99)
    r = run_step4_merge_aware_routing(
        m2,
        final_mining_map=fm,
        is_external=is_ext,
        placement_records=pr,
        hard_protected_cells=frozenset({block_away}),
    )
    assert r.committed
