"""STEP4 merge-aware routing: belt/pipe materialization and validation gate."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from unittest.mock import patch

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass1_timeline_integration as p1_tl_mod,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass1_timeline_integration import (  # noqa: E501
    integrate_pass12_placement_into_working_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitRecord,
    PlacementCommitState,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import (
    solver_mutation_transaction as mut_txn,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
    build_solver_timeline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_merge_routing as step4_mod,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_merge_routing import (
    run_step4_merge_aware_routing,
    step4_routing_skipped_result,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    cells_dict_from_mining_map,
    external_predicate_for_mining_map,
    validate_final_mining_layout,
)
from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline


def _mining_map_cascade_neighbor_rollback_fixture() -> list[dict[str, Any]]:
    """Two miners: A routes first on y=10; eastbound spine must use B's stub (15,10).

    B core at (15,11) outputs north to stub (15,10). All cells off y=10 (except miners) are
    fluid pipes so belt cannot detour vertically.
    """

    surface = "shape"
    rows: list[dict[str, Any]] = []
    cores = {(10, 10), (15, 11)}
    stubs = {(11, 10), (15, 10)}
    for x in range(8, 42):
        for y in range(7, 14):
            if y == 10:
                continue
            if (x, y) in cores:
                continue
            rows.append({"x": x, "y": y, "role": "pipe", "surface": "fluid"})
    for x in range(8, 42):
        if (x, 10) in cores or (x, 10) in stubs:
            continue
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
            "x": 10,
            "y": 10,
            "role": "occupied",
            "layout_kind": "miner",
            "surface": surface,
            "r": 0,
            "placement_id": "p1-000001",
        }
    )
    rows.append(
        {
            "x": 11,
            "y": 10,
            "role": "belt",
            "surface": surface,
            "placement_id": "p1-000001",
        }
    )
    rows.append(
        {
            "x": 15,
            "y": 11,
            "role": "occupied",
            "layout_kind": "miner",
            "surface": surface,
            "r": 3,
            "placement_id": "p1-000002",
        }
    )
    rows.append(
        {
            "x": 15,
            "y": 10,
            "role": "belt",
            "surface": surface,
            "placement_id": "p1-000002",
        }
    )
    for x in range(18, 38):
        rows.append({"x": x, "y": 10, "role": "belt", "surface": surface})
    return rows


def _placement_records_cascade_fixture() -> dict[str, PlacementCommitRecord]:
    return {
        "p1-000001": PlacementCommitRecord(
            placement_id="p1-000001",
            placement_pass="pass1",
            extractor_cell=(10, 10),
            extension_cells=(),
            stub_cell=(11, 10),
            transport_kind="shape_belt",
            state=PlacementCommitState.PROVISIONAL_PLACED,
        ),
        "p1-000002": PlacementCommitRecord(
            placement_id="p1-000002",
            placement_pass="pass1",
            extractor_cell=(15, 11),
            extension_cells=(),
            stub_cell=(15, 10),
            transport_kind="shape_belt",
            state=PlacementCommitState.PROVISIONAL_PLACED,
        ),
    }


def _decoded_shape_miners_with_belt_escape() -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for x in range(10, 13):
        entries.append({"X": x, "Y": 0, "T": "Layout_ShapeMiner"})
    for x in range(13, 30):
        entries.append({"X": x, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0})
    return {"BP": {"Entries": entries}}


def _decoded_fluid_miners_with_pipe_escape() -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for x in range(10, 13):
        entries.append({"X": x, "Y": 0, "T": "Layout_FluidMiner"})
    for x in range(13, 30):
        entries.append({"X": x, "Y": 0, "T": "Layout_FluidPipe", "R": 0})
    return {"BP": {"Entries": entries}}


def _blocked_extractors_extensions(mining_map: list[dict[str, Any]]) -> set[tuple[int, int]]:
    out: set[tuple[int, int]] = set()
    for row in mining_map:
        lk = row.get("layout_kind")
        if lk in ("miner", "fluid_miner", "extractor", "extension", "fluid_extension"):
            x, y = row["x"], row["y"]
            out.add((int(x), int(y)))
    return out


def _coords_from_routing_pair_lists(rs: dict[str, Any]) -> set[Coord]:
    out: set[Coord] = set()
    for key in ("hard_protected_corridors", "soft_protected_corridors"):
        raw = rs.get(key)
        if not isinstance(raw, list):
            continue
        for it in raw:
            if isinstance(it, (list, tuple)) and len(it) == 2:
                x, y = it[0], it[1]
                if isinstance(x, int) and isinstance(y, int):
                    out.add((x, y))
    nested = rs.get("protected_corridors")
    if isinstance(nested, dict):
        for sub in ("hard", "soft"):
            raw2 = nested.get(sub)
            if not isinstance(raw2, list):
                continue
            for it in raw2:
                if isinstance(it, (list, tuple)) and len(it) == 2:
                    x, y = it[0], it[1]
                    if isinstance(x, int) and isinstance(y, int):
                        out.add((x, y))
    return out


def test_step4_routing_state_protected_pool_covers_every_committed_path_cell() -> None:
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
    assert r.routing_state is not None
    pool = _coords_from_routing_pair_lists(r.routing_state)
    for rt in r.routes:
        for c in rt.path:
            assert c in pool, f"path cell {c} missing from hard/soft pool"


def test_step4_shape_map_routes_belts_and_passes_final_validation() -> None:
    decoded = _decoded_shape_miners_with_belt_escape()
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    _p1, m2, stats = integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    assert stats["pass12_skipped"] is False
    assert stats["pass12_mixed_surface_skipped"] is False
    pr = stats.get("placement_records")
    r = run_step4_merge_aware_routing(
        m2, final_mining_map=fm, is_external=is_ext, placement_records=pr
    )
    assert r.committed
    assert r.routing_state is not None
    assert r.trunk_load.get("step4_route_count", 0) >= 1
    assert r.rolled_back_placement_ids == ()
    if pr:
        assert all(
            s == PlacementCommitState.ROUTED_CONFIRMED.value
            for s in r.placement_commit_by_id.values()
        )
    rep = validate_final_mining_layout(r.map_after_routing)
    assert rep.connectivity_valid
    assert rep.disconnected_stub_count == 0
    assert rep.orphan_transport_count == 0
    assert rep.overlap_violation_count == 0
    if pr:
        assert any(
            row.get("placement_commit_state") == PlacementCommitState.ROUTED_CONFIRMED.value
            for row in r.map_after_routing
            if row.get("placement_id")
        )


def test_step4_merged_stub_route_includes_trunk_spine_in_protected_pool() -> None:
    """Stub-in-trunk shortcut uses a length-1 ``path``; pool must still cover the belt spine."""

    surface = "shape"
    final_mining_map: list[dict[str, Any]] = []
    for x in range(9, 35):
        for y in range(4, 8):
            final_mining_map.append(
                {
                    "x": x,
                    "y": y,
                    "role": "inferred",
                    "layout_kind": "asteroid_field",
                    "surface": surface,
                }
            )
    map_after_pass2: list[dict[str, Any]] = []
    for x in range(11, 30):
        map_after_pass2.append(
            {
                "x": x,
                "y": 5,
                "role": "belt",
                "surface": surface,
                "placement_id": "p-merge",
            }
        )
    map_after_pass2.append(
        {
            "x": 10,
            "y": 5,
            "role": "occupied",
            "layout_kind": "miner",
            "surface": surface,
            "r": 0,
            "placement_id": "p-merge",
        }
    )

    def is_ext(c: Coord) -> bool:
        return c[0] >= 30

    r = run_step4_merge_aware_routing(
        map_after_pass2,
        final_mining_map=final_mining_map,
        is_external=is_ext,
        placement_records=None,
    )
    assert r.routing_state is not None
    pool = _coords_from_routing_pair_lists(r.routing_state)
    assert (20, 5) in pool
    assert any(len(rt.path) == 1 and rt.merged_to_existing for rt in r.routes)


def test_step4_committed_routes_populate_soft_protected_corridor_pool() -> None:
    decoded = _decoded_shape_miners_with_belt_escape()
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    _p1, m2, stats = integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    r = run_step4_merge_aware_routing(
        m2,
        final_mining_map=fm,
        is_external=is_ext,
        placement_records=stats.get("placement_records"),
    )

    assert r.committed
    assert r.routing_state is not None
    route_cells = {cell for route in r.routes for cell in route.path}
    hard_cells = {tuple(cell) for cell in r.routing_state["protected_corridors"]["hard"]}
    soft_cells = {tuple(cell) for cell in r.routing_state["protected_corridors"]["soft"]}
    assert soft_cells
    pool_cells = soft_cells | hard_cells
    assert route_cells.issubset(pool_cells)
    assert soft_cells.isdisjoint(hard_cells)
    assert (
        r.routing_state["soft_protected_candidate_corridors"]
        == r.routing_state["soft_protected_confirmed_corridors"]
    )


def test_step4_output_stub_cells_populate_hard_protected_corridor_pool() -> None:
    decoded = _decoded_shape_miners_with_belt_escape()
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    _p1, m2, stats = integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    r = run_step4_merge_aware_routing(
        m2,
        final_mining_map=fm,
        is_external=is_ext,
        placement_records=stats.get("placement_records"),
    )

    assert r.routing_state is not None
    hard_cells = {tuple(cell) for cell in r.routing_state["protected_corridors"]["hard"]}
    stub_cells = {route.stub_cell for route in r.routes}
    external_trunk_entry_cells = {route.path[-1] for route in r.routes if route.path}
    assert stub_cells
    assert stub_cells.issubset(hard_cells)
    assert external_trunk_entry_cells.issubset(hard_cells)


def test_step4_fluid_map_routes_pipes() -> None:
    decoded = _decoded_fluid_miners_with_pipe_escape()
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    _p1, m2, stats = integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    assert stats["pass12_skipped"] is False
    pr = stats.get("placement_records")
    r = run_step4_merge_aware_routing(
        m2, final_mining_map=fm, is_external=is_ext, placement_records=pr
    )
    assert r.committed
    assert all(rt.transport_kind == "fluid_pipe" for rt in r.routes)
    pipes = [row for row in r.map_after_routing if row.get("role") == "pipe"]
    assert pipes, "expected pipe cells after STEP4"
    rep = validate_final_mining_layout(r.map_after_routing)
    assert rep.connectivity_valid


def test_step4_skipped_result_contract() -> None:
    m = [{"x": 1, "y": 0, "role": "belt", "surface": "shape"}]
    r = step4_routing_skipped_result(m)
    assert r.map_after_routing == m
    assert r.trunk_load.get("skipped") is True
    assert r.trunk_load.get("step4_route_count") == 0
    assert r.trunk_load.get("unfinalized_placement_count") == 0
    assert r.trunk_load.get("route_revalidation_passed") is True
    assert r.trunk_load.get("broken_routed_route_count") == 0
    assert r.trunk_load.get("cascade_rollback_count") == 0


def test_p2c_corrective_reroute_increments_when_stub_check_flaky_then_ok() -> None:
    decoded = _decoded_shape_miners_with_belt_escape()
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    _p1, m2, stats = integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    assert not stats["pass12_skipped"]
    pr = stats.get("placement_records")
    real_stub = step4_mod._stub_reaches_external_trunk
    calls = {"n": 0}

    def flaky_once(
        stub_cell: Coord,
        *,
        cells: dict[Coord, dict[str, Any]],
        want_role: str,
        is_external: Callable[[Coord], bool],
    ) -> bool:
        calls["n"] += 1
        if calls["n"] == 1:
            return False
        return real_stub(stub_cell, cells=cells, want_role=want_role, is_external=is_external)

    with patch.object(step4_mod, "_stub_reaches_external_trunk", flaky_once):
        r = run_step4_merge_aware_routing(
            m2, final_mining_map=fm, is_external=is_ext, placement_records=pr
        )

    assert r.trunk_load.get("route_revalidation_passed") is True
    assert r.trunk_load.get("cascade_reroute_count", 0) >= 1
    assert r.trunk_load.get("broken_routed_route_count", 0) >= 1
    detail = r.trunk_load.get("cascade_route_replay_detail")
    assert isinstance(detail, list) and len(detail) >= 1
    row0 = detail[0]
    assert row0.get("reason") == "p2c_cascade_reroute"
    assert row0.get("old_route_id")
    assert row0.get("new_route_id")
    assert row0.get("replacement_search_mode") == "p2c_dijkstra_trunk"
    assert row0.get("replacement_connectivity_preserved") is True
    assert row0.get("replacement_path_cell_delta") == row0.get("new_path_cell_count", 0) - row0.get(
        "old_path_cell_count", 0
    )
    assert row0.get("replacement_cost_delta") is None
    rm = row0.get("cells_removed")
    ad = row0.get("cells_added")
    kf = row0.get("cells_kept")
    assert isinstance(rm, list) and isinstance(ad, list) and isinstance(kf, list)
    assert all(isinstance(p, list) and len(p) == 2 for p in rm + ad + kf)
    assert len(rm) + len(kf) == row0["old_path_cell_count"]
    assert len(ad) + len(kf) == row0["new_path_cell_count"]
    assert row0.get("transport_kind") == "shape_belt"
    assert row0.get("replacement_reason") == "p2c_cascade_reroute"


def test_step4_cascade_revalidates_route_after_neighbor_rollback() -> None:
    """P2-C.1: B rolls back and removes its stub that A's winning path depended on; P2-C repairs A.

    ``force_route_attempt_placement_ids`` prevents the stub-in-trunk merge shortcut for B; otherwise
    B would skip ``_dijkstra_route`` after A laid belts through B's stub so we could not simulate
    routing failure at B's stub with a patch.
    """

    m = _mining_map_cascade_neighbor_rollback_fixture()
    pr = _placement_records_cascade_fixture()
    is_ext = external_predicate_for_mining_map(m)
    real_dij = step4_mod._dijkstra_route

    def fail_only_b_stub(stub_cell: Coord, *args: Any, **kwargs: Any) -> tuple[Coord, ...] | None:
        if stub_cell == (15, 10):
            return None
        return real_dij(stub_cell, *args, **kwargs)

    with patch.object(step4_mod, "_dijkstra_route", new=fail_only_b_stub):
        r = run_step4_merge_aware_routing(
            m,
            final_mining_map=m,
            is_external=is_ext,
            placement_records=pr,
            force_route_attempt_placement_ids=frozenset({"p1-000002"}),
        )

    tl = r.trunk_load
    assert tl.get("route_revalidation_passed") is True
    assert int(tl.get("broken_routed_route_count", 0)) >= 1
    assert int(tl.get("cascade_corrective_attempts", 0)) >= 1
    rer = int(tl.get("cascade_reroute_count", 0))
    crb = int(tl.get("cascade_rollback_count", 0))
    assert rer == 1 or crb == 1
    assert int(tl.get("unfinalized_placement_count", 0)) == 0
    assert r.placement_commit_by_id.get("p1-000001") == PlacementCommitState.ROUTED_CONFIRMED.value
    assert r.placement_commit_by_id.get("p1-000002") == PlacementCommitState.ROLLED_BACK.value
    assert "p1-000002" in r.rolled_back_placement_ids
    assert not r.quarantined_placement_ids
    assert not r.committed

    rep = validate_final_mining_layout(r.map_after_routing)
    assert rep.geometry_valid
    assert rep.connectivity_valid


def test_step4_paths_avoid_extractor_and_extension_cells() -> None:
    decoded = _decoded_shape_miners_with_belt_escape()
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    _p1, m2, stats = integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    assert not stats["pass12_skipped"]
    blocked = _blocked_extractors_extensions(m2)
    pr = stats.get("placement_records")
    r = run_step4_merge_aware_routing(
        m2, final_mining_map=fm, is_external=is_ext, placement_records=pr
    )
    assert r.committed
    for rt in r.routes:
        for c in rt.path:
            assert c not in blocked


def test_step4_second_stub_route_failure_quarantines_that_bundle() -> None:
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

    assert not r.committed
    pid = r.rolled_back_placement_ids[0]
    assert r.placement_commit_by_id[pid] == PlacementCommitState.ROLLED_BACK.value
    assert not r.quarantined_placement_ids
    assert any(
        s == PlacementCommitState.ROUTED_CONFIRMED.value for s in r.placement_commit_by_id.values()
    )

    fail = r.routing_failures[0]
    assert fail["extractor_id"] == pid
    assert fail["attempt_count"] == 1
    assert fail["final_state"] == PlacementCommitState.ROLLED_BACK.value
    assert fail["last_error"] == "no_route"
    assert fail.get("recovery_trigger") == "step4_routing_failure"
    assert not any(row.get("placement_id") == pid for row in r.map_after_routing)

    pcounts = r.trunk_load.get("placement_commit_counts") or {}
    assert pcounts.get(PlacementCommitState.ROUTED_CONFIRMED.value, 0) >= 1
    assert pcounts.get(PlacementCommitState.ROLLED_BACK.value, 0) >= 1
    assert pcounts.get(PlacementCommitState.QUARANTINED_UNROUTED.value, 0) == 0


def test_final_validation_rejects_quarantined_placement_commit_state() -> None:
    mining_map = [
        {
            "x": 10,
            "y": 10,
            "role": "belt",
            "surface": "shape",
            "placement_commit_state": "quarantined_unrouted",
        },
    ]
    rep = validate_final_mining_layout(mining_map)
    assert rep.quarantined_unrouted_count == 1
    assert not rep.geometry_valid


def test_final_validation_rejects_provisional_placed_row() -> None:
    mining_map = [
        {
            "x": 10,
            "y": 10,
            "role": "belt",
            "surface": "shape",
            "placement_commit_state": "provisional_placed",
        },
    ]
    rep = validate_final_mining_layout(mining_map)
    assert rep.provisional_placed_row_count == 1
    assert not rep.geometry_valid


def test_build_solver_timeline_step4_frame_has_placement_commit_counts() -> None:
    decoded = _decoded_shape_miners_with_belt_escape()
    out = build_solver_timeline(decoded)
    frames = out.get("solver_timeline") or []
    s4 = next((f for f in frames if f.get("id") == "solver_step4_routing"), None)
    assert s4 is not None
    summ = s4.get("summary") or {}
    assert "step4_routed_count" in summ
    assert "step4_rolled_back_count" in summ
    assert "step4_quarantined_count" in summ
    assert summ.get("unfinalized_placement_count") == 0
    top = out.get("solver_summary") or {}
    assert "placement_commit_counts" in top
    assert top.get("unfinalized_placement_count") == 0


def test_step4_orphan_provisional_record_increments_unfinalized_trunk_count() -> None:
    decoded = _decoded_shape_miners_with_belt_escape()
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    _p1, m2, stats = integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    pr = dict(stats.get("placement_records") or {})
    pr["p1-999999"] = PlacementCommitRecord(
        placement_id="p1-999999",
        placement_pass="pass1",
        extractor_cell=(99, 99),
        extension_cells=(),
        stub_cell=(100, 99),
        transport_kind="shape_belt",
        state=PlacementCommitState.PROVISIONAL_PLACED,
    )
    r = run_step4_merge_aware_routing(
        m2, final_mining_map=fm, is_external=is_ext, placement_records=pr
    )
    assert r.trunk_load.get("unfinalized_placement_count") == 1


def test_step4_exception_restores_scratch_and_txn_working_map() -> None:
    """BaseException mid-STEP4 clears in-memory cells/work_records; txn rollback keeps pass2 map."""

    decoded = _decoded_shape_miners_with_belt_escape()
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    _p1, m2, stats = integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    pr = stats.get("placement_records")
    baseline_m2 = [dict(r) for r in m2]

    txn = mut_txn.SolverMutationTransaction(m2)
    txn.begin()

    def boom(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("simulated step4 failure")

    with (
        patch.object(step4_mod, "_p2c_revalidate_and_correct", boom),
        pytest.raises(RuntimeError, match="simulated step4 failure"),
    ):
        run_step4_merge_aware_routing(
            txn.working_map,
            final_mining_map=fm,
            is_external=is_ext,
            placement_records=pr,
            mutate_input_map=True,
        )

    txn.rollback()
    assert txn.working_map == baseline_m2
    assert m2 == baseline_m2


def test_build_solver_timeline_unfinalized_return_reason_orphan_placement_record() -> None:
    decoded = _decoded_shape_miners_with_belt_escape()
    real = p1_tl_mod.integrate_pass12_placement_into_working_map

    def wrapped(**kwargs):  # type: ignore[no-untyped-def]
        m1, m2, stats = real(**kwargs)
        pr = dict(stats.get("placement_records") or {})
        pr["p1-999999"] = PlacementCommitRecord(
            placement_id="p1-999999",
            placement_pass="pass1",
            extractor_cell=(99, 99),
            extension_cells=(),
            stub_cell=(100, 99),
            transport_kind="shape_belt",
            state=PlacementCommitState.PROVISIONAL_PLACED,
        )
        return m1, m2, {**stats, "placement_records": pr}

    with patch.object(p1_tl_mod, "integrate_pass12_placement_into_working_map", wrapped):
        out = build_solver_timeline(decoded)

    assert out["return_reason"] == "validation_unfinalized_placement_failed"
    assert out["ok"] is False
    assert out["solver_summary"]["unfinalized_placement_count"] >= 1
    assert out["final_validation"]["unfinalized_placement_count"] >= 1
