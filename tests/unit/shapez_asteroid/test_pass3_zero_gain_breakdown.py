"""S5: Pass3 zero-gain reject buckets, outcome classification, and related invariants."""

from __future__ import annotations

from unittest.mock import patch

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_ABOVE_PASS2_BASELINE,
    P3E3_REJECT_HARD_PROTECTED_CORRIDOR,
    P3E3_REJECT_NO_INTERNAL_TRANSPORT_GAIN,
    P3E3_REJECT_PRECHECK_NO_CANDIDATE,
    P3E3_REJECT_PRECHECK_NO_REPLACEMENT_ROUTE,
    PASS3_GREEDY_REJECT_DETAIL_CONNECTIVITY,
    SOLVER_QUALITY_TIER_SOLVER_FAILURE,
    SOLVER_QUALITY_TIER_SUCCESS_VALID_WITH_OPTIMIZATION_WARNING,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3 import (
    pass3_zero_gain_breakdown as p3_zg,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_e3_guarded import (
    _p3e3_atomic_trace_from_dto,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_e3_guarded_dto import (
    P3E3GuardedCommitCandidate,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_greedy_core import (
    placement_stub_route_probe_path,
    reconstruct_mining_priority_transport,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.internal_transport_metrics import (  # noqa: E501
    count_internal_transport_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.finalize import (
    SOLVER_TERMINATION_SUCCESS,
    _compute_solver_quality_tier,
)


def test_aggregate_counts_hard_protected_block() -> None:
    tr = {
        "p3f_rejected_reason_raw": P3E3_REJECT_HARD_PROTECTED_CORRIDOR,
        "pass3_internal_transport_saved": 0,
    }
    agg = p3_zg.aggregate_pass3_reject_by_reason(tr)
    assert agg[p3_zg.PASS3_REJECT_HARD_PROTECTED_BLOCK] >= 1


def test_aggregate_counts_no_replacement_route() -> None:
    tr = {
        "p3f_rejected_reason_raw": P3E3_REJECT_PRECHECK_NO_REPLACEMENT_ROUTE,
        "pass3_internal_transport_saved": 0,
    }
    agg = p3_zg.aggregate_pass3_reject_by_reason(tr)
    assert agg[p3_zg.PASS3_REJECT_NO_REPLACEMENT_ROUTE] >= 1


def test_outcome_no_candidates_vs_candidates_rejected() -> None:
    no_cand = {
        "pass3_skipped": False,
        "pass3_internal_transport_saved": 0,
        "p3f_rejected_reason_raw": P3E3_REJECT_PRECHECK_NO_CANDIDATE,
        "p3f_candidate_kind_count": 0,
    }
    assert p3_zg.classify_pass3_zero_gain_outcome(no_cand) == p3_zg.PASS3_OUTCOME_NO_CANDIDATES

    rejected = {
        "pass3_skipped": False,
        "pass3_internal_transport_saved": 0,
        "p3f_rejected_reason_raw": P3E3_REJECT_NO_INTERNAL_TRANSPORT_GAIN,
        "p3f_candidate_kind_count": 2,
        "p3f_internal_transport_delta": 1,
    }
    got = p3_zg.classify_pass3_zero_gain_outcome(rejected)
    assert got == p3_zg.PASS3_OUTCOME_CANDIDATES_REJECTED


def test_enrich_zero_gain_summary_flags_reject_total() -> None:
    tr = {
        "pass3_skipped": False,
        "pass3_internal_transport_saved": 0,
        "p3f_rejected_reason_raw": P3E3_REJECT_NO_INTERNAL_TRANSPORT_GAIN,
        "p3f_candidate_kind_count": 1,
        "pass3_greedy_reject_detail": PASS3_GREEDY_REJECT_DETAIL_CONNECTIVITY,
        "p3e2_outlet_count": 1,
        "pass3_transport_kind": "belt",
        "pass3_routing_job_count": 1,
        "p3e2_lex_search_mode": "lex_dijkstra",
    }
    p3_zg.enrich_pass3_trace_zero_gain_telemetry(tr)
    assert tr["pass3_zero_gain_outcome"] == p3_zg.PASS3_OUTCOME_CANDIDATES_REJECTED
    assert "reject_total=" in tr["pass3_zero_gain_summary"]
    assert tr["pass3_reject_by_reason"][p3_zg.PASS3_REJECT_NO_INTERNAL_TRANSPORT_SAVING] >= 1
    assert tr["pass3_reject_by_reason"][p3_zg.PASS3_REJECT_CONNECTIVITY_BREAK] >= 1


def test_skipped_outcome() -> None:
    tr = {"pass3_skipped": True, "pass3_internal_transport_saved": 0}
    assert p3_zg.classify_pass3_zero_gain_outcome(tr) == p3_zg.PASS3_OUTCOME_SKIPPED


def test_improved_outcome() -> None:
    tr = {"pass3_skipped": False, "pass3_internal_transport_saved": 2}
    assert p3_zg.classify_pass3_zero_gain_outcome(tr) == p3_zg.PASS3_OUTCOME_IMPROVED


def test_placement_stub_route_probe_path_first_cell_is_stub() -> None:
    stub = (1, 0)
    anchor = (5, 0)
    mineable = {(x, y) for x in range(1, 8) for y in range(0, 3)}
    asteroid = set(mineable)
    tc = {
        stub: "belt",
        (2, 0): "belt",
        (3, 0): "belt",
        (4, 0): "belt",
        (5, 0): "belt",
    }
    buildings = {c: "occupied" for c in mineable if c not in tc}
    path = placement_stub_route_probe_path(
        outlet_stub=stub,
        anchor=anchor,
        asteroid_cells=asteroid,
        mineable_cells=mineable,
        buildings=buildings,
        transport_cells=tc,
        fixed_stubs=frozenset({stub}),
    )
    assert path is not None
    assert path[0] == stub


def test_internal_transport_above_baseline_is_optimization_warning_not_solver_failure() -> None:
    tier = _compute_solver_quality_tier(
        layout_hard_valid=True,
        solver_termination=SOLVER_TERMINATION_SUCCESS,
        optimization_warnings=[OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_ABOVE_PASS2_BASELINE],
        extractor_drop_count=0,
        preserve_source_loss_before_step4=0,
    )
    assert tier == SOLVER_QUALITY_TIER_SUCCESS_VALID_WITH_OPTIMIZATION_WARNING
    assert tier != SOLVER_QUALITY_TIER_SOLVER_FAILURE


def test_atomic_ratio_telemetry_uses_dto_baseline_length() -> None:
    dto = P3E3GuardedCommitCandidate(
        attempted=True,
        candidate_transport_cells=frozenset(),
        removed_transport_cells=frozenset(),
        added_transport_cells=frozenset(),
        preserved_stub_cells=frozenset({(0, 0)}),
        touched_hard_protected_cells=frozenset(),
        touched_soft_protected_cells=frozenset(),
        replacement_route_cells=frozenset(),
        baseline_route_length=10,
        candidate_route_length=25,
        route_length_ratio=None,
        precheck_passed=True,
        rejected_reason="rejected_by_route_length_ratio",
        hard_protected_corridors=frozenset(),
    )
    tr = _p3e3_atomic_trace_from_dto(
        dto,
        atomic_candidate_built=True,
        validation_passed=False,
        would_accept=False,
        atomic_rejected="rejected_by_route_length_ratio",
        route_length_ratio_cap=2.0,
    )
    assert tr.get("p3e3_route_allowed_max_length") == 20


def test_enrich_marks_improved_when_internal_saved_positive() -> None:
    tr = {
        "pass3_skipped": False,
        "pass3_internal_transport_saved": 3,
        "p3e2_outlet_count": 1,
        "pass3_transport_kind": "belt",
        "pass3_routing_job_count": 1,
    }
    p3_zg.enrich_pass3_trace_zero_gain_telemetry(tr)
    assert tr["pass3_zero_gain_outcome"] == p3_zg.PASS3_OUTCOME_IMPROVED


def test_greedy_local_reroute_reduces_internal_transport_count() -> None:
    """Greedy local reroute drops internal transport when a same-kind detour restores link."""

    def is_ext_y_ne_0(c: tuple[int, int]) -> bool:
        return c[1] != 0

    mineable = {(x, y) for x in range(1, 8) for y in range(0, 3)}
    asteroid = set(mineable)
    tc = {
        (1, 0): "belt",
        (2, 0): "belt",
        (3, 0): "belt",
        (4, 0): "belt",
        (5, 0): "belt",
    }
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_greedy_core."
        "PASS3_GREEDY_LOCAL_REPLACEMENT_ENABLED",
        True,
    ):
        res = reconstruct_mining_priority_transport(
            anchor=(5, 0),
            asteroid_cells=asteroid,
            mineable_cells=mineable,
            buildings={},
            transport_cells=dict(tc),
            outlets_order=[(1, 0)],
            transport_role="shape_belt",
            is_external=is_ext_y_ne_0,
        )
    bi = count_internal_transport_cells(tc.keys(), is_external=is_ext_y_ne_0)
    ai = count_internal_transport_cells(res.transport_cells.keys(), is_external=is_ext_y_ne_0)
    assert res.committed is True
    assert ai < bi
