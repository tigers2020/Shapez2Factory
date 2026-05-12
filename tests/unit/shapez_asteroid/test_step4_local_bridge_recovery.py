"""STEP4 bounded local bridge recovery (subset goals, Pass2 provisional)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitRecord,
    PlacementCommitState,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    blocked_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    want_role as _want_role_factory,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_goal_trunk_seed as _s4g,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_local_bridge_recovery as _s4lb,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_map_ops as _s4mo,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_merge_routing as _s4merge,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
    final_validation as _s15,
)

build_step4_goal_set = _s4g.build_step4_goal_set
bridge_goal_subset_for_local_recovery = _s4lb.bridge_goal_subset_for_local_recovery
build_trunk_seed_candidates_by_kind = _s4g.build_trunk_seed_candidates_by_kind
cells_dict_from_mining_map = _s15.cells_dict_from_mining_map
exterior_margin_cells = _s4g.exterior_margin_cells
run_step4_merge_aware_routing = _s4merge.run_step4_merge_aware_routing
same_kind_transport_cells = _s4mo.same_kind_transport_cells
transport_cells_reaching_external = _s15.transport_cells_reaching_external
try_step4_local_bridge_recovery = _s4lb.try_step4_local_bridge_recovery
validate_final_mining_layout = _s15.validate_final_mining_layout


def _void_detour_hard_wall() -> frozenset[Coord]:
    """Block cheap void shortcuts (y=±1) so belt routing stays on the mineable strip."""

    xs = range(2, 14)
    return frozenset({(x, 1) for x in xs} | {(x, -1) for x in xs})


def test_bridge_goal_subset_deterministic_order() -> None:
    stub: Coord = (0, 0)
    trunk = frozenset({(2, 0), (0, 2), (1, 1)})
    goals = frozenset({(2, 0), (5, 5)})
    margin = {(5, 5)}
    g = bridge_goal_subset_for_local_recovery(
        stub,
        trunk_cells=trunk,
        goal_cells=goals,
        margin_cells=margin,
    )
    assert (1, 1) in g or (2, 0) in g
    assert len(g) <= 12 + 4


def _rows_belt_line_to_external() -> tuple[list[dict[str, Any]], Callable[[Coord], bool]]:
    """Belt trunk on y=0; external east of x=12."""

    surface = "shape"
    rows: list[dict[str, Any]] = []

    def is_ext(c: Coord) -> bool:
        return c == (13, 0)

    for x in range(2, 13):
        rows.append(
            {
                "x": x,
                "y": 0,
                "role": "inferred",
                "layout_kind": "asteroid_field",
                "surface": surface,
            }
        )
    for x in range(5, 13):
        rows.append({"x": x, "y": 0, "role": "belt", "surface": surface})
    rows.append(
        {
            "x": 3,
            "y": 0,
            "role": "occupied",
            "layout_kind": "miner",
            "surface": surface,
            "r": 0,
            "placement_id": "p2-bridge",
        }
    )
    rows.append(
        {
            "x": 4,
            "y": 0,
            "role": "belt",
            "surface": surface,
            "placement_id": "p2-bridge",
        }
    )
    return rows, is_ext


def _pass2_rec_for_bridge() -> dict[str, PlacementCommitRecord]:
    return {
        "p2-bridge": PlacementCommitRecord(
            placement_id="p2-bridge",
            placement_pass="pass2",
            extractor_cell=(3, 0),
            extension_cells=(),
            stub_cell=(4, 0),
            transport_kind="shape_belt",
            state=PlacementCommitState.PROVISIONAL_PLACED,
        )
    }


def test_try_local_bridge_rejects_not_no_route_exhausted() -> None:
    rows, is_ext = _rows_belt_line_to_external()
    cells = cells_dict_from_mining_map(rows)
    mineable = frozenset((c for c, r in cells.items() if r.get("layout_kind") == "asteroid_field"))
    asteroid: frozenset[Coord] = frozenset()

    want_role = _want_role_factory("shape_belt")
    margin = exterior_margin_cells(
        mineable=mineable, asteroid=asteroid, cells=cells, is_external=is_ext
    )
    trunk_seed = build_trunk_seed_candidates_by_kind(
        exterior_margin=margin, hint_union=set(), cells=cells
    )
    raw_goal = build_step4_goal_set(
        "shape_belt",
        committed_trunk_by_kind={},
        exterior_margin_cells=margin,
        trunk_seed_candidates_by_kind=trunk_seed,
    )
    hard_extras: frozenset[Coord] = frozenset()
    blocked_set = set(blocked_cells(cells)) | set(hard_extras)
    stub_cell: Coord = (4, 0)
    blocked_set.discard(stub_cell)
    blocked = frozenset(blocked_set)
    transport_now = same_kind_transport_cells(cells, want_role)
    trunk_cells = frozenset(transport_cells_reaching_external(transport_now, set(blocked), is_ext))
    goal_cells = frozenset(raw_goal | set(trunk_cells))
    rec = _pass2_rec_for_bridge()["p2-bridge"]
    detail: dict[str, Any] = {
        "placement_id": "p2-bridge",
        "extractor_cell": [3, 0],
        "stub_cell": [4, 0],
        "transport_kind": "shape_belt",
        "nearest_existing_transport_distance": 1,
        "nearest_existing_transport_cell": [5, 0],
        "existing_trunk_goal_count": len(trunk_cells),
        "external_goal_count": len(goal_cells & margin),
        "blocked_reason_near_stub": [],
        "search_mode": "goal_cells_union_legacy",
        "expanded_nodes": 0,
        "fallback_reason": None,
        "last_error": "no_route_budget",
    }
    search_stats = {
        "search_mode": "goal_cells_union_legacy",
        "stop_reason": "budget",
        "expanded_nodes": 1,
    }
    out, reason, attempted, meta = try_step4_local_bridge_recovery(
        ext_cell=(3, 0),
        stub_cell=stub_cell,
        tk="shape_belt",
        rec=rec,
        cells=cells,
        mineable=mineable,
        asteroid=asteroid,
        is_external=is_ext,
        blocked=blocked,
        trunk_cells=trunk_cells,
        goal_cells=goal_cells,
        raw_goal=set(raw_goal),
        margin_cells=margin,
        trunk_seed_by_kind=trunk_seed,
        committed_trunk_by_kind={},
        cheap_reuse_cells=frozenset(trunk_cells),
        hard_extras=hard_extras,
        detail=detail,
        search_stats=search_stats,
        want_role=want_role,
        committed_trunk_for_kind=set(),
    )
    assert attempted
    assert out is None
    assert reason == "not_no_route_exhausted"
    assert meta is not None


def test_try_local_bridge_hard_protected_rejects() -> None:
    rows, is_ext = _rows_belt_line_to_external()
    cells = cells_dict_from_mining_map(rows)
    mineable = frozenset((c for c, r in cells.items() if r.get("layout_kind") == "asteroid_field"))
    asteroid: frozenset[Coord] = frozenset()

    want_role = _want_role_factory("shape_belt")
    margin = exterior_margin_cells(
        mineable=mineable, asteroid=asteroid, cells=cells, is_external=is_ext
    )
    trunk_seed = build_trunk_seed_candidates_by_kind(
        exterior_margin=margin, hint_union=set(), cells=cells
    )
    raw_goal = build_step4_goal_set(
        "shape_belt",
        committed_trunk_by_kind={},
        exterior_margin_cells=margin,
        trunk_seed_candidates_by_kind=trunk_seed,
    )
    stub_cell: Coord = (4, 0)
    # Block the east trunk on y=0 and void shortcuts so local search cannot bypass hard blocks.
    hard_extras = _void_detour_hard_wall() | frozenset({(x, 0) for x in range(5, 12)})
    blocked_set = set(blocked_cells(cells)) | set(hard_extras)
    blocked_set.discard(stub_cell)
    blocked = frozenset(blocked_set)
    transport_now = same_kind_transport_cells(cells, want_role)
    trunk_cells = frozenset(transport_cells_reaching_external(transport_now, set(blocked), is_ext))
    goal_cells = frozenset(raw_goal | set(trunk_cells))
    rec = _pass2_rec_for_bridge()["p2-bridge"]
    detail: dict[str, Any] = {
        "placement_id": "p2-bridge",
        "extractor_cell": [3, 0],
        "stub_cell": [4, 0],
        "transport_kind": "shape_belt",
        "nearest_existing_transport_distance": 1,
        "nearest_existing_transport_cell": [5, 0],
        "existing_trunk_goal_count": len(trunk_cells),
        "external_goal_count": len(goal_cells & margin),
        "blocked_reason_near_stub": [
            {"cell": [5, 0], "reason": "ok"},
            {"cell": [3, 0], "reason": "ok"},
        ],
        "search_mode": "goal_cells_union_legacy",
        "expanded_nodes": 5,
        "fallback_reason": None,
        "last_error": "no_route_exhausted",
    }
    search_stats = {
        "search_mode": "goal_cells_union_legacy",
        "stop_reason": "exhausted",
        "expanded_nodes": 5,
    }
    out, reason, attempted, _meta = try_step4_local_bridge_recovery(
        ext_cell=(3, 0),
        stub_cell=stub_cell,
        tk="shape_belt",
        rec=rec,
        cells=cells,
        mineable=mineable,
        asteroid=asteroid,
        is_external=is_ext,
        blocked=blocked,
        trunk_cells=trunk_cells,
        goal_cells=goal_cells,
        raw_goal=set(raw_goal),
        margin_cells=margin,
        trunk_seed_by_kind=trunk_seed,
        committed_trunk_by_kind={},
        cheap_reuse_cells=frozenset(trunk_cells),
        hard_extras=hard_extras,
        detail=detail,
        search_stats=search_stats,
        want_role=want_role,
        committed_trunk_for_kind=set(),
    )
    assert attempted
    assert out is None
    assert reason == "exhausted"


def test_merge_local_bridge_success_when_primary_exhausted(monkeypatch: pytest.MonkeyPatch) -> None:
    """Primary full-goal search forced to fail; Pass2 recovery no-op; bridge succeeds."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
        step4_failed_pass2_route_recovery as p2r,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
        step4_merge_routing as m4,
    )

    rows, is_ext = _rows_belt_line_to_external()
    final_rows = [dict(r) for r in rows]
    pr = _pass2_rec_for_bridge()

    real_d = m4.dijkstra_route_step4
    call_n = {"n": 0}

    def _wrap(*a: Any, **kw: Any) -> Any:
        call_n["n"] += 1
        ss = kw.get("search_stats")
        if call_n["n"] == 1:
            if ss is not None:
                ss["stop_reason"] = "exhausted"
                # Keep within narrow bucket so local bridge trigger stays in scope.
                ss["expanded_nodes"] = 5
            return None
        return real_d(*a, **kw)

    monkeypatch.setattr(m4, "_dijkstra_route", _wrap)
    monkeypatch.setattr(p2r, "try_step4_failed_pass2_route_recovery", lambda *_a, **_kw: (None, 0))
    r = run_step4_merge_aware_routing(
        rows,
        final_mining_map=final_rows,
        is_external=is_ext,
        placement_records=pr,
        force_route_attempt_placement_ids=frozenset({"p2-bridge"}),
    )
    assert r.committed
    assert int(r.trunk_load.get("step4_local_bridge_recovery_success_count", 0) or 0) >= 1
    rep = validate_final_mining_layout(r.map_after_routing)
    assert rep.geometry_valid
    assert rep.connectivity_valid


def test_merge_local_bridge_wrong_kind_pipe_blocks_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fluid pipe on stub corridor blocks belt expansion (step cost None)."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
        step4_failed_pass2_route_recovery as p2r,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
        step4_merge_routing as m4,
    )

    rows, is_ext = _rows_belt_line_to_external()
    rows.append({"x": 5, "y": 0, "role": "pipe", "surface": "fluid"})
    final_rows = [dict(r) for r in rows]
    pr = _pass2_rec_for_bridge()

    real_d = m4.dijkstra_route_step4
    call_n = {"n": 0}

    def _wrap(*a: Any, **kw: Any) -> Any:
        call_n["n"] += 1
        ss = kw.get("search_stats")
        if call_n["n"] == 1:
            if ss is not None:
                ss["stop_reason"] = "exhausted"
                ss["expanded_nodes"] = 5
            return None
        return real_d(*a, **kw)

    monkeypatch.setattr(m4, "_dijkstra_route", _wrap)
    monkeypatch.setattr(p2r, "try_step4_failed_pass2_route_recovery", lambda *_a, **_kw: (None, 0))
    r = run_step4_merge_aware_routing(
        rows,
        final_mining_map=final_rows,
        is_external=is_ext,
        placement_records=pr,
        force_route_attempt_placement_ids=frozenset({"p2-bridge"}),
        hard_protected_cells=_void_detour_hard_wall(),
    )
    assert not r.committed
    assert int(r.trunk_load.get("step4_local_bridge_recovery_rejected_count", 0) or 0) >= 1


def test_merge_rollback_when_unrecoverable(monkeypatch: pytest.MonkeyPatch) -> None:
    """No bridge path: rolled_back list populated like pre-bridge failure."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
        step4_failed_pass2_route_recovery as p2r,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
        step4_merge_routing as m4,
    )

    rows, is_ext = _rows_belt_line_to_external()
    for x in range(5, 12):
        rows.append(
            {
                "x": x,
                "y": 1,
                "role": "occupied",
                "layout_kind": "fluid_extension",
                "surface": "fluid",
            }
        )
    for x in range(5, 12):
        rows.append({"x": x, "y": -1, "role": "pipe", "surface": "fluid"})
    final_rows = [dict(r) for r in rows]
    pr = _pass2_rec_for_bridge()

    real_d = m4.dijkstra_route_step4
    call_n = {"n": 0}

    def _wrap(*a: Any, **kw: Any) -> Any:
        call_n["n"] += 1
        ss = kw.get("search_stats")
        if call_n["n"] == 1:
            if ss is not None:
                ss["stop_reason"] = "exhausted"
                ss["expanded_nodes"] = 5
            return None
        return real_d(*a, **kw)

    monkeypatch.setattr(m4, "_dijkstra_route", _wrap)
    monkeypatch.setattr(p2r, "try_step4_failed_pass2_route_recovery", lambda *_a, **_kw: (None, 0))
    r = run_step4_merge_aware_routing(
        rows,
        final_mining_map=final_rows,
        is_external=is_ext,
        placement_records=pr,
        force_route_attempt_placement_ids=frozenset({"p2-bridge"}),
        hard_protected_cells=_void_detour_hard_wall() | frozenset({(x, 0) for x in range(5, 13)}),
    )
    assert not r.committed
    assert r.rolled_back_placement_ids
