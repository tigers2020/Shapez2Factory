"""T6: NDJSON / solver_summary STEP4 telemetry schema regression gates (tests only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.test.utils import override_settings

from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
    build_solver_timeline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_failure_category as s4fc_mod,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_route_failure_detail as s4fd_mod,
)


def _never_external(_c: tuple[int, int]) -> bool:
    return False


def _minimal_route_failure_detail() -> dict[str, Any]:
    stub = (2, 2)
    ext = (2, 3)
    cells = {
        stub: {"x": 2, "y": 2, "role": "belt", "surface": "shape"},
        ext: {"x": 2, "y": 3, "role": "occupied", "layout_kind": "miner", "surface": "shape"},
    }
    blocked = frozenset({(3, 2), (1, 2), (2, 1)})
    hard = frozenset({(3, 2)})
    return s4fd_mod.build_step4_route_failure_detail(
        placement_id="p-t6-gate",
        extractor_cell=ext,
        stub_cell=stub,
        transport_kind="shape_belt",
        want_role="belt",
        blocked=blocked,
        hard_extras=hard,
        trunk_cells=frozenset(),
        goal_cells=frozenset({(10, 10)}),
        margin_cells={(10, 10)},
        transport_now=set(),
        cells=cells,
        mineable=frozenset(),
        asteroid=frozenset(),
        is_external=_never_external,
        cheap_reuse_cells=None,
        search_stats={
            "stop_reason": "exhausted",
            "expanded_nodes": 3,
            "heap_pops": 4,
            "goal_ordering_mode": "none",
        },
    )


def test_step4_route_failure_detail_has_canonical_fields() -> None:
    detail = _minimal_route_failure_detail()
    canon = s4fd_mod.STEP4_ROUTE_FAILURE_DETAIL_TOP_LEVEL_CANONICAL_KEYS
    missing_top = [k for k in canon if k not in detail]
    assert not missing_top, f"missing top-level canonical keys: {missing_top}"
    rfd = detail["routing_failure_detail"]
    rfd_keys = s4fd_mod.ROUTING_FAILURE_DETAIL_KEYS
    missing_rfd = [k for k in rfd_keys if k not in rfd]
    assert not missing_rfd, f"missing routing_failure_detail keys: {missing_rfd}"
    assert detail["failure_detail_phase"] is None
    assert detail["attempt_index"] == 0
    assert detail["rollback_reason"] is None
    assert detail["rejected_reason"] is None


def test_step4_route_failure_detail_preserves_existing_fields() -> None:
    detail = _minimal_route_failure_detail()
    assert isinstance(detail.get("blocked_reason_near_stub"), list)
    assert len(detail["blocked_reason_near_stub"]) == 4
    assert detail.get("expanded_nodes") == 3
    assert detail.get("last_error") == "no_route_exhausted"
    assert "nearest_existing_transport_distance" in detail


def test_step4_reachable_goal_fields_exist() -> None:
    detail = _minimal_route_failure_detail()
    for k in (
        "reachable_goal_count",
        "reachable_existing_trunk_count",
        "reachable_exterior_margin_count",
    ):
        assert k in detail
        assert k in detail["routing_failure_detail"]
    assert isinstance(detail["reachable_goal_count"], int)
    assert isinstance(detail["reachable_existing_trunk_count"], int)
    assert isinstance(detail["reachable_exterior_margin_count"], int)


def test_step4_failure_category_exists() -> None:
    detail = _minimal_route_failure_detail()
    cat = detail.get("step4_failure_category")
    assert cat is not None
    assert str(cat) in tuple(x.value for x in s4fc_mod.Step4FailureCategory)
    assert detail["routing_failure_detail"]["step4_failure_category"] == cat


def test_goal_ordering_mode_field_exists() -> None:
    detail = _minimal_route_failure_detail()
    assert detail.get("goal_ordering_mode") == "none"
    assert detail["routing_failure_detail"].get("goal_ordering_mode") == "none"


def test_additive_goal_cell_count_aliases() -> None:
    detail = _minimal_route_failure_detail()
    ext_ct = int(detail["external_goal_count"])
    assert detail["margin_goals_in_active_goal_cells_count"] == ext_ct
    assert detail["active_goal_cells_count"] == int(detail["goal_set_size"])
    rfd = detail["routing_failure_detail"]
    assert rfd["margin_goals_in_active_goal_cells_count"] == ext_ct
    assert rfd["active_goal_cells_count"] == int(rfd["goal_set_size"])


def test_step4_failure_classification_shape() -> None:
    detail = _minimal_route_failure_detail()
    clf = detail.get("step4_failure_classification")
    assert isinstance(clf, dict)
    assert set(clf.keys()) >= {"category", "confidence", "evidence"}
    assert clf["category"] == detail["step4_failure_category"]
    assert clf["confidence"] in ("high", "medium", "low")
    assert isinstance(clf["evidence"], dict)


def test_step4_outcome_fields_exist() -> None:
    detail = _minimal_route_failure_detail()
    for k in ("placement_commit_state", "quarantined", "rolled_back"):
        assert k in detail
        assert k in detail["routing_failure_detail"]
    assert detail["quarantined"] is False
    assert detail["rolled_back"] is False


def test_solver_summary_contains_step4_aggregates() -> None:
    decoded: dict[str, Any] = {
        "BP": {
            "Entries": [{"X": x, "Y": 0, "T": "Layout_ShapeMiner"} for x in range(10, 13)]
            + [{"X": x, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0} for x in range(13, 30)]
        }
    }
    with override_settings(SHAPEZ_MINING_ASSERT_STEP9_ROUTING_STATE=True):
        out = build_solver_timeline(decoded)
    ss = out.get("solver_summary") or {}
    required = (
        "step4_complete_routing_success",
        "step4_committed",
        "step4_routing_failure_count",
        "step4_failed_placement_ids",
        "step4_failure_details_count",
        "step4_failure_attempt_detail_count",
        "step4_failed_placement_count",
        "step4_route_failure_category_counts",
        "step4_route_failure_last_error_counts",
        "step4_route_failure_frontier_stop_reason_counts",
        "step4_search_mode_counts",
        "step4_failure_transport_kind_counts",
        "step4_reachable_goal_zero_count",
        "step4_search_budget_exhausted_count",
        "step4_rolled_back_failure_count",
        "step4_quarantined_failure_count",
    )
    missing = [k for k in required if k not in ss]
    assert not missing, f"solver_summary missing STEP4 aggregate keys: {missing}"


def test_summary_does_not_feed_algorithm() -> None:
    """Routing decision modules must not reference solver_summary / NDJSON consumption."""

    root = Path("django_apps/shapez_asteroid/services/asteroid_mining_layout/step4")
    for fname in (
        "step4_dijkstra.py",
        "step4_merge_routing.py",
        "step4_routing_permission.py",
    ):
        text = (root / fname).read_text(encoding="utf-8").lower()
        assert "solver_summary" not in text, f"{fname} must not mention solver_summary"
        assert "ndjson" not in text, f"{fname} must not mention ndjson"


def test_failure_detail_deterministic_ordering() -> None:
    d1 = _minimal_route_failure_detail()
    d2 = _minimal_route_failure_detail()
    keys_top = list(s4fd_mod.STEP4_ROUTE_FAILURE_DETAIL_TOP_LEVEL_CANONICAL_KEYS)
    blob1 = json.dumps({k: d1.get(k) for k in keys_top}, sort_keys=True)
    blob2 = json.dumps({k: d2.get(k) for k in keys_top}, sort_keys=True)
    assert blob1 == blob2
    rfd1 = json.dumps(d1["routing_failure_detail"], sort_keys=True)
    rfd2 = json.dumps(d2["routing_failure_detail"], sort_keys=True)
    assert rfd1 == rfd2


def test_committed_false_does_not_use_commit_reason_for_failure() -> None:
    detail = _minimal_route_failure_detail()
    assert "commit_reason" not in detail
    rfd = detail["routing_failure_detail"]
    assert "commit_reason" not in rfd
    s4fd_mod.apply_routing_failure_detail_lifecycle(
        detail,
        quarantined=True,
        placement_commit_state="quarantined_unrouted",
    )
    assert "commit_reason" not in detail
    assert "commit_reason" not in detail["routing_failure_detail"]
