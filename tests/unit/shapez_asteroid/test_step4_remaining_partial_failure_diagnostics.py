"""Pass2 first-route margin trace + STEP4 route-failure classifier (partial-failure diagnostics)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass12_route_probe as p12rp,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_route_failure_diagnostic as s4frd,
)


def _is_ext(c: Coord, ext: Coord) -> bool:
    return c == ext


def _external_at(ext: Coord) -> Callable[[Coord], bool]:
    def _pred(c: Coord) -> bool:
        return _is_ext(c, ext)

    return _pred


def _row_inferred(x: int, y: int) -> dict[str, Any]:
    return {"x": x, "y": y, "role": "inferred", "layout_kind": "asteroid_field", "surface": "shape"}


def test_first_route_positive_margin_final_goal_count() -> None:
    """Exterior margin exists → nonzero goals (Outcome A contract satisfied)."""

    ext: Coord = (5, 0)
    is_external = _external_at(ext)
    mineable = frozenset({(4, 0), (3, 0)})
    asteroid: frozenset[Coord] = frozenset()
    cells: dict[Coord, dict[str, Any]] = {
        (3, 0): _row_inferred(3, 0),
        (4, 0): _row_inferred(4, 0),
    }
    _, kind, n, trace = p12rp.build_pass2_step4_aligned_routing_goals(
        transport_kind="shape_belt",
        mineable=mineable,
        asteroid=asteroid,
        cells=cells,
        is_external=is_external,
        existing_layout_analysis=None,
        transport_cells_before=frozenset(),
        transport_cells_probe=frozenset({(4, 0)}),
        blocked_for_probe=frozenset(),
    )
    assert kind == "first_route"
    assert n > 0
    assert trace["final_goal_count"] > 0
    assert trace["exterior_margin_cell_count"] >= 1
    assert trace["universe_cell_count"] >= 2
    assert trace["rejected_reason"] is None


def test_first_route_no_exterior_margin_for_probe_reason() -> None:
    """No universe cell neighbors external → explicit ``no_exterior_margin_for_probe``."""

    ext: Coord = (5, 0)
    is_external = _external_at(ext)
    mineable = frozenset({(3, 0)})
    asteroid: frozenset[Coord] = frozenset()
    cells: dict[Coord, dict[str, Any]] = {(3, 0): _row_inferred(3, 0)}
    _, kind, n, trace = p12rp.build_pass2_step4_aligned_routing_goals(
        transport_kind="shape_belt",
        mineable=mineable,
        asteroid=asteroid,
        cells=cells,
        is_external=is_external,
        existing_layout_analysis=None,
        transport_cells_before=frozenset(),
        transport_cells_probe=frozenset(),
        blocked_for_probe=frozenset(),
    )
    assert kind == "first_route"
    assert n == 0
    assert trace["exterior_margin_cell_count"] == 0
    exp = str(s4frd.Step4RouteFailureReason.no_exterior_margin_for_probe)
    assert trace["rejected_reason"] == exp
    assert trace["mineable_asteroid_bbox"] == {"x_min": 3, "x_max": 3, "y_min": 0, "y_max": 0}
    md = trace["pass2_external_margin_diagnostic"]
    assert md["margin_eligible_universe_cell_count"] == 1
    assert "margin_generation_reason_if_zero" in md


def test_classifier_no_route_exhausted_before_mixed_stub_inferred() -> None:
    """Exhausted search with goals: not ``mixed_transport_kind`` (inferred stub ok path)."""

    detail: dict[str, Any] = {
        "last_error": "no_route_exhausted",
        "blocked_reason_near_stub": [{"cell": (0, 0), "reason": "ok"}],
    }
    r = s4frd.classify_step4_route_failure_reason(
        goal_count=93,
        exterior_goal_count=0,
        existing_trunk_goal_count=85,
        stub_cell_role_ok=False,
        nearest_transport_hops=2,
        stop_reason=None,
        detail=detail,
        route_length_ratio_exceeded=False,
    )
    assert r == s4frd.Step4RouteFailureReason.no_route_exhausted


def test_classifier_mixed_transport_kind_when_not_exhausted() -> None:
    """True role mismatch when search did not exhaust → ``mixed_transport_kind``."""

    detail: dict[str, Any] = {
        "last_error": "no_route",
        "blocked_reason_near_stub": [{"cell": (0, 0), "reason": "ok"}],
    }
    r = s4frd.classify_step4_route_failure_reason(
        goal_count=5,
        exterior_goal_count=1,
        existing_trunk_goal_count=2,
        stub_cell_role_ok=False,
        nearest_transport_hops=1,
        stop_reason=None,
        detail=detail,
        route_length_ratio_exceeded=False,
    )
    assert r == s4frd.Step4RouteFailureReason.mixed_transport_kind


def test_build_diagnostic_includes_classifier_fields() -> None:
    """``build_step4_route_failure_diagnostic`` emits stub-role + classifier_inputs."""

    def _never_external(_c: Coord) -> bool:
        return False

    detail: dict[str, Any] = {
        "nearest_existing_transport_distance": 2,
        "blocked_reason_near_stub": [{"cell": (0, 0), "reason": "ok"}],
        "last_error": "no_route_exhausted",
    }
    d = s4frd.build_step4_route_failure_diagnostic(
        rec=None,
        extractor_cell=(1, 1),
        stub_cell=(2, 2),
        transport_kind="fluid_pipe",
        want_role="pipe",
        raw_goal={(1, 1)},
        goal_cells=frozenset({(1, 1), (3, 3)}),
        trunk_cells=frozenset({(3, 3)}),
        trunk_seed_candidates_by_kind={"shape_belt": set(), "fluid_pipe": set()},
        margin_cells=set(),
        committed_trunk_for_kind={(3, 3)},
        blocked=frozenset(),
        hard_extras=frozenset(),
        cells={(2, 2): {"x": 2, "y": 2, "role": "inferred"}},
        mineable=frozenset(),
        asteroid=frozenset(),
        is_external=_never_external,
        cheap_reuse_cells=None,
        search_stats={"stop_reason": None, "search_mode": "goal_cells_union_legacy"},
        detail=detail,
        final_state="rolled_back",
    )
    assert d["failure_reason"] == s4frd.Step4RouteFailureReason.no_route_exhausted.value
    assert d["stub_cell_role_ok"] is False
    assert d["stub_role"] == "inferred"
    assert d["expected_stub_role"] == "pipe"
    assert d["classifier_inputs"]["last_error"] == "no_route_exhausted"
    assert d["search_exhausted"] is True


def test_no_route_exhausted_breakdown_empty_failures() -> None:
    """Empty ``failures`` → fixed zero skeleton (contract keys + types)."""

    b = s4frd.build_step4_no_route_exhausted_breakdown([])
    assert b == {
        "count": 0,
        "by_transport_kind": {},
        "by_placement_pass": {},
        "by_nearest_transport_hops": {},
        "by_blocked_reason_near_stub": {},
        "by_goal_count": {},
        "by_existing_trunk_goal_count": {},
        "by_protected_hard_count": {},
        "by_protected_soft_count": {},
        "by_expanded_nodes_bucket": {},
        "expanded_nodes": {"min": None, "max": None, "mean": None},
        "by_breaker_category": {},
        "dominant_blocker_category": None,
        "sample_rows": [],
    }


def _nr_diag_row(**diag_kw: Any) -> dict[str, Any]:
    pid = diag_kw.pop("placement_id", "placement_nr_test")
    base: dict[str, Any] = {
        "failure_reason": s4frd.Step4RouteFailureReason.no_route_exhausted.value,
        "transport_kind": "fluid_pipe",
        "placement_pass": 2,
        "goal_count": 3,
        "existing_trunk_goal_count": 2,
        "exterior_goal_count": 0,
        "protected_hard_count": 0,
        "protected_soft_count": 0,
        "expanded_nodes": 5,
        "classifier_inputs": {"nearest_transport_hops": 1},
    }
    base.update(diag_kw)
    return {
        "placement_id": pid,
        "step4_route_failure_diagnostic": base,
        "step4_route_failure_detail": {
            "blocked_reason_near_stub": [{"cell": (1, 2), "reason": "ok"}],
        },
    }


def test_no_route_exhausted_breakdown_filters_other_reasons() -> None:
    """Only ``no_route_exhausted`` rows count; dominant uses declaration-order tie-break."""

    other = {
        "step4_route_failure_diagnostic": {
            "failure_reason": s4frd.Step4RouteFailureReason.no_same_kind_route.value,
            "transport_kind": "shape_belt",
            "placement_pass": 1,
        },
    }
    narrow = _nr_diag_row(
        placement_id="narrow1", expanded_nodes=5, exterior_goal_count=1, existing_trunk_goal_count=0
    )
    wide = _nr_diag_row(
        placement_id="wide1", expanded_nodes=25, exterior_goal_count=1, existing_trunk_goal_count=0
    )
    b = s4frd.build_step4_no_route_exhausted_breakdown(
        [_nr_diag_row(), _nr_diag_row(), other, narrow, wide]
    )
    assert b["count"] == 4
    assert b["by_transport_kind"] == {"fluid_pipe": 4}
    assert b["by_placement_pass"] == {"2": 4}
    assert b["by_breaker_category"]["narrow_search_exhausted"] == 1
    assert b["by_breaker_category"]["wide_search_exhausted"] == 1
    assert b["by_breaker_category"]["trunk_union_goals_unreachable_from_stub"] == 2
    assert b["dominant_blocker_category"] == "trunk_union_goals_unreachable_from_stub"
    assert [r["placement_id"] for r in b["sample_rows"]] == [
        "placement_nr_test",
        "placement_nr_test",
        "narrow1",
        "wide1",
    ]
    for r in b["sample_rows"]:
        assert "breaker_category" in r
        assert r["transport_kind"] == "fluid_pipe"


def test_no_route_exhausted_breakdown_trunk_union_breaker() -> None:
    """``exterior_goal_count==0`` and ``existing_trunk_goal_count>0`` without geometry/hard ring."""

    row = {
        "placement_id": "trunk-union-1",
        "step4_route_failure_detail": {
            "step4_route_failure_diagnostic": {
                "failure_reason": s4frd.Step4RouteFailureReason.no_route_exhausted.value,
                "transport_kind": "fluid_pipe",
                "placement_pass": 1,
                "goal_count": 5,
                "exterior_goal_count": 0,
                "existing_trunk_goal_count": 3,
                "protected_hard_count": 0,
                "protected_soft_count": 0,
                "expanded_nodes": 15,
                "classifier_inputs": {},
            },
            "nearest_existing_transport_distance": 4,
            "blocked_reason_near_stub": [{"cell": (0, 0), "reason": "ok"}],
        },
    }
    b = s4frd.build_step4_no_route_exhausted_breakdown([row])
    assert b["count"] == 1
    assert b["by_breaker_category"] == {"trunk_union_goals_unreachable_from_stub": 1}
    assert b["dominant_blocker_category"] == "trunk_union_goals_unreachable_from_stub"
    assert b["sample_rows"] == [
        {
            "placement_id": "trunk-union-1",
            "stub_cell": None,
            "extractor_cell": None,
            "transport_kind": "fluid_pipe",
            "placement_pass": 1,
            "breaker_category": "trunk_union_goals_unreachable_from_stub",
            "goal_count": 5,
            "existing_trunk_goal_count": 3,
            "exterior_goal_count": 0,
            "blocked_near_stub": [{"x": 0, "y": 0, "reason": "ok"}],
        }
    ]


def test_no_route_exhausted_breakdown_expanded_nodes_stats_and_buckets() -> None:
    """Integer ``expanded_nodes`` only → buckets + min/max/mean."""

    def one(expanded: int) -> dict[str, Any]:
        return _nr_diag_row(
            expanded_nodes=expanded,
            exterior_goal_count=1,
            existing_trunk_goal_count=0,
        )

    b = s4frd.build_step4_no_route_exhausted_breakdown([one(1), one(10), one(40)])
    assert b["count"] == 3
    assert b["by_expanded_nodes_bucket"] == {"0-1": 1, "8-32": 1, "33+": 1}
    assert b["expanded_nodes"]["min"] == 1
    assert b["expanded_nodes"]["max"] == 40
    assert len(b["sample_rows"]) == 3
    assert b["expanded_nodes"]["mean"] == round((1 + 10 + 40) / 3.0, 4)
