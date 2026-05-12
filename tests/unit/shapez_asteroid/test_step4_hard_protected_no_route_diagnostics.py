"""STEP4 hard-protected stub ring diagnostics (telemetry only; no routing semantics)."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass1_timeline_integration import (  # noqa: E501
    integrate_pass12_placement_into_working_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_hard_protected_no_route_diagnostics as s4hp,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_route_failure_diagnostic as s4frd,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_merge_routing import (
    run_step4_merge_aware_routing,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    external_predicate_for_mining_map,
)
from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline
from tests.unit.shapez_asteroid.test_step4_merge_routing import (
    _decoded_shape_miners_with_belt_escape,
)


def _ring_detail(*, soft_blocked: tuple[int, int] | None = None) -> dict:
    """Stub at (5,5) with four ``hard_protected`` neighbors (grid ring)."""

    near = [
        {"cell": [5, 6], "reason": "hard_protected"},
        {"cell": [6, 5], "reason": "hard_protected"},
        {"cell": [5, 4], "reason": "hard_protected"},
        {"cell": [4, 5], "reason": "hard_protected"},
    ]
    if soft_blocked is not None:
        sx, sy = soft_blocked
        near[0] = {"cell": [sx, sy], "reason": "blocked"}
    return {"blocked_reason_near_stub": near, "last_error": "no_route_exhausted"}


def test_is_hard_protected_stub_ring_failure() -> None:
    assert s4frd.is_hard_protected_stub_ring_failure(_ring_detail())
    assert not s4frd.is_hard_protected_stub_ring_failure({"blocked_reason_near_stub": []})
    assert not s4frd.is_hard_protected_stub_ring_failure(
        {
            "blocked_reason_near_stub": [
                {"cell": [5, 6], "reason": "hard_protected"},
                {"cell": [6, 5], "reason": "ok"},
            ]
        }
    )


def test_build_ring_trace_fields_trunk_beyond_and_soft() -> None:
    stub = (5, 5)
    hard = frozenset({(5, 6), (6, 5), (5, 4), (4, 5)})
    trunk = frozenset({(7, 5)})  # touches (6,5) but not stub
    ela = {
        "pass12_soft_protected_corridor_cells": [[5, 6]],
        "protected_corridor_ids": ["c-a", "c-z"],
    }
    detail = _ring_detail(soft_blocked=(5, 6))
    tr = s4hp.build_step4_hard_protected_ring_trace_fields(
        detail=detail,
        stub_cell=stub,
        trunk_cells=trunk,
        hard_extras=hard,
        existing_layout_analysis=ela,
    )
    assert tr["hard_protected_neighbors_near_stub"] == 3
    assert tr["same_kind_trunk_beyond_protected"] is True
    assert tr["bypass_candidate_count"] == 0
    assert tr["soft_replace_candidate_count"] == 1
    assert tr["protected_corridor_ids"] == ["c-a", "c-z"]


def test_build_step4_hard_protected_no_route_breakdown() -> None:
    tr = s4hp.build_step4_hard_protected_ring_trace_fields(
        detail=_ring_detail(),
        stub_cell=(5, 5),
        trunk_cells=frozenset(),
        hard_extras=frozenset({(5, 6), (6, 5), (5, 4), (4, 5)}),
        existing_layout_analysis=None,
    )
    row = {
        "transport_kind": "shape_belt",
        "extractor_id": "p-test",
        "step4_hard_protected_no_route_trace": tr,
        "step4_route_failure_diagnostic": {
            "placement_pass": "pass2",
            "placement_id": "p-test",
        },
    }
    b = s4frd.build_step4_hard_protected_no_route_breakdown([row])
    assert b["count"] == 1
    assert b["by_transport_kind"] == {"shape_belt": 1}
    assert b["by_placement_pass"] == {"pass2": 1}
    assert b["same_kind_trunk_beyond_protected"] == {"true": 0, "false": 1}
    assert b["bypass_candidate_total"] == 0
    assert b["soft_replace_candidate_total"] == 0
    assert b["hard_protected_neighbors_near_stub"]["min"] == 4
    assert len(b["sample_traces"]) == 1
    assert b["sample_traces"][0]["placement_id"] == "p-test"


def test_merge_trunk_load_always_has_hard_protected_breakdown() -> None:
    decoded = _decoded_shape_miners_with_belt_escape()
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    _p1, m2, stats = integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    pr = stats.get("placement_records") or {}
    r = run_step4_merge_aware_routing(
        m2,
        final_mining_map=fm,
        is_external=is_ext,
        placement_records=pr,
        hard_protected_cells=frozenset({(99, 99)}),
    )
    assert r.committed
    hpbd = r.trunk_load.get("step4_hard_protected_no_route_breakdown")
    assert isinstance(hpbd, dict)
    assert hpbd.get("count") == 0
    assert hpbd.get("bypass_candidate_total") == 0
