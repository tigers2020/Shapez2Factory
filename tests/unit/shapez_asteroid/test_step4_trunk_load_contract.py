"""STEP4 ``trunk_load`` nested schema + legacy alias contract (v3)."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    SOLVER_FRAME_STEP4_ROUTING,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass1_timeline_integration import (  # noqa: E501
    integrate_pass12_placement_into_working_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
    build_solver_timeline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_merge_routing import (
    run_step4_merge_aware_routing,
    step4_routing_skipped_result,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_trunk_load import (
    TRUNK_EDGE_LOAD_OBSERVATION_TOP_N,
    TRUNK_EDGE_LOAD_OBSERVATION_VERSION,
    TRUNK_EDGE_SHARED_THRESHOLD,
    TRUNK_LOAD_CONTRACT_VERSION,
    accumulate_trunk_edge_load,
    build_step4_trunk_load,
    build_step4_trunk_load_pipeline_exception_stub,
    build_trunk_edge_load_observation,
    canonical_trunk_edge_key,
    cells_on_high_sharing_trunk_edges,
    compact_trunk_load_overlay_for_replay,
    pass3_edge_congestion_weights_from_trunk_load,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    external_predicate_for_mining_map,
)
from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline
from tests.unit.shapez_asteroid.test_step4_merge_routing import (
    _decoded_shape_miners_with_belt_escape,
)


def _empty_trunk_edge_load_by_kind() -> dict[str, dict[str, int]]:
    return {"shape_belt": {}, "fluid_pipe": {}}


def _assert_transport_usage_dual_edge_maps(tul: dict) -> None:
    assert tul["trunk_edge_load"] == _empty_trunk_edge_load_by_kind()
    assert tul["trunk_edge_load_from_maximized_placements"] == _empty_trunk_edge_load_by_kind()


def _assert_empty_kind_observation_block(obs: dict) -> None:
    assert obs["observation_version"] == TRUNK_EDGE_LOAD_OBSERVATION_VERSION
    assert obs["top_n"] == TRUNK_EDGE_LOAD_OBSERVATION_TOP_N
    assert obs["shared_threshold"] == TRUNK_EDGE_SHARED_THRESHOLD
    for kind in ("shape_belt", "fluid_pipe"):
        bk = obs["by_kind"][kind]
        assert bk["traversal_count_total"] == 0
        assert bk["max_sharing"] == 0
        assert bk["shared_edge_count"] == 0
        assert bk["edge_count"] == 0
        assert bk["top_edges"] == []


def _assert_trunk_load_nested_matches_legacy(tl: dict) -> None:
    rm = tl["route_metrics"]
    tul = tl["transport_usage_load"]
    assert tl["edges"] == tul["existing_transport_cell_crossings"]
    assert rm["route_cell_visits"] == tl["step4_accumulated_route_cell_visits"]
    assert rm["unique_route_cell_count"] == tl["step4_final_route_cell_count"]
    by_kind = tl["trunk_load_by_kind"]
    assert sum(int(v["route_cell_visits"]) for v in by_kind.values()) == rm["route_cell_visits"]
    assert (
        sum(int(v["unique_route_cell_count"]) for v in by_kind.values())
        == rm["unique_route_cell_count"]
    )


def test_pipeline_exception_stub_distinguishes_from_pass12_skipped() -> None:
    tl = build_step4_trunk_load_pipeline_exception_stub()
    assert tl.get("skipped") is False
    assert tl.get("step4_result_state") == "pipeline_exception"
    assert tl["trunk_load_contract_version"] == TRUNK_LOAD_CONTRACT_VERSION
    _assert_transport_usage_dual_edge_maps(tl["transport_usage_load"])
    _assert_empty_kind_observation_block(tl["trunk_edge_load_observation"])


def test_p2c_metrics_cannot_overwrite_reserved_trunk_load_contract_keys() -> None:
    malicious = {
        "route_revalidation_passed": False,
        "route_metrics": {"route_cell_visits": 999, "unique_route_cell_count": 999},
        "trunk_load_by_kind": {},
        "transport_usage_load": {"existing_transport_cell_crossings": {}, "trunk_edge_load": {}},
        "edges": {"9,9": 1},
        "trunk_load_contract_version": 99,
        "mode": "wrong",
        "step4_accumulated_route_cell_visits": 999,
        "step4_final_route_cell_count": 999,
        "step4_committed_trunk_cell_count_by_kind": {"shape_belt": 999},
        "trunk_edge_load_observation": {"bogus": True},
    }
    tl = build_step4_trunk_load(
        trunk_edge_hits={},
        route_cell_visits=3,
        final_route_cells={(1, 1), (2, 2)},
        committed_trunk_by_kind={"shape_belt": {(1, 1)}},
        route_visits_by_kind={"shape_belt": 3},
        unique_cells_by_kind={"shape_belt": {(1, 1), (2, 2)}},
        p2c_metrics=malicious,
        trace={
            "step4_route_count": 0,
            "step4_route_commit_count": 0,
            "step4_routing_failure_count": 0,
            "initial_trunk_cells": 0,
            "placement_commit_counts": {},
            "unfinalized_placement_count": 0,
            "step4_routed_count": 0,
            "step4_routed_stub_count": 0,
            "step4_total_stub_count": 0,
            "step4_quarantined_count": 0,
            "step4_quarantined_unrouted_count": 0,
            "step4_rolled_back_count": 0,
            "step4_trunk_seed_candidate_count_by_kind": {},
            "step4_trunk_seed_candidate_count": 0,
            "step4_goal_set_size_peak": 0,
            "routes_by_placement_id": {},
        },
    )
    assert tl["trunk_load_contract_version"] == TRUNK_LOAD_CONTRACT_VERSION
    assert tl["mode"] == "accumulate_only"
    assert tl["route_metrics"]["route_cell_visits"] == 3
    assert tl["route_metrics"]["unique_route_cell_count"] == 2
    assert tl["route_revalidation_passed"] is False
    assert tl["edges"] == {}
    _assert_transport_usage_dual_edge_maps(tl["transport_usage_load"])
    obs = tl["trunk_edge_load_observation"]
    assert obs["observation_version"] == TRUNK_EDGE_LOAD_OBSERVATION_VERSION
    assert "bogus" not in obs
    _assert_empty_kind_observation_block(obs)


def test_trunk_edge_load_observation_top_edges_order_and_cap() -> None:
    """``top_edges[].edge`` matches ``trunk_edge_load`` undirected keys ``x,y--x,y`` (not ``->``).

    Sort: ``count`` desc, ``edge`` asc tie-break; at most ``top_n`` entries.
    """

    block = {
        "shape_belt": {
            "1,1--1,2": 3,
            "1,2--1,3": 2,
            "9,9--9,10": 2,
            "0,0--0,1": 1,
        },
        "fluid_pipe": {},
    }
    obs = build_trunk_edge_load_observation(block, kind_keys=("shape_belt", "fluid_pipe"))
    sb = obs["by_kind"]["shape_belt"]
    assert sb["traversal_count_total"] == 8
    assert sb["edge_count"] == 4
    assert sb["max_sharing"] == 3
    assert sb["shared_edge_count"] == 3
    assert [e["edge"] for e in sb["top_edges"]] == [
        "1,1--1,2",
        "1,2--1,3",
        "9,9--9,10",
        "0,0--0,1",
    ]
    assert len(sb["top_edges"]) <= TRUNK_EDGE_LOAD_OBSERVATION_TOP_N


def test_trunk_edge_load_observation_top_n_truncates_with_tie_breaker() -> None:
    edges = {f"{i},0--{i},1": 1 for i in range(TRUNK_EDGE_LOAD_OBSERVATION_TOP_N + 3)}
    obs = build_trunk_edge_load_observation(
        {"shape_belt": edges, "fluid_pipe": {}},
        kind_keys=("shape_belt", "fluid_pipe"),
    )
    te = obs["by_kind"]["shape_belt"]["top_edges"]
    assert len(te) == TRUNK_EDGE_LOAD_OBSERVATION_TOP_N
    keys_sorted = sorted(edges)
    assert [e["edge"] for e in te] == keys_sorted[:TRUNK_EDGE_LOAD_OBSERVATION_TOP_N]


def test_shared_edge_count_uses_shared_threshold_constant() -> None:
    block = {"shape_belt": {"1,1--1,2": 1, "2,2--2,3": 2}, "fluid_pipe": {}}
    obs = build_trunk_edge_load_observation(block, kind_keys=("shape_belt", "fluid_pipe"))
    assert obs["by_kind"]["shape_belt"]["shared_edge_count"] == 1
    assert obs["shared_threshold"] == TRUNK_EDGE_SHARED_THRESHOLD


def test_canonical_trunk_edge_key_is_symmetric_under_reverse() -> None:
    a, b = (1, 2), (1, 3)
    assert canonical_trunk_edge_key(a, b) == canonical_trunk_edge_key(b, a)
    assert canonical_trunk_edge_key(a, b) == "1,2--1,3"


def test_accumulate_trunk_edge_load_single_path() -> None:
    acc: dict[str, dict[str, int]] = {}
    accumulate_trunk_edge_load(acc, "shape_belt", [(1, 1), (1, 2), (1, 3)])
    assert acc["shape_belt"] == {"1,1--1,2": 1, "1,2--1,3": 1}


def test_accumulate_trunk_edge_load_shared_segment() -> None:
    acc: dict[str, dict[str, int]] = {}
    accumulate_trunk_edge_load(acc, "shape_belt", [(1, 1), (1, 2), (1, 3)])
    accumulate_trunk_edge_load(acc, "shape_belt", [(2, 1), (1, 2), (1, 3)])
    assert acc["shape_belt"]["1,2--1,3"] == 2


def test_accumulate_trunk_edge_load_reverse_paths_merge() -> None:
    acc: dict[str, dict[str, int]] = {}
    accumulate_trunk_edge_load(acc, "shape_belt", [(1, 2), (1, 3)])
    accumulate_trunk_edge_load(acc, "shape_belt", [(1, 3), (1, 2)])
    assert acc["shape_belt"] == {"1,2--1,3": 2}


def test_accumulate_trunk_edge_load_kind_isolation() -> None:
    acc: dict[str, dict[str, int]] = {}
    accumulate_trunk_edge_load(acc, "shape_belt", [(1, 2), (1, 3)])
    accumulate_trunk_edge_load(acc, "fluid_pipe", [(1, 2), (1, 3)])
    assert acc["shape_belt"] == {"1,2--1,3": 1}
    assert acc["fluid_pipe"] == {"1,2--1,3": 1}


def test_trunk_edge_visit_sum_relates_to_route_cell_visits() -> None:
    """sum(edge traversals) = sum(max(len(path)-1,0)) over accumulated paths."""

    acc: dict[str, dict[str, int]] = {}
    paths = (
        ("shape_belt", [(1, 1), (1, 2), (1, 3)]),
        ("shape_belt", [(1, 3), (1, 2)]),
        ("shape_belt", [(5, 5)]),
    )
    visits = 0
    edge_steps = 0
    for kind, path in paths:
        accumulate_trunk_edge_load(acc, kind, path)
        visits += len(path)
        edge_steps += max(len(path) - 1, 0)
    total_edges = sum(sum(d.values()) for d in acc.values())
    assert total_edges == edge_steps
    tl = build_step4_trunk_load(
        trunk_edge_hits={},
        route_cell_visits=visits,
        final_route_cells={(1, 1), (1, 2), (1, 3), (5, 5)},
        committed_trunk_by_kind={"shape_belt": {(1, 1), (1, 2), (1, 3), (5, 5)}},
        route_visits_by_kind={"shape_belt": visits},
        unique_cells_by_kind={"shape_belt": {(1, 1), (1, 2), (1, 3), (5, 5)}},
        p2c_metrics={},
        trace={"mode": "accumulate_only"},
        trunk_edge_load_by_kind=acc,
    )
    assert tl["route_metrics"]["route_cell_visits"] == visits
    tel = tl["transport_usage_load"]["trunk_edge_load"]
    assert sum(sum(d.values()) for d in tel.values()) == total_edges


def test_step4_trunk_load_skipped_has_contract_version_and_nested_blocks() -> None:
    r = step4_routing_skipped_result([])
    tl = r.trunk_load
    assert tl["trunk_load_contract_version"] == TRUNK_LOAD_CONTRACT_VERSION
    assert tl["skipped"] is True
    assert tl["route_metrics"]["route_cell_visits"] == 0
    assert tl["route_metrics"]["unique_route_cell_count"] == 0
    assert tl["transport_usage_load"]["existing_transport_cell_crossings"] == {}
    _assert_transport_usage_dual_edge_maps(tl["transport_usage_load"])
    _assert_empty_kind_observation_block(tl["trunk_edge_load_observation"])
    assert "shape_belt" in tl["trunk_load_by_kind"] and "fluid_pipe" in tl["trunk_load_by_kind"]
    assert tl.get("step4_result_state") != "pipeline_exception"
    _assert_trunk_load_nested_matches_legacy(tl)


def test_step4_trunk_load_keeps_legacy_edges_alias_for_one_release() -> None:
    decoded = _decoded_shape_miners_with_belt_escape()
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    _p1, m2, stats = integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    pr = stats.get("placement_records")
    r = run_step4_merge_aware_routing(
        m2,
        final_mining_map=fm,
        is_external=is_ext,
        placement_records=pr,
    )
    tl = r.trunk_load
    assert tl["trunk_load_contract_version"] == TRUNK_LOAD_CONTRACT_VERSION
    tul = tl["transport_usage_load"]
    tel = tul["trunk_edge_load"]
    tmax = tul["trunk_edge_load_from_maximized_placements"]
    assert set(tel) == {"shape_belt", "fluid_pipe"} == set(tmax)
    for kind in ("shape_belt", "fluid_pipe"):
        for ek, c in tmax[kind].items():
            assert int(c) <= int(tel[kind][ek])
    obs = tl["trunk_edge_load_observation"]
    assert obs["observation_version"] == TRUNK_EDGE_LOAD_OBSERVATION_VERSION
    for kind in ("shape_belt", "fluid_pipe"):
        assert sum(tel[kind].values()) == obs["by_kind"][kind]["traversal_count_total"]
        assert len(obs["by_kind"][kind]["top_edges"]) <= TRUNK_EDGE_LOAD_OBSERVATION_TOP_N
    _assert_trunk_load_nested_matches_legacy(tl)


def test_solver_timeline_step4_frame_summary_includes_full_trunk_load() -> None:
    out = build_solver_timeline(_decoded_shape_miners_with_belt_escape())
    step4_f = next(f for f in out["solver_timeline"] if f["id"] == SOLVER_FRAME_STEP4_ROUTING)
    assert "trunk_load" in step4_f["summary"]
    tl_frame = step4_f["summary"]["trunk_load"]
    tl_ss = out["solver_summary"]["trunk_load"]
    assert tl_frame == tl_ss
    _assert_trunk_load_nested_matches_legacy(tl_frame)


def test_pass3_edge_congestion_weights_from_trunk_load() -> None:
    tl = {
        "transport_usage_load": {
            "trunk_edge_load": {"shape_belt": {"1,0--2,0": 3, "2,0--3,0": 1}},
        },
    }
    w = pass3_edge_congestion_weights_from_trunk_load(tl, transport_kind="shape_belt")
    assert w == {"1,0--2,0": 30, "2,0--3,0": 10}
    assert pass3_edge_congestion_weights_from_trunk_load(None, transport_kind="shape_belt") is None


def test_pass3_edge_congestion_weights_squares_maximized_contribution() -> None:
    """``v_eff = (v_all - v_max) + v_max**2`` on edges touched by maximized-only routes."""

    tl = {
        "transport_usage_load": {
            "trunk_edge_load": {"shape_belt": {"1,0--2,0": 3}},
            "trunk_edge_load_from_maximized_placements": {"shape_belt": {"1,0--2,0": 2}},
        },
    }
    w = pass3_edge_congestion_weights_from_trunk_load(tl, transport_kind="shape_belt")
    assert w == {"1,0--2,0": 50}


def test_compact_trunk_load_overlay_for_replay_minimal() -> None:
    tl = {
        "trunk_edge_load_observation": {
            "observation_version": 1,
            "top_n": 10,
            "shared_threshold": 2,
            "by_kind": {
                "shape_belt": {
                    "traversal_count_total": 2,
                    "max_sharing": 2,
                    "shared_edge_count": 1,
                    "top_edges": [{"edge": "1,0--2,0", "count": 2}],
                }
            },
        },
    }
    ov = compact_trunk_load_overlay_for_replay(tl)
    assert ov is not None
    assert ov["overlay_version"] == 1
    assert ov["by_kind"]["shape_belt"]["top_edges"][0]["edge"] == "1,0--2,0"


def test_cells_on_high_sharing_trunk_edges() -> None:
    tl = {
        "transport_usage_load": {
            "trunk_edge_load": {"shape_belt": {"1,0--2,0": 2, "3,0--4,0": 1}},
        },
    }
    cells = cells_on_high_sharing_trunk_edges(tl, transport_kind="shape_belt")
    assert (1, 0) in cells and (2, 0) in cells
    assert (3, 0) not in cells
