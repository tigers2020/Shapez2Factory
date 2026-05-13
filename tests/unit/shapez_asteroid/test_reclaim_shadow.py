"""P4-A reclaim shadow: mineable_cur, exclusions, budget/gain trace (no commits).

gain_ratio (§12.2): ``RECLAIM_SHADOW_MINER_EXTENSION_GAIN_SLOTS`` divided by
``additional_route_cost`` (RouteZone path sum). ``DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD`` is
empirical, not a strict dimensionless physical ratio; see ``documents/Algorithm/
Shapez2 Asteroid Mining Solver logic.md`` §12.2 (v5.10).
"""

from __future__ import annotations

import copy
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    CORRIDOR_REPLACEMENT_BUDGET_KEYS_SOFT_REPLACE,
    P4_RECLAIM_ZERO_ALL_TRANSPORT_PROTECTED,
    P4_RECLAIM_ZERO_NO_RECLAIMED_CELLS,
    RECLAIM_CONTINUITY_BONUS_MAX,
    RECLAIM_CONTINUITY_DECAY,
    RECLAIM_CONTINUITY_IDEAL_DISTANCE,
    RECLAIM_CONTINUITY_MULTI_WINDOW_ENABLED,
    RECLAIM_CONTINUITY_WINDOW,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow import (
    DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD,
    MAX_RECLAIM_ITERATIONS,
    MAX_RECLAIM_SHADOW_SCAN_LIMIT,
    P4_RECLAIM_CORRIDOR_SOURCE_EMPTY,
    P4_RECLAIM_CORRIDOR_SOURCE_SOLVER_POOL,
    P4_REJECT_FINAL_ROUTE_OVERLAP,
    P4_REJECT_GAIN_RATIO,
    P4_REJECT_HARD_PROTECTED_CORRIDOR,
    P4_REJECT_INTERNAL_TRANSPORT_BUDGET,
    P4_REJECT_NO_INCREMENTAL_ROUTE,
    P4_REJECT_NO_SHADOW_CANDIDATE,
    P4_REJECT_SOFT_PROTECTED_CORRIDOR,
    P4_ROLLBACK_AFTER_INCREMENTAL_ROUTE_FAILED,
    P4_ROLLBACK_AFTER_PROVISIONAL_VALIDATION_FAILURE,
    P4_SOFT_REPLACE_REJECT_NO_REPLACEMENT_ROUTE,
    P4_SOFT_REPLACE_REJECT_OLD_NOT_SOFT_PROTECTED,
    P4_SOFT_REPLACE_REJECT_REPLACEMENT_NOT_CONNECTED,
    P4_SOFT_REPLACE_REJECT_VALIDATION,
    P4_SOFT_REPLACE_V1_CONTRACT,
    P4_SOFT_REPLACE_V2_CONTRACT,
    ReclaimShadowScanResult,
    _evaluate_one_shadow_bundle,
    _mineable_cur_for_reclaim,
    _p4_bundle_eval,
    _reclaimed_interior_transport_cells,
    _try_atomic_replace_soft_corridor,
    p4_reclaim_provisional_commit_neutral_trace,
    protected_corridors_for_reclaim,
    reclaim_shadow_scan_core_after_pass3,
    run_p4_reclaim_loop_after_pass3,
    run_p4_reclaim_provisional_commit_after_pass3,
    run_reclaim_shadow_scan_after_pass3,
    select_best_accepted_p4_bundle,
    solver_routing_state_for_p4_reclaim,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow_scan import (  # noqa: E501
    _p4_bucketed_anchor_lists_for_scan,
    _p4_min_manhattan_to_priors,
    _p4_reclaim_zero_candidate_diag,
    _p4_scan_distance_bucket_name,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow_scan_eval import (  # noqa: E501
    _p4_reclaim_diversity_fields,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.recovery_context import (
    RECOVERY_SEGMENT_P4_RECLAIM,
    RECOVERY_SEGMENT_SOFT_REPLACE_V2,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
    build_solver_timeline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_state_hash import (
    mining_map_state_hash,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    FinalValidationReport,
    cells_dict_from_mining_map,
)

_P4_SCAN_EVAL_ROUTE_COST_DETAIL = (
    "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim."
    "reclaim_shadow_scan_eval._path_additional_route_cost_detail"
)


def _never_external(_c: tuple[int, int]) -> bool:
    return False


def _external_east(c: tuple[int, int]) -> bool:
    return c[0] >= 20


def _base_final_mining_map() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for x in range(1, 22):
        for y in range(0, 8):
            rows.append({"x": x, "y": y, "role": "inferred"})
    return rows


def _minimal_routed_shape_map(*, include_orphan_belt_at_8_4: bool) -> list[dict[str, object]]:
    """Post-step4-like map: one shape miner, belt trunk to east-facing external."""

    rows = _base_final_mining_map()
    extra: list[dict[str, object]] = [
        {
            "x": 10,
            "y": 2,
            "role": "occupied",
            "layout_kind": "miner",
            "surface": "shape",
            "r": 0,
            "placement_id": "p4a-test",
        },
    ]
    for x in range(11, 20):
        extra.append({"x": x, "y": 2, "role": "belt"})
    if include_orphan_belt_at_8_4:
        extra.append({"x": 8, "y": 4, "role": "belt"})
    return rows + extra


def test_mineable_cur_excludes_final_route_hard_soft_committed() -> None:
    mineable = frozenset({(1, 1), (2, 1), (3, 1), (4, 1)})
    final_route = frozenset({(2, 1)})
    hard = frozenset({(3, 1)})
    soft = frozenset({(1, 1)})
    committed = frozenset({(5, 5)})
    cur = _mineable_cur_for_reclaim(
        mineable,
        final_route_cells=final_route,
        hard_protected_corridors=hard,
        soft_protected_corridors=soft,
        committed_building_cells=committed,
    )
    assert cur == frozenset({(4, 1)})


def test_reclaimed_interior_transport_is_before_minus_after() -> None:
    before = _minimal_routed_shape_map(include_orphan_belt_at_8_4=True)
    after = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    r = _reclaimed_interior_transport_cells(before, after, is_external=_never_external)
    assert r == frozenset({(8, 4)})


def test_reclaimed_interior_transport_excludes_external_belt() -> None:
    """Belt cells classified external are not interior, so removal does not count as reclaimed."""

    before = _minimal_routed_shape_map(include_orphan_belt_at_8_4=True)
    after = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)

    def _external_only_8_4(c: tuple[int, int]) -> bool:
        return c == (8, 4)

    r = _reclaimed_interior_transport_cells(before, after, is_external=_external_only_8_4)
    assert r == frozenset()


def test_p4_zero_candidates_when_no_interior_reclaim_and_maps_match() -> None:
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    trace = run_reclaim_shadow_scan_after_pass3(
        m,
        m,
        final_mining_map=_base_final_mining_map(),
        is_external=_never_external,
        pass3_trace={"pass3_internal_transport_saved": 10},
    )
    assert trace["p4_reclaim_shadow_enabled"] is True
    assert trace["p4_reclaim_candidate_count"] == 0
    assert trace["p4_reclaim_accepted_shadow_count"] == 0
    assert trace["p4_reclaim_rejected_shadow_count"] == 0
    assert trace["p4_reclaim_best_candidate"] is None
    pre = trace.get("p4_reclaim_scan_preconditions")
    assert isinstance(pre, dict)
    assert pre["routing_jobs_count"] >= 1
    assert pre["reclaim_anchor_candidate_count"] == 0
    assert trace.get("p4_reclaim_entry_mining_map_state_hash") is not None
    assert P4_RECLAIM_ZERO_NO_RECLAIMED_CELLS in trace.get("p4_reclaim_zero_candidate_reasons", [])
    assert trace.get("mineable_base_count", 0) > 0
    assert isinstance(trace.get("reclaim_anchor_failure_samples"), list)


def test_p4_zero_candidate_diag_all_transport_protected_reason() -> None:
    """All belt/pipe cells are in hard|soft protected → all_transport_protected in diagnostics."""

    d = _p4_reclaim_zero_candidate_diag(
        mineable_base=frozenset({(1, 1)}),
        mineable_cur=frozenset({(1, 1)}),
        final_route_cells=frozenset(),
        hard=frozenset({(10, 10)}),
        soft=frozenset({(11, 11)}),
        committed=frozenset(),
        reclaimed=frozenset(),
        reclaim_anchor_cells=set(),
        transport_cells=frozenset({(10, 10), (11, 11)}),
        internal_budget=5,
        spent_prior=0,
        anchor_specs_empty_all=False,
        has_routing_jobs=True,
    )
    assert P4_RECLAIM_ZERO_ALL_TRANSPORT_PROTECTED in d["p4_reclaim_zero_candidate_reasons"]
    assert d["p4_reclaim_unprotected_transport_count"] == 0
    assert P4_RECLAIM_ZERO_NO_RECLAIMED_CELLS in d["p4_reclaim_zero_candidate_reasons"]


def test_p4_scan_preconditions_no_routing_jobs_includes_zero_routing_count() -> None:
    base = _base_final_mining_map()
    trace = run_reclaim_shadow_scan_after_pass3(
        base,
        base,
        final_mining_map=base,
        is_external=_never_external,
        pass3_trace={"pass3_internal_transport_saved": 0},
    )
    assert trace.get("p4_reclaim_shadow_skip_reason") == "no_routing_jobs"
    pre = trace["p4_reclaim_scan_preconditions"]
    assert pre["routing_jobs_count"] == 0
    assert trace.get("p4_reclaim_zero_candidate_reasons") == []
    assert trace.get("mineable_base_count") is not None


def test_reclaim_continuity_multi_window_disabled_uses_single_anchor_tail() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow_commit_loop import (  # noqa: E501
        _p4_recent_reclaim_window_newest_first,
    )

    assert RECLAIM_CONTINUITY_MULTI_WINDOW_ENABLED is False
    assert RECLAIM_CONTINUITY_WINDOW > 1
    acc = [[10, 2], [11, 2], [12, 2], [13, 2]]
    w1 = _p4_recent_reclaim_window_newest_first(acc, max_window=1)
    w_full = _p4_recent_reclaim_window_newest_first(acc, max_window=RECLAIM_CONTINUITY_WINDOW)
    assert w1 is not None and len(w1) == 1
    assert w_full is not None and len(w_full) == RECLAIM_CONTINUITY_WINDOW


def test_p4_scan_entry_baseline_matches_when_compare_enabled() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_timeline import (  # noqa: E501
        _internal_transport_count_for_pass3_kind,
    )

    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    bl = _internal_transport_count_for_pass3_kind(m, is_external=_external_east)
    if bl is None:
        pytest.skip("fixture has no single-kind internal transport baseline")
    r = reclaim_shadow_scan_core_after_pass3(
        m,
        m,
        final_mining_map=_base_final_mining_map(),
        is_external=_external_east,
        pass3_trace={"pass3_internal_transport_saved": 100},
        p4_baseline_internal_transport_at_reclaim_entry=bl,
        p4_compare_baseline_internal_to_scan_entry=True,
    )
    if r.trace.get("p4_reclaim_shadow_skip_reason"):
        pytest.skip(str(r.trace.get("p4_reclaim_shadow_skip_reason")))
    assert r.trace.get("p4_reclaim_scan_entry_baseline_mismatch") is False
    assert r.trace.get("p4_reclaim_internal_transport_at_scan_entry") == bl


def test_p4_rejects_stub_in_soft_protected_corridor() -> None:
    mineable = frozenset({(x, y) for x in range(1, 22) for y in range(0, 8)})
    asteroid = frozenset(mineable)
    # Omit (11,2) so overlap is classified as soft corridor, not final-route belt.
    final_route = frozenset({(12, 2), (13, 2)})
    hard = frozenset()
    soft = frozenset({(11, 2)})
    committed = frozenset()
    mineable_cur = _mineable_cur_for_reclaim(
        mineable,
        final_route_cells=final_route,
        hard_protected_corridors=hard,
        soft_protected_corridors=soft,
        committed_building_cells=committed,
    )
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    ev = _evaluate_one_shadow_bundle(
        anchor=(10, 2),
        extension=(9, 2),
        rotation=0,
        map_after_pass3=m,
        mineable=mineable,
        asteroid=asteroid,
        mineable_cur=mineable_cur,
        final_route_cells=final_route,
        hard_protected_corridors=hard,
        soft_protected_corridors=soft,
        want_role="belt",
        is_external=_external_east,
        outlets_order=[(11, 2)],
        internal_budget=50,
        pass3_raw_saved=100,
        gain_slots=2.0,
        gain_ratio_threshold=DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD,
    )
    assert ev.rejected_reason == P4_REJECT_SOFT_PROTECTED_CORRIDOR


def test_p4_rejects_anchor_in_hard_protected() -> None:
    mineable = frozenset({(x, y) for x in range(1, 22) for y in range(0, 8)})
    asteroid = frozenset(mineable)
    final_route = frozenset({(11, 2), (12, 2)})
    hard = frozenset({(8, 4)})
    soft = frozenset()
    # Canonical mineable_cur would exclude (8,4); include it to exercise hard-strike logic.
    mineable_cur = frozenset({(8, 4), (7, 4)})
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    ev = _evaluate_one_shadow_bundle(
        anchor=(8, 4),
        extension=(7, 4),
        rotation=0,
        map_after_pass3=m,
        mineable=mineable,
        asteroid=asteroid,
        mineable_cur=mineable_cur,
        final_route_cells=final_route,
        hard_protected_corridors=hard,
        soft_protected_corridors=soft,
        want_role="belt",
        is_external=_external_east,
        outlets_order=[(11, 2)],
        internal_budget=50,
        pass3_raw_saved=100,
        gain_slots=2.0,
        gain_ratio_threshold=DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD,
    )
    assert ev.rejected_reason == P4_REJECT_HARD_PROTECTED_CORRIDOR


def test_p4_rejects_gain_ratio_below_threshold_via_path_cost_patch() -> None:
    mineable = frozenset({(x, y) for x in range(1, 22) for y in range(0, 8)})
    asteroid = frozenset(mineable)
    final_route = frozenset({(11, 2), (12, 2)})
    mineable_cur = _mineable_cur_for_reclaim(
        mineable,
        final_route_cells=final_route,
        hard_protected_corridors=frozenset(),
        soft_protected_corridors=frozenset(),
        committed_building_cells=frozenset({(10, 2)}),
    )
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    stub = (11, 4)  # (10,4) r=0
    path = [stub, (12, 4), (19, 2)]
    with (
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "placement_stub_route_probe_path",
            return_value=path,
        ),
        patch(_P4_SCAN_EVAL_ROUTE_COST_DETAIL, return_value=(10, 10, 0)),
    ):
        ev = _evaluate_one_shadow_bundle(
            anchor=(10, 4),
            extension=(10, 3),
            rotation=0,
            map_after_pass3=m,
            mineable=mineable,
            asteroid=asteroid,
            mineable_cur=mineable_cur,
            final_route_cells=final_route,
            hard_protected_corridors=frozenset(),
            soft_protected_corridors=frozenset(),
            want_role="belt",
            is_external=_external_east,
            outlets_order=[(11, 2)],
            internal_budget=50,
            pass3_raw_saved=100,
            gain_slots=2.0,
            gain_ratio_threshold=DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD,
        )
    assert ev.rejected_reason == P4_REJECT_GAIN_RATIO
    assert ev.gain_ratio == 0.2


def test_p4_rejects_internal_transport_budget() -> None:
    mineable = frozenset({(x, y) for x in range(1, 22) for y in range(0, 8)})
    asteroid = frozenset(mineable)
    final_route = frozenset({(11, 2), (12, 2)})
    mineable_cur = _mineable_cur_for_reclaim(
        mineable,
        final_route_cells=final_route,
        hard_protected_corridors=frozenset(),
        soft_protected_corridors=frozenset(),
        committed_building_cells=frozenset({(10, 2)}),
    )
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    stub = (11, 4)
    path = [stub, (12, 4), (19, 2)]
    with (
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "placement_stub_route_probe_path",
            return_value=path,
        ),
        patch(_P4_SCAN_EVAL_ROUTE_COST_DETAIL, return_value=(1, 1, 0)),
    ):
        ev = _evaluate_one_shadow_bundle(
            anchor=(10, 4),
            extension=(10, 3),
            rotation=0,
            map_after_pass3=m,
            mineable=mineable,
            asteroid=asteroid,
            mineable_cur=mineable_cur,
            final_route_cells=final_route,
            hard_protected_corridors=frozenset(),
            soft_protected_corridors=frozenset(),
            want_role="belt",
            is_external=_external_east,
            outlets_order=[(11, 2)],
            internal_budget=0,
            pass3_raw_saved=100,
            gain_slots=2.0,
            gain_ratio_threshold=DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD,
        )
    assert ev.rejected_reason == P4_REJECT_INTERNAL_TRANSPORT_BUDGET


def test_p4_accepted_shadow_with_cheap_route_and_budget() -> None:
    mineable = frozenset({(x, y) for x in range(1, 22) for y in range(0, 8)})
    asteroid = frozenset(mineable)
    final_route = frozenset({(11, 2), (12, 2)})
    mineable_cur = _mineable_cur_for_reclaim(
        mineable,
        final_route_cells=final_route,
        hard_protected_corridors=frozenset(),
        soft_protected_corridors=frozenset(),
        committed_building_cells=frozenset({(10, 2)}),
    )
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    stub = (11, 4)
    path = [stub, (12, 4), (19, 2)]
    with (
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "placement_stub_route_probe_path",
            return_value=path,
        ),
        patch(_P4_SCAN_EVAL_ROUTE_COST_DETAIL, return_value=(1, 1, 0)),
    ):
        ev = _evaluate_one_shadow_bundle(
            anchor=(10, 4),
            extension=(10, 3),
            rotation=0,
            map_after_pass3=m,
            mineable=mineable,
            asteroid=asteroid,
            mineable_cur=mineable_cur,
            final_route_cells=final_route,
            hard_protected_corridors=frozenset(),
            soft_protected_corridors=frozenset(),
            want_role="belt",
            is_external=_external_east,
            outlets_order=[(11, 2)],
            internal_budget=5,
            pass3_raw_saved=100,
            gain_slots=2.0,
            gain_ratio_threshold=DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD,
        )
    assert ev.accepted_shadow is True
    assert ev.rejected_reason is None


def test_p4_scan_finds_accepted_bundle_on_reclaimed_cell_with_savings() -> None:
    before = _minimal_routed_shape_map(include_orphan_belt_at_8_4=True) + [
        {"x": x, "y": 6, "role": "belt"} for x in range(1, 20)
    ]
    after = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    stub = (11, 4)
    path = [stub, (12, 4), (19, 2)]
    with (
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "placement_stub_route_probe_path",
            return_value=path,
        ),
        patch(_P4_SCAN_EVAL_ROUTE_COST_DETAIL, return_value=(1, 1, 0)),
    ):
        trace = run_reclaim_shadow_scan_after_pass3(
            before,
            after,
            final_mining_map=_base_final_mining_map(),
            is_external=_external_east,
            pass3_trace={"pass3_internal_transport_saved": 100},
        )
    assert trace["p4_reclaim_candidate_count"] > 0
    assert trace["p4_reclaim_accepted_shadow_count"] >= 1
    assert trace["p4_reclaim_internal_transport_budget"] == 7
    bc = trace["p4_reclaim_best_candidate"]
    assert bc is not None
    assert bc.get("rejected_reason") is None
    assert "p4_diversity" in bc
    assert "cluster_penalty" in bc["p4_diversity"]
    assert "distance_bucket" in bc["p4_diversity"]
    assert "continuity_bonus" in bc["p4_diversity"]
    assert "final_diversity_score" in bc["p4_diversity"]
    assert "continuity_band_state" in bc["p4_diversity"]
    assert "continuity_winning_index" in bc["p4_diversity"]
    assert "continuity_window_size" in bc["p4_diversity"]
    assert "frontier_orbit_score" in bc["p4_diversity"]
    assert bc["p4_diversity"]["frontier_orbit_score"] == 0
    assert trace.get("p4_reclaim_frontier_orbit_streak_prior") == 0
    slot_order = trace["p4_reclaim_scan_slot_order"]
    assert len(slot_order) == trace["p4_reclaim_candidate_count"]
    assert slot_order[0]["slot_index"] == 0
    assert "rr_bucket_cycle" in slot_order[0]
    assert "distance_bucket" in slot_order[0]
    for row in slot_order:
        assert row["distance_bucket"] == "all"


def test_p4_scan_zero_accepted_when_spent_prior_exhausts_internal_budget() -> None:
    before = _minimal_routed_shape_map(include_orphan_belt_at_8_4=True) + [
        {"x": x, "y": 6, "role": "belt"} for x in range(1, 20)
    ]
    after = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    path = [(11, 4), (12, 4), (19, 2)]
    with (
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "placement_stub_route_probe_path",
            return_value=path,
        ),
        patch(_P4_SCAN_EVAL_ROUTE_COST_DETAIL, return_value=(1, 1, 0)),
    ):
        tr0 = run_reclaim_shadow_scan_after_pass3(
            before,
            after,
            final_mining_map=_base_final_mining_map(),
            is_external=_external_east,
            pass3_trace={"pass3_internal_transport_saved": 100},
        )
        tr1 = run_reclaim_shadow_scan_after_pass3(
            before,
            after,
            final_mining_map=_base_final_mining_map(),
            is_external=_external_east,
            pass3_trace={"pass3_internal_transport_saved": 100},
            reclaim_internal_transport_spent_prior=100,
        )
    assert tr0["p4_reclaim_accepted_shadow_count"] >= 1
    assert tr1["p4_reclaim_accepted_shadow_count"] == 0


def test_p4_evaluate_rejects_when_spent_prior_plus_incr_exceeds_internal_cap() -> None:
    mineable = frozenset({(x, y) for x in range(1, 22) for y in range(0, 8)})
    asteroid = frozenset(mineable)
    final_route = frozenset({(11, 2), (12, 2)})
    mineable_cur = _mineable_cur_for_reclaim(
        mineable,
        final_route_cells=final_route,
        hard_protected_corridors=frozenset(),
        soft_protected_corridors=frozenset(),
        committed_building_cells=frozenset({(10, 2)}),
    )
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    stub = (11, 4)
    path = [stub, (12, 4), (19, 2)]
    with (
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "placement_stub_route_probe_path",
            return_value=path,
        ),
        patch(_P4_SCAN_EVAL_ROUTE_COST_DETAIL, return_value=(1, 1, 0)),
    ):
        ev = _evaluate_one_shadow_bundle(
            anchor=(10, 4),
            extension=(10, 3),
            rotation=0,
            map_after_pass3=m,
            mineable=mineable,
            asteroid=asteroid,
            mineable_cur=mineable_cur,
            final_route_cells=final_route,
            hard_protected_corridors=frozenset(),
            soft_protected_corridors=frozenset(),
            want_role="belt",
            is_external=_external_east,
            outlets_order=[(11, 2)],
            internal_budget=35,
            pass3_raw_saved=100,
            spent_prior=99,
            gain_slots=2.0,
            gain_ratio_threshold=DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD,
        )
    assert ev.accepted_shadow is False
    assert ev.rejected_reason == P4_REJECT_INTERNAL_TRANSPORT_BUDGET


def test_build_solver_timeline_includes_p4_reclaim_loop_trace_when_p4_runs() -> None:
    from tests.unit.shapez_asteroid.test_pass1_timeline_integration import (
        _decoded_miners_with_belt_escape,
    )

    out = build_solver_timeline(_decoded_miners_with_belt_escape())
    ss = out["solver_summary"]
    if not ss.get("p4_reclaim_shadow_enabled"):
        return
    assert ss.get("p4_reclaim_loop_max_iterations") == 3
    assert ss.get("p4_reclaim_shadow_scan_limit") == 16
    assert isinstance(ss.get("p4_reclaim_loop_iterations_executed"), int)
    assert ss.get("p4_reclaim_loop_iterations_executed", 0) >= 1
    assert isinstance(ss.get("p4_reclaim_loop_successful_commits"), int)
    assert isinstance(ss.get("p4_reclaim_loop_internal_transport_cumulative_added"), int)
    assert ss.get("p4_reclaim_loop_terminated_reason") is not None


def test_p4_reclaim_loop_stops_at_max_reclaim_iterations() -> None:
    """§12.6: outer loop runs at most ``MAX_RECLAIM_ITERATIONS`` then ``max_iterations``."""

    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    m0 = copy.deepcopy(m)
    ev = _p4_bundle_eval(
        gain=2.0,
        additional_route_cost=1.0,
        gain_ratio=2.0,
        incremental_internal_transport_added=0,
        rejected_reason=None,
        accepted_shadow=True,
        anchor=(10, 4),
        extension=(10, 3),
        rotation=0,
    )
    trace_w = {**_fake_accepted_scan_trace()}

    def fake_scan(*_a: object, **_k: object) -> ReclaimShadowScanResult:
        return ReclaimShadowScanResult(trace=trace_w, evals=[ev], transport_kind="shape_belt")

    success = {
        "p4_reclaim_provisional_commit_attempted": True,
        "p4_reclaim_provisional_commit_committed": True,
        "p4_reclaim_provisional_commit_rollback_performed": False,
        "p4_reclaim_provisional_commit_rollback_reason": None,
        "p4_reclaim_selected_candidate": None,
        "p4_reclaim_selected_candidate_rank": 0,
        "p4_reclaim_added_extractor_cells": [],
        "p4_reclaim_added_extension_cells": [],
        "p4_reclaim_added_stub_cells": [],
        "p4_reclaim_provisional_commit_skip_reason": None,
        "p4_reclaim_incremental_route_attempted": True,
        "p4_reclaim_incremental_route_committed": True,
        "p4_reclaim_incremental_route_rollback_performed": False,
        "p4_reclaim_incremental_route_rollback_reason": None,
        "p4_reclaim_incremental_route_skip_reason": None,
        "p4_reclaim_incremental_route_path_cells": [[20, 1], [20, 2]],
        "p4_reclaim_incremental_route_cells_added": [[20, 2]],
        "p4_reclaim_incremental_route_b2_internal_transport_added": 1,
        "p4_reclaim_final_route_cells_added": [[20, 1], [20, 2]],
        "p4_reclaim_soft_protected_candidate_cells_added": [[20, 1], [20, 2]],
        "p4_reclaim_mineable_excluded_by_route_cells": 2,
    }

    def fake_commit(cur: list[dict], **_kw: object) -> tuple[list[dict], dict]:
        return cur, success

    with (
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "reclaim_shadow_scan_core_after_pass3",
            side_effect=fake_scan,
        ),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "run_p4_reclaim_provisional_commit_after_pass3",
            side_effect=fake_commit,
        ),
    ):
        _out_m, merged = run_p4_reclaim_loop_after_pass3(
            m0,
            m0,
            final_mining_map=_base_final_mining_map(),
            pass3_trace={"pass3_internal_transport_saved": 100},
            solver_routing_state=None,
            is_external=_external_east,
        )
    assert merged["p4_reclaim_loop_max_iterations"] == MAX_RECLAIM_ITERATIONS
    assert merged["p4_reclaim_shadow_scan_limit"] == MAX_RECLAIM_SHADOW_SCAN_LIMIT
    assert merged["p4_reclaim_loop_successful_commits"] == MAX_RECLAIM_ITERATIONS
    assert merged["p4_reclaim_loop_iterations_executed"] == MAX_RECLAIM_ITERATIONS
    assert merged["p4_reclaim_loop_terminated_reason"] == "max_iterations"
    assert merged["p4_reclaim_route_zone_excluded_cumulative_count"] == 2
    assert merged["p4_reclaim_last_commit_route_cells"] == [[20, 1], [20, 2]]
    assert merged["p4_reclaim_last_soft_protected_candidate_cells"] == [[20, 1], [20, 2]]


def _p4_soft_overlap_fail_commit_trace() -> dict[str, object]:
    """Synthetic provisional failure: soft corridor + belt collision cells for loop hook."""

    out = dict(
        p4_reclaim_provisional_commit_neutral_trace(
            attempted=True,
            rollback_performed=False,
            rollback_reason=P4_REJECT_SOFT_PROTECTED_CORRIDOR,
        )
    )
    out["p4_reclaim_soft_corridor_transport_collision_cells"] = [[14, 2]]
    out["p4_reclaim_selected_candidate"] = {
        "anchor": [10, 4],
        "extension": [10, 3],
        "rotation": 0,
        "gain": 2.0,
        "additional_route_cost": 1.0,
        "gain_ratio": 2.0,
        "incremental_internal_transport_added": 1,
    }
    out["p4_reclaim_selected_candidate_rank"] = 0
    return out


def _p4_loop_success_commit_trace() -> dict[str, object]:
    return {
        "p4_reclaim_provisional_commit_attempted": True,
        "p4_reclaim_provisional_commit_committed": True,
        "p4_reclaim_provisional_commit_rollback_performed": False,
        "p4_reclaim_provisional_commit_rollback_reason": None,
        "p4_reclaim_selected_candidate": None,
        "p4_reclaim_selected_candidate_rank": 0,
        "p4_reclaim_added_extractor_cells": [],
        "p4_reclaim_added_extension_cells": [],
        "p4_reclaim_added_stub_cells": [],
        "p4_reclaim_provisional_commit_skip_reason": None,
        "p4_reclaim_incremental_route_attempted": True,
        "p4_reclaim_incremental_route_committed": True,
        "p4_reclaim_incremental_route_rollback_performed": False,
        "p4_reclaim_incremental_route_rollback_reason": None,
        "p4_reclaim_incremental_route_skip_reason": None,
        "p4_reclaim_incremental_route_path_cells": [[20, 1], [20, 2]],
        "p4_reclaim_incremental_route_cells_added": [[20, 2]],
        "p4_reclaim_incremental_route_b2_internal_transport_added": 1,
        "p4_reclaim_final_route_cells_added": [[20, 1], [20, 2]],
        "p4_reclaim_soft_protected_candidate_cells_added": [[20, 1], [20, 2]],
        "p4_reclaim_mineable_excluded_by_route_cells": 2,
    }


def test_p4_loop_attempts_soft_replace_when_candidate_hits_soft_corridor() -> None:
    """P4 loop calls §14.3 atomic soft replace when provisional fails on soft + transport hit."""

    from unittest.mock import MagicMock

    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    m0 = copy.deepcopy(m)
    ev = _p4_bundle_eval(
        gain=2.0,
        additional_route_cost=1.0,
        gain_ratio=2.0,
        incremental_internal_transport_added=1,
        rejected_reason=None,
        accepted_shadow=True,
        anchor=(10, 4),
        extension=(10, 3),
        rotation=0,
    )
    trace_w = {**_fake_accepted_scan_trace()}
    trace_w["p4_reclaim_soft_protected_candidate_cells_added"] = [[14, 2]]

    def fake_scan(*_a: object, **_k: object) -> ReclaimShadowScanResult:
        return ReclaimShadowScanResult(trace=trace_w, evals=[ev], transport_kind="shape_belt")

    replace_mock = MagicMock(
        return_value=(
            None,
            {
                "p4_soft_replace_attempted": True,
                "p4_soft_replace_committed": False,
                "p4_soft_replace_rejected_reason": P4_SOFT_REPLACE_REJECT_NO_REPLACEMENT_ROUTE,
                "p4_soft_replace_old_cells": [[14, 2]],
                "p4_soft_replace_new_cells": [],
                "p4_soft_replace_connected": None,
            },
        )
    )

    def fake_commit(_cur: list[dict], **_kw: object) -> tuple[list[dict], dict]:
        return m0, _p4_soft_overlap_fail_commit_trace()

    with (
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "reclaim_shadow_scan_core_after_pass3",
            side_effect=fake_scan,
        ),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "run_p4_reclaim_provisional_commit_after_pass3",
            side_effect=fake_commit,
        ),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "_try_atomic_replace_soft_corridor",
            replace_mock,
        ),
    ):
        out_m, merged = run_p4_reclaim_loop_after_pass3(
            m0,
            m0,
            final_mining_map=_base_final_mining_map(),
            pass3_trace={"pass3_internal_transport_saved": 100},
            solver_routing_state=None,
            is_external=_external_east,
        )
    replace_mock.assert_called()
    assert replace_mock.call_count == MAX_RECLAIM_ITERATIONS
    call_kw = replace_mock.call_args.kwargs
    assert call_kw["old_soft_corridor_cells"] == [(14, 2)]
    assert P4_SOFT_REPLACE_V1_CONTRACT
    assert merged["p4_soft_replace_contract"] == P4_SOFT_REPLACE_V2_CONTRACT
    assert merged["p4_soft_replace_attempted"] is True
    assert merged["p4_soft_replace_attempt_count"] == MAX_RECLAIM_ITERATIONS
    assert merged["p4_soft_replace_commit_count"] == 0
    assert out_m is m0


def test_p4_loop_keeps_original_reject_when_soft_replace_fails() -> None:
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    m0 = copy.deepcopy(m)
    ev = _p4_bundle_eval(
        gain=2.0,
        additional_route_cost=1.0,
        gain_ratio=2.0,
        incremental_internal_transport_added=1,
        rejected_reason=None,
        accepted_shadow=True,
        anchor=(10, 4),
        extension=(10, 3),
        rotation=0,
    )

    def fake_scan(*_a: object, **_k: object) -> ReclaimShadowScanResult:
        return ReclaimShadowScanResult(
            trace=_fake_accepted_scan_trace(), evals=[ev], transport_kind="shape_belt"
        )

    def fake_commit(_cur: list[dict], **_kw: object) -> tuple[list[dict], dict]:
        return m0, _p4_soft_overlap_fail_commit_trace()

    with (
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "reclaim_shadow_scan_core_after_pass3",
            side_effect=fake_scan,
        ),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "run_p4_reclaim_provisional_commit_after_pass3",
            side_effect=fake_commit,
        ),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "_try_atomic_replace_soft_corridor",
            return_value=(
                None,
                {
                    "p4_soft_replace_attempted": True,
                    "p4_soft_replace_committed": False,
                    "p4_soft_replace_rejected_reason": P4_SOFT_REPLACE_REJECT_VALIDATION,
                    "p4_soft_replace_old_cells": [[14, 2]],
                    "p4_soft_replace_new_cells": [],
                    "p4_soft_replace_connected": None,
                },
            ),
        ),
    ):
        out_m, merged = run_p4_reclaim_loop_after_pass3(
            m0,
            m0,
            final_mining_map=_base_final_mining_map(),
            pass3_trace={"pass3_internal_transport_saved": 100},
            solver_routing_state=None,
            is_external=_external_east,
        )
    assert out_m is m0
    assert merged["p4_reclaim_loop_terminated_reason"] == "provisional_commit_failed_max_iterations"
    assert merged["p4_reclaim_provisional_commit_committed"] is False
    assert merged["p4_soft_replace_committed"] is False
    assert merged["p4_soft_replace_attempt_count"] == MAX_RECLAIM_ITERATIONS
    assert merged["p4_soft_replace_commit_count"] == 0


def test_p4_loop_commits_reclaim_after_successful_soft_replace() -> None:
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    m0 = copy.deepcopy(m)
    m_after_replace = copy.deepcopy(m0)
    m_after_replace.append(
        {"x": 99, "y": 99, "role": "inferred", "_p4_soft_replace_test_marker": True}
    )
    ev = _p4_bundle_eval(
        gain=2.0,
        additional_route_cost=1.0,
        gain_ratio=2.0,
        incremental_internal_transport_added=1,
        rejected_reason=None,
        accepted_shadow=True,
        anchor=(10, 4),
        extension=(10, 3),
        rotation=0,
    )
    trace_w = {**_fake_accepted_scan_trace()}

    def fake_scan(*_a: object, **_k: object) -> ReclaimShadowScanResult:
        return ReclaimShadowScanResult(trace=trace_w, evals=[ev], transport_kind="shape_belt")

    n_commit = {"v": 0}

    def fake_commit(cur: list[dict], **_kw: object) -> tuple[list[dict], dict]:
        n_commit["v"] += 1
        if n_commit["v"] == 1:
            assert cur is m0
            return m0, _p4_soft_overlap_fail_commit_trace()
        assert any(r.get("_p4_soft_replace_test_marker") for r in cur if isinstance(r, dict))
        m_done = copy.deepcopy(cur)
        return m_done, _p4_loop_success_commit_trace()

    soft_ok = {
        "p4_soft_replace_attempted": True,
        "p4_soft_replace_committed": True,
        "p4_soft_replace_rejected_reason": None,
        "p4_soft_replace_old_cells": [[14, 2]],
        "p4_soft_replace_new_cells": [[14, 3]],
        "p4_soft_replace_connected": True,
    }

    with (
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "reclaim_shadow_scan_core_after_pass3",
            side_effect=fake_scan,
        ),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "run_p4_reclaim_provisional_commit_after_pass3",
            side_effect=fake_commit,
        ),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "_try_atomic_replace_soft_corridor",
            return_value=(m_after_replace, soft_ok),
        ),
    ):
        out_m, merged = run_p4_reclaim_loop_after_pass3(
            m0,
            m0,
            final_mining_map=_base_final_mining_map(),
            pass3_trace={"pass3_internal_transport_saved": 100},
            solver_routing_state=None,
            is_external=_external_east,
            max_loop_iterations=2,
        )
    assert n_commit["v"] == 2
    assert merged["p4_reclaim_loop_successful_commits"] == 1
    assert merged["p4_reclaim_provisional_commit_committed"] is True
    assert merged["p4_soft_replace_committed"] is True
    assert merged["p4_soft_replace_attempt_count"] == 1
    assert merged["p4_soft_replace_commit_count"] == 1
    assert out_m is not m0
    assert merged["recovery_context_chain"] == [
        RECOVERY_SEGMENT_P4_RECLAIM,
        RECOVERY_SEGMENT_SOFT_REPLACE_V2,
    ]


def test_recovery_context_chain_preserved_through_soft_replace() -> None:
    """§13: ``p4_reclaim`` remains first; ``soft_replace_v2`` appends after atomic commit."""

    test_p4_loop_commits_reclaim_after_successful_soft_replace()


def test_p4_reclaim_shadow_scan_limit_is_separate_from_loop_limit() -> None:
    """Per-scan bundle cap (16) is independent of commit-loop cap (3)."""

    assert MAX_RECLAIM_ITERATIONS != MAX_RECLAIM_SHADOW_SCAN_LIMIT
    assert MAX_RECLAIM_ITERATIONS == 3
    assert MAX_RECLAIM_SHADOW_SCAN_LIMIT == 16
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    tr = run_reclaim_shadow_scan_after_pass3(
        m,
        m,
        final_mining_map=_base_final_mining_map(),
        is_external=_external_east,
        pass3_trace={"pass3_internal_transport_saved": 100},
    )
    if tr.get("p4_reclaim_shadow_skip_reason"):
        pytest.skip(f"shadow scan skipped: {tr.get('p4_reclaim_shadow_skip_reason')}")
    assert tr.get("p4_reclaim_shadow_scan_limit") == MAX_RECLAIM_SHADOW_SCAN_LIMIT
    cc = tr.get("p4_reclaim_candidate_count")
    assert cc is not None
    assert int(cc) <= MAX_RECLAIM_SHADOW_SCAN_LIMIT


def test_p4_reclaim_committed_route_cells_are_excluded_from_next_scan() -> None:
    """§12.3: prior P4 route zone merges into final_route; mineable exclusion count rises."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow import (
        _all_transport_cells,
        _mineable_and_asteroid_coords,
    )

    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    final_map = _base_final_mining_map()
    mineable, _asteroid = _mineable_and_asteroid_coords(final_map)
    block = (15, 5)
    assert block in mineable
    assert block not in _all_transport_cells(m)
    r0 = reclaim_shadow_scan_core_after_pass3(
        m,
        m,
        final_mining_map=final_map,
        is_external=_external_east,
        pass3_trace={"pass3_internal_transport_saved": 100},
    )
    if r0.trace.get("p4_reclaim_shadow_skip_reason"):
        pytest.skip(str(r0.trace.get("p4_reclaim_shadow_skip_reason")))
    r1 = reclaim_shadow_scan_core_after_pass3(
        m,
        m,
        final_mining_map=final_map,
        is_external=_external_east,
        pass3_trace={"pass3_internal_transport_saved": 100},
        p4_committed_route_cells_for_zone=frozenset({block}),
    )
    assert (
        r1.trace["p4_reclaim_mineable_excluded_by_route_cells"]
        == r0.trace["p4_reclaim_mineable_excluded_by_route_cells"] + 1
    )
    assert r1.trace["p4_reclaim_route_zone_rebuilt"] is True


def test_p4_reclaim_trace_records_zone_rebuild_after_commit() -> None:
    """§12.3: B2 incremental commit trace lists final route / soft cells and rebuild flag."""

    scan = ReclaimShadowScanResult(
        trace=_fake_accepted_scan_trace(),
        evals=[_accepted_eval_at_10_4()],
        transport_kind="shape_belt",
    )
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    stub = (11, 4)
    path = [stub, (12, 4), (19, 2)]
    ok = FinalValidationReport(
        geometry_valid=True,
        connectivity_valid=True,
        disconnected_stub_count=0,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=0,
        overlap_violation_count=0,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
    )
    with (
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "validate_final_mining_layout",
            return_value=ok,
        ),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "placement_stub_route_probe_path",
            return_value=path,
        ),
    ):
        _out_m, tr = run_p4_reclaim_provisional_commit_after_pass3(
            m,
            final_mining_map=_base_final_mining_map(),
            pass3_trace={"pass3_internal_transport_saved": 10},
            solver_routing_state=None,
            scan_result=scan,
            is_external=_external_east,
        )
    assert tr.get("p4_reclaim_route_zone_rebuilt") is True
    assert tr.get("p4_reclaim_final_route_cells_added") == [[11, 4], [12, 4], [19, 2]]
    assert tr.get("p4_reclaim_soft_protected_candidate_cells_added") == [[11, 4], [12, 4], [19, 2]]
    assert tr.get("p4_reclaim_mineable_excluded_by_route_cells") == 3


def test_p4_rejects_stub_on_final_route_overlap() -> None:
    mineable = frozenset({(x, y) for x in range(1, 22) for y in range(0, 8)})
    asteroid = frozenset(mineable)
    final_route = frozenset({(11, 2), (12, 2), (10, 3)})
    mineable_cur = _mineable_cur_for_reclaim(
        mineable,
        final_route_cells=final_route,
        hard_protected_corridors=frozenset(),
        soft_protected_corridors=frozenset(),
        committed_building_cells=frozenset({(10, 2)}),
    )
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    # r=3 → stub (10,3), declared occupied by final_route
    ev = _evaluate_one_shadow_bundle(
        anchor=(10, 4),
        extension=(10, 5),
        rotation=3,
        map_after_pass3=m,
        mineable=mineable,
        asteroid=asteroid,
        mineable_cur=mineable_cur,
        final_route_cells=final_route,
        hard_protected_corridors=frozenset(),
        soft_protected_corridors=frozenset(),
        want_role="belt",
        is_external=_external_east,
        outlets_order=[(11, 2)],
        internal_budget=50,
        pass3_raw_saved=100,
        gain_slots=2.0,
        gain_ratio_threshold=DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD,
    )
    assert ev.rejected_reason == P4_REJECT_FINAL_ROUTE_OVERLAP


def test_solver_summary_p4_placeholder_when_pass3_skipped() -> None:
    from tests.unit.shapez_asteroid.test_pass1_timeline_integration import (
        _decoded_miners_with_belt_escape,
    )

    decoded = _decoded_miners_with_belt_escape()
    with (
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service."
            "run_pass3_transport_minimization_from_maps",
            side_effect=lambda mm, **kw: (
                mm,
                None,
                {
                    "pass3_skipped": True,
                    "pass3_skip_reason": "unit_test_skip",
                    "pass3_internal_transport_saved": 0,
                },
            ),
        ),
    ):
        out = build_solver_timeline(decoded)
    ss = out["solver_summary"]
    assert ss.get("p4_reclaim_shadow_enabled") is False
    assert ss.get("p4_reclaim_shadow_skip_reason") == "unit_test_skip"


def test_protected_corridors_solver_pool_wins_over_p3e3_touched() -> None:
    pcs = protected_corridors_for_reclaim(
        pass3_trace={
            "p3e3_guarded_commit_candidate": {
                "touched_hard_protected_cells": [[3, 3]],
                "touched_soft_protected_cells": [],
            },
        },
        solver_routing_state={
            "hard_protected_corridors": [[7, 7]],
            "soft_protected_corridors": [[8, 8]],
        },
    )
    assert pcs.source == P4_RECLAIM_CORRIDOR_SOURCE_SOLVER_POOL
    assert pcs.hard == frozenset({(7, 7)})
    assert pcs.soft == frozenset({(8, 8)})
    assert pcs.existing_layout_hints_cells == frozenset()


def test_protected_corridors_existing_layout_hints_are_ignored_for_runtime_dto() -> None:
    """ELA solver_hints are replay/UI context only — reclaim DTO must not attach them."""

    hints = {
        "trunk_seed_cell_union": [[21, 1]],
        "cleanup_candidate_cell_union": [[22, 1]],
    }
    pcs = protected_corridors_for_reclaim(
        pass3_trace={},
        solver_routing_state=None,
        existing_layout_solver_hints=hints,
    )
    assert pcs.source == P4_RECLAIM_CORRIDOR_SOURCE_EMPTY
    assert pcs.hard == frozenset()
    assert pcs.soft == frozenset()
    assert pcs.existing_layout_hints_cells == frozenset()


def test_protected_corridors_hard_pool_ignores_existing_layout_hint_overlap() -> None:
    pcs = protected_corridors_for_reclaim(
        pass3_trace={},
        solver_routing_state={"hard_protected_corridors": [[5, 5]], "soft_protected_corridors": []},
        existing_layout_solver_hints={
            "trunk_seed_cell_union": [[5, 5]],
            "cleanup_candidate_cell_union": [[6, 6]],
        },
    )
    assert pcs.hard == frozenset({(5, 5)})
    assert (5, 5) not in pcs.soft
    assert (6, 6) not in pcs.soft
    assert pcs.existing_layout_hints_cells == frozenset()


def test_protected_corridors_empty_solver_hints_no_regression() -> None:
    base = protected_corridors_for_reclaim(
        pass3_trace={},
        solver_routing_state={"soft_protected_corridors": [[3, 3]]},
    )
    merged = protected_corridors_for_reclaim(
        pass3_trace={},
        solver_routing_state={"soft_protected_corridors": [[3, 3]]},
        existing_layout_solver_hints={},
    )
    assert base == merged


def test_run_reclaim_shadow_trace_reports_zero_hint_cells_when_hints_not_runtime_authority() -> (
    None
):
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    trace = run_reclaim_shadow_scan_after_pass3(
        m,
        m,
        final_mining_map=_base_final_mining_map(),
        is_external=_never_external,
        pass3_trace={
            "pass3_internal_transport_saved": 0,
            "protected_corridors": {"hard": [[15, 2]], "soft": []},
        },
        existing_layout_solver_hints={
            "trunk_seed_cell_union": [[99, 99]],
            "cleanup_candidate_cell_union": [[0, 1]],
        },
    )
    assert trace.get("p4_reclaim_existing_layout_hint_cell_count") == 0


def test_solver_routing_state_for_p4_reclaim_prefers_routing_state_over_trunk() -> None:
    ns = SimpleNamespace(
        routing_state={"hard_protected_corridors": [[40, 1]]},
        trunk_load={"hard_protected_corridors": [[1, 1]], "soft_protected_corridors": []},
    )
    assert solver_routing_state_for_p4_reclaim(ns) == {"hard_protected_corridors": [[40, 1]]}


def test_solver_routing_state_ignores_trunk_when_routing_state_corridors_empty() -> None:
    ns = SimpleNamespace(
        routing_state={
            "source": "step4_committed_routes",
            "hard_protected_corridors": [],
            "soft_protected_corridors": [],
            "protected_corridors": {"hard": [], "soft": []},
        },
        trunk_load={"hard_protected_corridors": [[7, 7]], "soft_protected_corridors": [[8, 8]]},
    )
    merged = solver_routing_state_for_p4_reclaim(ns)
    assert merged == {
        "source": "step4_committed_routes",
        "hard_protected_corridors": [],
        "soft_protected_corridors": [],
        "protected_corridors": {"hard": [], "soft": []},
    }


def test_solver_routing_state_for_p4_reclaim_without_trunk_load() -> None:
    ns = SimpleNamespace(
        routing_state={"protected_corridors": {"hard": [[5, 5]], "soft": []}},
        trunk_load=None,
    )
    assert solver_routing_state_for_p4_reclaim(ns) == {
        "protected_corridors": {"hard": [[5, 5]], "soft": []},
    }


def test_solver_routing_state_for_p4_reclaim_empty_when_no_routing_state() -> None:
    ns = SimpleNamespace(
        routing_state=None,
        trunk_load={"hard_protected_corridors": [[2, 2]]},
    )
    assert solver_routing_state_for_p4_reclaim(ns) is None


def test_protected_corridors_flattens_nested_routing_state() -> None:
    pcs = protected_corridors_for_reclaim(
        pass3_trace={},
        solver_routing_state={"routing_state": {"hard_protected_corridors": [[6, 6]]}},
    )
    assert pcs.source == P4_RECLAIM_CORRIDOR_SOURCE_SOLVER_POOL
    assert pcs.hard == frozenset({(6, 6)})


def test_p4_reclaim_trace_solver_pool_without_trunk_load() -> None:
    ns = SimpleNamespace(
        routing_state={"hard_protected_corridors": [[14, 2]], "soft_protected_corridors": []},
        trunk_load=None,
    )
    merged = solver_routing_state_for_p4_reclaim(ns)
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    trace = run_reclaim_shadow_scan_after_pass3(
        m,
        m,
        final_mining_map=_base_final_mining_map(),
        is_external=_never_external,
        pass3_trace={"pass3_internal_transport_saved": 0},
        solver_routing_state=merged,
    )
    assert (
        trace.get("p4_reclaim_protected_corridor_source") == P4_RECLAIM_CORRIDOR_SOURCE_SOLVER_POOL
    )
    assert trace.get("p4_reclaim_hard_protected_count") == 1
    assert trace.get("p4_reclaim_soft_protected_count") == 0


def test_p4_reclaim_receives_step4_protected_corridor_pool() -> None:
    step4_result = SimpleNamespace(
        routing_state={
            "source": "step4_committed_routes",
            "protected_corridors": {"hard": [[11, 2]], "soft": [[12, 2], [13, 2]]},
            "hard_protected_corridors": [[99, 99]],
            "soft_protected_corridors": [],
        },
        trunk_load={"protected_corridors": {"hard": [[1, 1]], "soft": [[2, 2]]}},
    )

    solver_pool = solver_routing_state_for_p4_reclaim(step4_result)
    pcs = protected_corridors_for_reclaim(pass3_trace={}, solver_routing_state=solver_pool)

    assert pcs.source == P4_RECLAIM_CORRIDOR_SOURCE_SOLVER_POOL
    assert pcs.hard == frozenset({(11, 2)})
    assert pcs.soft == frozenset({(12, 2), (13, 2)})


def test_protected_corridors_pass3_block_empty_when_solver_pool_absent() -> None:
    pcs = protected_corridors_for_reclaim(
        pass3_trace={
            "protected_corridors": {"hard": [[4, 1]], "soft": [[5, 2]]},
        },
        solver_routing_state=None,
    )
    assert pcs.source == P4_RECLAIM_CORRIDOR_SOURCE_EMPTY
    assert pcs.hard == frozenset()
    assert pcs.soft == frozenset()


def test_protected_corridors_p3e3_touched_empty_when_solver_pool_absent() -> None:
    pcs = protected_corridors_for_reclaim(
        pass3_trace={
            "p3e3_guarded_commit_candidate": {
                "touched_hard_protected_cells": [[9, 1]],
                "touched_soft_protected_cells": [[10, 2]],
            },
        },
        solver_routing_state=None,
    )
    assert pcs.source == P4_RECLAIM_CORRIDOR_SOURCE_EMPTY
    assert pcs.hard == frozenset()
    assert pcs.soft == frozenset()


def test_protected_corridors_malformed_pass3_block_empty_source() -> None:
    pcs = protected_corridors_for_reclaim(
        pass3_trace={
            "protected_corridors": {"hard": "not-a-list", "soft": [[1, 1]]},
        },
        solver_routing_state=None,
    )
    assert pcs.hard == frozenset()
    assert pcs.soft == frozenset()
    assert pcs.source == P4_RECLAIM_CORRIDOR_SOURCE_EMPTY


def test_protected_corridors_malformed_trace_empty_source() -> None:
    pcs = protected_corridors_for_reclaim(
        pass3_trace={
            "p3e3_guarded_commit_candidate": "not-a-dict",
            "protected_corridors": "bad",
        },
        solver_routing_state=None,
    )
    assert pcs.hard == frozenset() and pcs.soft == frozenset()
    assert pcs.source == P4_RECLAIM_CORRIDOR_SOURCE_EMPTY


def test_reclaim_mineable_cur_uses_selected_protected_source() -> None:
    mineable = frozenset({(1, 1), (2, 1), (3, 1)})
    pcs = protected_corridors_for_reclaim(
        pass3_trace={},
        solver_routing_state={"hard_protected_corridors": [(2, 1)]},
    )
    assert pcs.source == P4_RECLAIM_CORRIDOR_SOURCE_SOLVER_POOL
    cur = _mineable_cur_for_reclaim(
        mineable,
        final_route_cells=frozenset(),
        hard_protected_corridors=pcs.hard,
        soft_protected_corridors=pcs.soft,
        committed_building_cells=frozenset(),
    )
    assert (2, 1) not in cur
    assert cur == frozenset({(1, 1), (3, 1)})


def test_run_reclaim_shadow_emits_corridor_trace_keys() -> None:
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    trace = run_reclaim_shadow_scan_after_pass3(
        m,
        m,
        final_mining_map=_base_final_mining_map(),
        is_external=_never_external,
        pass3_trace={
            "pass3_internal_transport_saved": 0,
            "protected_corridors": {"hard": [[15, 2]], "soft": []},
        },
    )
    assert trace.get("p4_reclaim_protected_corridor_source") == P4_RECLAIM_CORRIDOR_SOURCE_EMPTY
    assert trace.get("p4_reclaim_hard_protected_count") == 0
    assert trace.get("p4_reclaim_soft_protected_count") == 0
    assert trace.get("p4_reclaim_existing_layout_hint_cell_count") == 0


def test_solver_summary_p4_trace_when_shadow_runs() -> None:
    from tests.unit.shapez_asteroid.test_pass1_timeline_integration import (
        _decoded_miners_with_belt_escape,
    )

    decoded = _decoded_miners_with_belt_escape()
    fake_p4 = {
        "p4_reclaim_shadow_enabled": True,
        "p4_reclaim_shadow_skip_reason": None,
        "p4_reclaim_candidate_count": 3,
        "p4_reclaim_accepted_shadow_count": 1,
        "p4_reclaim_rejected_shadow_count": 2,
        "p4_reclaim_internal_transport_budget": 7,
        "p4_reclaim_internal_transport_projected_added": 2,
        "p4_reclaim_best_candidate": {"gain": 2.0, "rejected_reason": None},
    }
    fake_b1 = {
        "p4_reclaim_provisional_commit_attempted": True,
        "p4_reclaim_provisional_commit_committed": False,
        "p4_reclaim_provisional_commit_rollback_performed": False,
        "p4_reclaim_provisional_commit_rollback_reason": P4_REJECT_NO_SHADOW_CANDIDATE,
        "p4_reclaim_selected_candidate": None,
        "p4_reclaim_selected_candidate_rank": None,
        "p4_reclaim_added_extractor_cells": [],
        "p4_reclaim_added_extension_cells": [],
        "p4_reclaim_added_stub_cells": [],
        "p4_reclaim_provisional_commit_skip_reason": None,
    }
    loop_trace = {
        **fake_p4,
        **fake_b1,
        "p4_reclaim_shadow_scan_limit": 16,
        "p4_reclaim_loop_max_iterations": 3,
        "p4_reclaim_loop_iterations_executed": 1,
        "p4_reclaim_loop_successful_commits": 0,
        "p4_reclaim_loop_internal_transport_cumulative_added": 0,
        "p4_reclaim_loop_terminated_reason": "unit_test_loop_stub",
        "p4_reclaim_route_zone_excluded_cumulative_count": 0,
        "p4_reclaim_last_commit_route_cells": [],
        "p4_reclaim_last_soft_protected_candidate_cells": [],
    }
    with (
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service."
            "run_pass3_transport_minimization_from_maps",
            side_effect=lambda mm, **kw: (
                mm,
                None,
                {
                    "pass3_skipped": False,
                    "pass3_committed": True,
                    "gain": 1,
                    "commit_reason": "normal_gain",
                    "before_transport_count": 10,
                    "after_transport_count": 9,
                    "before_internal_transport_count": 20,
                    "after_internal_transport_count": 18,
                    "pass3_transport_cells_removed_total": 1,
                    "pass3_internal_transport_saved": 2,
                },
            ),
        ),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "run_p4_reclaim_loop_after_pass3",
            side_effect=lambda map_before, map_cur, **kw: (map_cur, loop_trace),
        ),
    ):
        out = build_solver_timeline(decoded)
    ss = out["solver_summary"]
    assert ss["p4_reclaim_candidate_count"] == 3
    assert ss["p4_reclaim_accepted_shadow_count"] == 1
    assert ss["p4_reclaim_internal_transport_budget"] == 7
    assert ss.get("p4_reclaim_provisional_commit_attempted") is True


def _fake_accepted_scan_trace() -> dict[str, object]:
    return {
        "p4_reclaim_shadow_enabled": True,
        "p4_reclaim_shadow_skip_reason": None,
        "p4_reclaim_shadow_scan_limit": MAX_RECLAIM_SHADOW_SCAN_LIMIT,
        "p4_reclaim_final_route_cells_added": [],
        "p4_reclaim_soft_protected_candidate_cells_added": [],
        "p4_reclaim_route_zone_rebuilt": False,
        "p4_reclaim_mineable_excluded_by_route_cells": 0,
        "p4_reclaim_candidate_count": 1,
        "p4_reclaim_accepted_shadow_count": 1,
        "p4_reclaim_rejected_shadow_count": 0,
        "p4_reclaim_internal_transport_budget": 10,
        "p4_reclaim_internal_transport_projected_added": 1,
        "p4_reclaim_best_candidate": None,
        "p4_reclaim_protected_corridor_source": P4_RECLAIM_CORRIDOR_SOURCE_EMPTY,
        "p4_reclaim_hard_protected_count": 0,
        "p4_reclaim_soft_protected_count": 0,
    }


def _accepted_eval_at_10_4():
    return _p4_bundle_eval(
        gain=2.0,
        additional_route_cost=1.0,
        gain_ratio=2.0,
        incremental_internal_transport_added=1,
        rejected_reason=None,
        accepted_shadow=True,
        anchor=(10, 4),
        extension=(10, 3),
        rotation=0,
    )


def test_p4_b1_no_accepted_candidate_no_commit() -> None:
    rej = _p4_bundle_eval(
        gain=2.0,
        additional_route_cost=1.0,
        gain_ratio=2.0,
        incremental_internal_transport_added=1,
        rejected_reason=P4_REJECT_GAIN_RATIO,
        accepted_shadow=False,
        anchor=(10, 4),
        extension=(10, 3),
        rotation=0,
    )
    scan = ReclaimShadowScanResult(
        trace=_fake_accepted_scan_trace(),
        evals=[rej],
        transport_kind="shape_belt",
    )
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    out_m, tr = run_p4_reclaim_provisional_commit_after_pass3(
        m,
        final_mining_map=_base_final_mining_map(),
        pass3_trace={"pass3_internal_transport_saved": 10},
        solver_routing_state=None,
        scan_result=scan,
    )
    assert out_m == m
    assert tr["p4_reclaim_provisional_commit_attempted"] is True
    assert tr["p4_reclaim_provisional_commit_committed"] is False
    assert tr["p4_reclaim_provisional_commit_rollback_reason"] == P4_REJECT_NO_SHADOW_CANDIDATE


def test_p4_b1_provisional_commit_when_validation_ok() -> None:
    scan = ReclaimShadowScanResult(
        trace=_fake_accepted_scan_trace(),
        evals=[_accepted_eval_at_10_4()],
        transport_kind="shape_belt",
    )
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    ok = FinalValidationReport(
        geometry_valid=True,
        connectivity_valid=True,
        disconnected_stub_count=0,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=0,
        overlap_violation_count=0,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
    )
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
        "validate_final_mining_layout",
        return_value=ok,
    ):
        out_m, tr = run_p4_reclaim_provisional_commit_after_pass3(
            m,
            final_mining_map=_base_final_mining_map(),
            pass3_trace={"pass3_internal_transport_saved": 10},
            solver_routing_state=None,
            scan_result=scan,
        )
    assert tr["p4_reclaim_provisional_commit_committed"] is True
    assert tr["p4_reclaim_provisional_commit_rollback_performed"] is False
    assert tr["p4_reclaim_added_extractor_cells"] == [[10, 4]]
    assert tr["p4_reclaim_added_extension_cells"] == [[10, 3]]
    assert tr["p4_reclaim_added_stub_cells"] == [[11, 4]]
    cells = {(r["x"], r["y"]): r for r in out_m if "x" in r and "y" in r}
    assert cells[(10, 4)].get("layout_kind") == "miner"
    assert cells[(10, 3)].get("layout_kind") == "extension"
    assert cells[(11, 4)].get("role") == "belt"
    assert tr.get("p4_reclaim_incremental_route_skip_reason") == "is_external_not_provided"


def test_p4_b2_commits_incremental_route_when_is_external_provided() -> None:
    scan = ReclaimShadowScanResult(
        trace=_fake_accepted_scan_trace(),
        evals=[_accepted_eval_at_10_4()],
        transport_kind="shape_belt",
    )
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    stub = (11, 4)
    path = [stub, (12, 4), (19, 2)]
    ok = FinalValidationReport(
        geometry_valid=True,
        connectivity_valid=True,
        disconnected_stub_count=0,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=0,
        overlap_violation_count=0,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
    )
    with (
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "validate_final_mining_layout",
            return_value=ok,
        ),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "placement_stub_route_probe_path",
            return_value=path,
        ),
    ):
        _out_m, tr = run_p4_reclaim_provisional_commit_after_pass3(
            m,
            final_mining_map=_base_final_mining_map(),
            pass3_trace={"pass3_internal_transport_saved": 10},
            solver_routing_state=None,
            scan_result=scan,
            is_external=_external_east,
        )
    assert tr["p4_reclaim_incremental_route_committed"] is True
    assert tr.get("p4_reclaim_incremental_route_skip_reason") is None
    assert tr.get("p4_reclaim_incremental_route_cells_added") == [[12, 4]]
    scan = ReclaimShadowScanResult(
        trace=_fake_accepted_scan_trace(),
        evals=[_accepted_eval_at_10_4()],
        transport_kind="shape_belt",
    )
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    bad = FinalValidationReport(
        geometry_valid=False,
        connectivity_valid=True,
        disconnected_stub_count=0,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=0,
        overlap_violation_count=0,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
    )
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
        "validate_final_mining_layout",
        return_value=bad,
    ):
        out_m, tr = run_p4_reclaim_provisional_commit_after_pass3(
            m,
            final_mining_map=_base_final_mining_map(),
            pass3_trace={"pass3_internal_transport_saved": 10},
            solver_routing_state=None,
            scan_result=scan,
        )
    assert out_m == m
    assert tr["p4_reclaim_provisional_commit_rollback_performed"] is True
    assert (
        tr["p4_reclaim_provisional_commit_rollback_reason"]
        == P4_ROLLBACK_AFTER_PROVISIONAL_VALIDATION_FAILURE
    )


def test_p4_b1_rejects_pre_apply_final_route_overlap() -> None:
    scan = ReclaimShadowScanResult(
        trace=_fake_accepted_scan_trace(),
        evals=[_accepted_eval_at_10_4()],
        transport_kind="shape_belt",
    )
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False) + [
        {"x": 11, "y": 4, "role": "belt"},
    ]
    out_m, tr = run_p4_reclaim_provisional_commit_after_pass3(
        m,
        final_mining_map=_base_final_mining_map(),
        pass3_trace={"pass3_internal_transport_saved": 10},
        solver_routing_state=None,
        scan_result=scan,
    )
    assert out_m == m
    assert tr["p4_reclaim_provisional_commit_rollback_reason"] == P4_REJECT_FINAL_ROUTE_OVERLAP


def test_p4_b1_rejects_hard_protected_overlap() -> None:
    scan = ReclaimShadowScanResult(
        trace=_fake_accepted_scan_trace(),
        evals=[_accepted_eval_at_10_4()],
        transport_kind="shape_belt",
    )
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    out_m, tr = run_p4_reclaim_provisional_commit_after_pass3(
        m,
        final_mining_map=_base_final_mining_map(),
        pass3_trace={"pass3_internal_transport_saved": 10},
        solver_routing_state={
            "hard_protected_corridors": [[10, 4]],
            "soft_protected_corridors": [],
        },
        scan_result=scan,
    )
    assert out_m == m
    assert tr["p4_reclaim_provisional_commit_rollback_reason"] == P4_REJECT_HARD_PROTECTED_CORRIDOR


def test_p4_b1_rejects_soft_protected_overlap_when_soft_has_active_transport() -> None:
    """Extension on a belt that is also soft-protected: pre-check hits final-route overlap first."""

    scan = ReclaimShadowScanResult(
        trace=_fake_accepted_scan_trace(),
        evals=[_accepted_eval_at_10_4()],
        transport_kind="shape_belt",
    )
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False) + [
        {"x": 10, "y": 3, "role": "belt"},
    ]
    out_m, tr = run_p4_reclaim_provisional_commit_after_pass3(
        m,
        final_mining_map=_base_final_mining_map(),
        pass3_trace={"pass3_internal_transport_saved": 10},
        solver_routing_state={
            "hard_protected_corridors": [],
            "soft_protected_corridors": [[10, 3]],
        },
        scan_result=scan,
    )
    assert out_m == m
    assert tr["p4_reclaim_provisional_commit_rollback_reason"] == P4_REJECT_FINAL_ROUTE_OVERLAP


def test_p4_b2_1_trial_connectivity_fail_geometry_ok_b2_succeeds() -> None:
    """P4-B2.1: B1 trial may fail connectivity; B2 route + merged full validation can succeed."""

    scan = ReclaimShadowScanResult(
        trace=_fake_accepted_scan_trace(),
        evals=[_accepted_eval_at_10_4()],
        transport_kind="shape_belt",
    )
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    stub = (11, 4)
    path = [stub, (12, 4), (19, 2)]
    trial_report = FinalValidationReport(
        geometry_valid=True,
        connectivity_valid=False,
        disconnected_stub_count=1,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=1,
        overlap_violation_count=0,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
    )
    merged_ok = FinalValidationReport(
        geometry_valid=True,
        connectivity_valid=True,
        disconnected_stub_count=0,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=0,
        overlap_violation_count=0,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
    )
    validate_queue = [trial_report, merged_ok]

    def _validate_side_effect(_mm: object) -> FinalValidationReport:
        return validate_queue.pop(0)

    with (
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "validate_final_mining_layout",
            side_effect=_validate_side_effect,
        ),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "placement_stub_route_probe_path",
            return_value=path,
        ),
    ):
        out_m, tr = run_p4_reclaim_provisional_commit_after_pass3(
            m,
            final_mining_map=_base_final_mining_map(),
            pass3_trace={"pass3_internal_transport_saved": 10},
            solver_routing_state=None,
            scan_result=scan,
            is_external=_external_east,
        )
    assert tr["p4_reclaim_provisional_commit_committed"] is True
    assert tr["p4_reclaim_incremental_route_committed"] is True
    assert validate_queue == []
    assert out_m != m


def test_p4_b2_1_incremental_disabled_disconnected_returns_original() -> None:
    scan = ReclaimShadowScanResult(
        trace=_fake_accepted_scan_trace(),
        evals=[_accepted_eval_at_10_4()],
        transport_kind="shape_belt",
    )
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    disconnected = FinalValidationReport(
        geometry_valid=True,
        connectivity_valid=False,
        disconnected_stub_count=1,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=1,
        overlap_violation_count=0,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
    )
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
        "validate_final_mining_layout",
        return_value=disconnected,
    ):
        out_m, tr = run_p4_reclaim_provisional_commit_after_pass3(
            m,
            final_mining_map=_base_final_mining_map(),
            pass3_trace={"pass3_internal_transport_saved": 10},
            solver_routing_state=None,
            scan_result=scan,
            p4_reclaim_incremental_route_commit_enabled=False,
        )
    assert out_m == m
    assert tr["p4_reclaim_provisional_commit_rollback_performed"] is True
    assert tr["p4_reclaim_provisional_commit_committed"] is False
    assert tr.get("p4_reclaim_incremental_route_skip_reason") == (
        "p4_reclaim_incremental_route_disabled"
    )


def test_p4_b2_1_is_external_none_disconnected_returns_original() -> None:
    scan = ReclaimShadowScanResult(
        trace=_fake_accepted_scan_trace(),
        evals=[_accepted_eval_at_10_4()],
        transport_kind="shape_belt",
    )
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    disconnected = FinalValidationReport(
        geometry_valid=True,
        connectivity_valid=False,
        disconnected_stub_count=1,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=1,
        overlap_violation_count=0,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
    )
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
        "validate_final_mining_layout",
        return_value=disconnected,
    ):
        out_m, tr = run_p4_reclaim_provisional_commit_after_pass3(
            m,
            final_mining_map=_base_final_mining_map(),
            pass3_trace={"pass3_internal_transport_saved": 10},
            solver_routing_state=None,
            scan_result=scan,
            is_external=None,
        )
    assert out_m == m
    assert tr["p4_reclaim_provisional_commit_rollback_performed"] is True
    assert tr["p4_reclaim_provisional_commit_committed"] is False
    assert tr.get("p4_reclaim_incremental_route_skip_reason") == "is_external_not_provided"


def test_p4_b2_1_incremental_disabled_fully_valid_allows_b1_only() -> None:
    scan = ReclaimShadowScanResult(
        trace=_fake_accepted_scan_trace(),
        evals=[_accepted_eval_at_10_4()],
        transport_kind="shape_belt",
    )
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    ok = FinalValidationReport(
        geometry_valid=True,
        connectivity_valid=True,
        disconnected_stub_count=0,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=0,
        overlap_violation_count=0,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
    )
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
        "validate_final_mining_layout",
        return_value=ok,
    ):
        out_m, tr = run_p4_reclaim_provisional_commit_after_pass3(
            m,
            final_mining_map=_base_final_mining_map(),
            pass3_trace={"pass3_internal_transport_saved": 10},
            solver_routing_state=None,
            scan_result=scan,
            p4_reclaim_incremental_route_commit_enabled=False,
        )
    assert out_m != m
    assert tr["p4_reclaim_provisional_commit_committed"] is True
    assert tr.get("p4_reclaim_incremental_route_skip_reason") == (
        "p4_reclaim_incremental_route_disabled"
    )


def test_p4_b2_1_b2_probe_failure_restores_original_map() -> None:
    scan = ReclaimShadowScanResult(
        trace=_fake_accepted_scan_trace(),
        evals=[_accepted_eval_at_10_4()],
        transport_kind="shape_belt",
    )
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    ok = FinalValidationReport(
        geometry_valid=True,
        connectivity_valid=False,
        disconnected_stub_count=0,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=0,
        overlap_violation_count=0,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
    )
    with (
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "validate_final_mining_layout",
            return_value=ok,
        ),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "placement_stub_route_probe_path",
            return_value=None,
        ),
    ):
        out_m, tr = run_p4_reclaim_provisional_commit_after_pass3(
            m,
            final_mining_map=_base_final_mining_map(),
            pass3_trace={"pass3_internal_transport_saved": 10},
            solver_routing_state=None,
            scan_result=scan,
            is_external=_external_east,
        )
    assert out_m == m
    assert tr["p4_reclaim_provisional_commit_rollback_performed"] is True
    assert tr["p4_reclaim_provisional_commit_committed"] is False
    assert tr.get("p4_reclaim_incremental_route_rollback_reason") == P4_REJECT_NO_INCREMENTAL_ROUTE


def test_p4_b2_1_b2_merged_validation_failure_restores_original_map() -> None:
    scan = ReclaimShadowScanResult(
        trace=_fake_accepted_scan_trace(),
        evals=[_accepted_eval_at_10_4()],
        transport_kind="shape_belt",
    )
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    stub = (11, 4)
    path = [stub, (12, 4), (19, 2)]
    trial_ok = FinalValidationReport(
        geometry_valid=True,
        connectivity_valid=False,
        disconnected_stub_count=1,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=1,
        overlap_violation_count=0,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
    )
    merged_bad = FinalValidationReport(
        geometry_valid=False,
        connectivity_valid=True,
        disconnected_stub_count=0,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=0,
        overlap_violation_count=1,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
    )
    validate_queue = [trial_ok, merged_bad]

    def _validate_side_effect(_mm: object) -> FinalValidationReport:
        return validate_queue.pop(0)

    with (
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "validate_final_mining_layout",
            side_effect=_validate_side_effect,
        ),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "placement_stub_route_probe_path",
            return_value=path,
        ),
    ):
        out_m, tr = run_p4_reclaim_provisional_commit_after_pass3(
            m,
            final_mining_map=_base_final_mining_map(),
            pass3_trace={"pass3_internal_transport_saved": 10},
            solver_routing_state=None,
            scan_result=scan,
            is_external=_external_east,
        )
    assert out_m == m
    assert tr["p4_reclaim_provisional_commit_rollback_performed"] is True
    assert tr["p4_reclaim_provisional_commit_committed"] is False
    assert tr.get("p4_reclaim_incremental_route_rollback_reason") == (
        P4_ROLLBACK_AFTER_INCREMENTAL_ROUTE_FAILED
    )
    assert validate_queue == []


def test_soft_replace_reject_not_soft_protected_map_unchanged() -> None:
    """§14.3: 소프트 풀 밖 셀을 치환 대상으로 두면 거절되고 입력 맵 셀 dict는 그대로다."""

    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    before_cells = cells_dict_from_mining_map(copy.deepcopy(m))
    out_map, tr = _try_atomic_replace_soft_corridor(
        m,
        final_mining_map=_base_final_mining_map(),
        pass3_trace={},
        solver_routing_state=None,
        old_soft_corridor_cells=[(11, 2)],
        is_external=_external_east,
    )
    assert out_map is None
    assert tr["p4_soft_replace_rejected_reason"] == P4_SOFT_REPLACE_REJECT_OLD_NOT_SOFT_PROTECTED
    assert cells_dict_from_mining_map(m) == before_cells


def test_soft_replace_rejects_hard_protected_corridor_map_unchanged() -> None:
    """§14.3 / PR4-B: hard 풀과 겹치는 치환 대상은 거절하고 입력 맵은 그대로다."""

    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    before_cells = cells_dict_from_mining_map(copy.deepcopy(m))
    out_map, tr = _try_atomic_replace_soft_corridor(
        m,
        final_mining_map=_base_final_mining_map(),
        pass3_trace={},
        solver_routing_state={
            "hard_protected_corridors": [[5, 5]],
            "soft_protected_corridors": [[14, 2]],
        },
        old_soft_corridor_cells=[(5, 5)],
        is_external=_external_east,
    )
    assert out_map is None
    assert tr["p4_soft_replace_attempted"] is True
    assert tr["p4_soft_replace_rejected_reason"] == P4_REJECT_HARD_PROTECTED_CORRIDOR
    assert cells_dict_from_mining_map(m) == before_cells


def test_soft_corridor_replace_rejects_without_replacement_route() -> None:
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    before = copy.deepcopy(m)
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
        "placement_stub_route_probe_path",
        return_value=None,
    ):
        out_map, tr = _try_atomic_replace_soft_corridor(
            m,
            final_mining_map=_base_final_mining_map(),
            pass3_trace={"pass3_internal_transport_saved": 10},
            solver_routing_state={
                "hard_protected_corridors": [],
                "soft_protected_corridors": [[14, 2]],
            },
            old_soft_corridor_cells=[(14, 2)],
            is_external=_external_east,
        )
    assert out_map is None
    assert tr["p4_soft_replace_attempted"] is True
    assert tr["p4_soft_replace_committed"] is False
    assert tr["p4_soft_replace_rejected_reason"] == P4_SOFT_REPLACE_REJECT_NO_REPLACEMENT_ROUTE
    assert tr["p4_soft_replace_connected"] is None
    assert tr.get("replacement_search_exhausted") is True
    assert tr.get("replacement_budget_keys") == list(CORRIDOR_REPLACEMENT_BUDGET_KEYS_SOFT_REPLACE)
    assert m == before


def _soft_replace_two_job_map() -> list[dict[str, object]]:
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    m.extend(
        [
            {
                "x": 10,
                "y": 4,
                "role": "occupied",
                "layout_kind": "miner",
                "surface": "shape",
                "r": 0,
                "placement_id": "p4-soft-v2-second",
            },
            {
                "x": 11,
                "y": 4,
                "role": "belt",
                "surface": "shape",
                "placement_id": "p4-soft-v2-second",
            },
        ]
    )
    return m


def _valid_layout_report() -> FinalValidationReport:
    return FinalValidationReport(
        geometry_valid=True,
        connectivity_valid=True,
        disconnected_stub_count=0,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=0,
        overlap_violation_count=0,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
    )


def test_soft_replace_v2_tries_multiple_jobs_until_one_succeeds() -> None:
    m = _soft_replace_two_job_map()
    before = copy.deepcopy(m)
    calls: list[tuple[int, int]] = []

    def probe_side_effect(
        *, outlet_stub: tuple[int, int], **_kwargs: object
    ) -> list[tuple[int, int]] | None:
        calls.append(outlet_stub)
        if outlet_stub == (11, 2):
            return None
        return [(11, 4), (12, 4), (13, 4), (14, 4), (15, 4), (16, 4), (17, 4), (18, 4)]

    with (
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "placement_stub_route_probe_path",
            side_effect=probe_side_effect,
        ),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "validate_final_mining_layout",
            return_value=_valid_layout_report(),
        ),
    ):
        out_map, tr = _try_atomic_replace_soft_corridor(
            m,
            final_mining_map=_base_final_mining_map(),
            pass3_trace={"pass3_internal_transport_saved": 10},
            solver_routing_state={
                "hard_protected_corridors": [],
                "soft_protected_corridors": [[14, 2]],
            },
            old_soft_corridor_cells=[(14, 2)],
            is_external=_external_east,
        )

    assert calls == [(11, 2), (11, 4)]
    assert out_map is not None
    assert m == before
    assert tr["p4_soft_replace_committed"] is True
    assert tr["p4_soft_replace_job_count"] == 2
    assert tr["p4_soft_replace_jobs_attempted"] == 2
    assert tr["p4_soft_replace_selected_job_index"] == 1
    assert tr["p4_soft_replace_rejected_reasons_by_job"] == [
        P4_SOFT_REPLACE_REJECT_NO_REPLACEMENT_ROUTE
    ]


def test_soft_replace_v2_preserves_map_when_all_jobs_fail() -> None:
    m = _soft_replace_two_job_map()
    before = copy.deepcopy(m)
    h_before = mining_map_state_hash(before)
    calls: list[tuple[int, int]] = []

    def probe_side_effect(*, outlet_stub: tuple[int, int], **_kwargs: object) -> None:
        calls.append(outlet_stub)
        return None

    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
        "placement_stub_route_probe_path",
        side_effect=probe_side_effect,
    ):
        out_map, tr = _try_atomic_replace_soft_corridor(
            m,
            final_mining_map=_base_final_mining_map(),
            pass3_trace={"pass3_internal_transport_saved": 10},
            solver_routing_state={
                "hard_protected_corridors": [],
                "soft_protected_corridors": [[14, 2]],
            },
            old_soft_corridor_cells=[(14, 2)],
            is_external=_external_east,
        )

    assert calls == [(11, 2), (11, 4)]
    assert out_map is None
    assert m == before
    assert mining_map_state_hash(m) == h_before
    assert tr["p4_soft_replace_committed"] is False
    assert tr["p4_soft_replace_job_count"] == 2
    assert tr["p4_soft_replace_jobs_attempted"] == 2
    assert tr["p4_soft_replace_selected_job_index"] is None
    assert tr["p4_soft_replace_rejected_reasons_by_job"] == [
        P4_SOFT_REPLACE_REJECT_NO_REPLACEMENT_ROUTE,
        P4_SOFT_REPLACE_REJECT_NO_REPLACEMENT_ROUTE,
    ]


def test_soft_replace_v2_records_selected_job_index() -> None:
    m = _soft_replace_two_job_map()

    def probe_side_effect(
        *, outlet_stub: tuple[int, int], **_kwargs: object
    ) -> list[tuple[int, int]]:
        if outlet_stub == (11, 2):
            return [(11, 2), (12, 4)]
        return [(11, 4), (12, 4), (13, 4), (14, 4)]

    with (
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "placement_stub_route_probe_path",
            side_effect=probe_side_effect,
        ),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "validate_final_mining_layout",
            return_value=_valid_layout_report(),
        ),
    ):
        out_map, tr = _try_atomic_replace_soft_corridor(
            m,
            final_mining_map=_base_final_mining_map(),
            pass3_trace={"pass3_internal_transport_saved": 10},
            solver_routing_state={
                "hard_protected_corridors": [],
                "soft_protected_corridors": [[14, 2]],
            },
            old_soft_corridor_cells=[(14, 2)],
            is_external=_external_east,
        )

    assert out_map is not None
    assert tr["p4_soft_replace_selected_job_index"] == 1
    assert tr["p4_soft_replace_jobs_attempted"] == 2
    assert tr["p4_soft_replace_rejected_reasons_by_job"] == [
        P4_SOFT_REPLACE_REJECT_REPLACEMENT_NOT_CONNECTED
    ]


def test_soft_corridor_replace_does_not_remove_old_cells_on_failure() -> None:
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    before = copy.deepcopy(m)
    stub = (11, 2)
    anchor = (19, 2)
    path = [
        stub,
        (12, 2),
        (13, 2),
        (13, 3),
        (14, 3),
        (15, 3),
        (15, 2),
        (16, 2),
        (17, 2),
        (18, 2),
        anchor,
    ]
    bad = FinalValidationReport(
        geometry_valid=False,
        connectivity_valid=False,
        disconnected_stub_count=0,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=0,
        overlap_violation_count=1,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
    )
    with (
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "placement_stub_route_probe_path",
            return_value=path,
        ),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "validate_final_mining_layout",
            return_value=bad,
        ),
    ):
        out_map, tr = _try_atomic_replace_soft_corridor(
            m,
            final_mining_map=_base_final_mining_map(),
            pass3_trace={"pass3_internal_transport_saved": 10},
            solver_routing_state={
                "hard_protected_corridors": [],
                "soft_protected_corridors": [[14, 2]],
            },
            old_soft_corridor_cells=[(14, 2)],
            is_external=_external_east,
        )
    assert out_map is None
    assert tr["p4_soft_replace_committed"] is False
    assert tr["p4_soft_replace_rejected_reason"] == P4_SOFT_REPLACE_REJECT_VALIDATION
    assert m == before


def test_soft_corridor_replace_commits_old_remove_and_new_add_atomically() -> None:
    m = _minimal_routed_shape_map(include_orphan_belt_at_8_4=False)
    before = copy.deepcopy(m)
    stub = (11, 2)
    anchor = (19, 2)
    path = [
        stub,
        (12, 2),
        (13, 2),
        (13, 3),
        (14, 3),
        (15, 3),
        (15, 2),
        (16, 2),
        (17, 2),
        (18, 2),
        anchor,
    ]
    ok = FinalValidationReport(
        geometry_valid=True,
        connectivity_valid=True,
        disconnected_stub_count=0,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=0,
        overlap_violation_count=0,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
    )
    with (
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "placement_stub_route_probe_path",
            return_value=path,
        ),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "validate_final_mining_layout",
            return_value=ok,
        ),
    ):
        out_map, tr = _try_atomic_replace_soft_corridor(
            m,
            final_mining_map=_base_final_mining_map(),
            pass3_trace={"pass3_internal_transport_saved": 10},
            solver_routing_state={
                "hard_protected_corridors": [],
                "soft_protected_corridors": [[14, 2]],
            },
            old_soft_corridor_cells=[(14, 2)],
            is_external=_external_east,
        )
    assert tr["p4_soft_replace_attempted"] is True
    assert tr["p4_soft_replace_committed"] is True
    assert tr["p4_soft_replace_rejected_reason"] is None
    assert tr["p4_soft_replace_connected"] is True
    assert tr["p4_soft_replace_old_cells"] == [[14, 2]]
    assert tr["p4_soft_replace_new_cells"]
    assert (14, 2) not in {(c[0], c[1]) for c in tr["p4_soft_replace_new_cells"]}
    assert m == before
    assert out_map is not None
    cells = {(r["x"], r["y"]): r for r in out_map if "x" in r and "y" in r}
    assert cells[(14, 2)].get("role") == "inferred"
    for xy in tr["p4_soft_replace_new_cells"]:
        assert cells[tuple(xy)].get("role") == "belt"


def test_select_best_accepted_deterministic_tie_break() -> None:
    a = _p4_bundle_eval(
        gain=2.0,
        additional_route_cost=1.0,
        gain_ratio=2.0,
        incremental_internal_transport_added=1,
        rejected_reason=None,
        accepted_shadow=True,
        anchor=(10, 4),
        extension=(10, 3),
        rotation=0,
    )
    b = _p4_bundle_eval(
        gain=2.0,
        additional_route_cost=1.0,
        gain_ratio=2.0,
        incremental_internal_transport_added=1,
        rejected_reason=None,
        accepted_shadow=True,
        anchor=(10, 5),
        extension=(10, 6),
        rotation=0,
    )
    best = select_best_accepted_p4_bundle([b, a])
    assert best is not None
    assert best.anchor == (10, 4)


def test_p4_scan_distance_bucket_near_mid_far() -> None:
    priors = frozenset({(10, 1)})
    d11 = _p4_min_manhattan_to_priors((11, 1), priors)
    d25 = _p4_min_manhattan_to_priors((25, 1), priors)
    d50 = _p4_min_manhattan_to_priors((50, 1), priors)
    assert _p4_scan_distance_bucket_name(d11, has_priors=True) == "near"
    assert _p4_scan_distance_bucket_name(d25, has_priors=True) == "mid"
    assert _p4_scan_distance_bucket_name(d50, has_priors=True) == "far"


def test_p4_bucketed_anchor_lists_sorted_yx_within_each_bucket() -> None:
    reclaim = {(11, 2), (11, 0), (50, 1), (25, 1)}
    priors = frozenset({(10, 1)})
    bm, order = _p4_bucketed_anchor_lists_for_scan(reclaim, priors)
    assert order == ("near", "mid", "far")
    assert bm["near"] == [(11, 0), (11, 2)]
    assert bm["mid"] == [(25, 1)]
    assert bm["far"] == [(50, 1)]


def test_p4_bucketed_anchor_lists_no_priors_single_all_stream() -> None:
    cells = {(3, 1), (2, 2), (2, 0)}
    bm, order = _p4_bucketed_anchor_lists_for_scan(cells, frozenset())
    assert order == ("all",)
    assert bm["all"] == sorted(cells, key=lambda p: (p[1], p[0]))


def test_p4_reclaim_diversity_triangular_continuity_peak_at_ideal() -> None:
    recent = (10, 1)
    anchor = (10 + RECLAIM_CONTINUITY_IDEAL_DISTANCE, 1)
    r = _p4_reclaim_diversity_fields(
        anchor,
        2.0,
        prior_reclaim_anchors=frozenset({recent}),
        route_zone_cells_for_overlap=frozenset(),
        shadow_route_path=(),
        recent_reclaim_anchors=(recent,),
        scan_distance_bucket="mid",
    )
    assert r["p4_continuity_band_state"] == "peak"
    assert abs(r["p4_continuity_bonus"] - RECLAIM_CONTINUITY_BONUS_MAX) < 1e-9
    assert r["p4_min_recent_anchor_distance"] == RECLAIM_CONTINUITY_IDEAL_DISTANCE
    assert r["p4_continuity_winning_index"] == 0
    assert r["p4_continuity_window_size"] == 1
    assert r["p4_continuity_max_weighted_t"] == pytest.approx(1.0)


def test_p4_reclaim_diversity_continuity_out_of_band_zero_bonus() -> None:
    recent = (10, 1)
    anchor = (50, 1)
    r = _p4_reclaim_diversity_fields(
        anchor,
        2.0,
        prior_reclaim_anchors=frozenset({recent}),
        route_zone_cells_for_overlap=frozenset(),
        shadow_route_path=(),
        recent_reclaim_anchors=(recent,),
        scan_distance_bucket="far",
    )
    assert r["p4_continuity_band_state"] == "out_of_band"
    assert r["p4_continuity_bonus"] == 0.0
    assert r["p4_continuity_winning_index"] == 0
    assert r["p4_continuity_window_size"] == 1


def test_p4_reclaim_diversity_window_older_anchor_can_win_under_decay() -> None:
    recent = ((10, 1), (23, 1))
    anchor = (36, 1)
    r = _p4_reclaim_diversity_fields(
        anchor,
        2.0,
        prior_reclaim_anchors=frozenset(recent),
        route_zone_cells_for_overlap=frozenset(),
        shadow_route_path=(),
        recent_reclaim_anchors=recent,
        scan_distance_bucket="mid",
    )
    assert r["p4_continuity_winning_index"] == 1
    assert r["p4_continuity_window_size"] == 2
    exp_bonus = RECLAIM_CONTINUITY_BONUS_MAX * RECLAIM_CONTINUITY_DECAY
    assert r["p4_continuity_bonus"] == pytest.approx(exp_bonus)


def test_p4_reclaim_diversity_decay_lowers_bonus_when_old_frontier_wins_max() -> None:
    anchor = (36, 1)
    base = dict(
        gain_ratio=2.0,
        prior_reclaim_anchors=frozenset({(10, 1), (23, 1)}),
        route_zone_cells_for_overlap=frozenset(),
        shadow_route_path=(),
        scan_distance_bucket="mid",
    )
    r_only_prior_peak = _p4_reclaim_diversity_fields(
        anchor,
        **base,
        recent_reclaim_anchors=((23, 1),),
    )
    r_window = _p4_reclaim_diversity_fields(
        anchor,
        **base,
        recent_reclaim_anchors=((10, 1), (23, 1)),
    )
    assert r_window["p4_continuity_winning_index"] == 1
    assert r_only_prior_peak["p4_continuity_bonus"] == pytest.approx(RECLAIM_CONTINUITY_BONUS_MAX)
    exp_decayed = RECLAIM_CONTINUITY_BONUS_MAX * RECLAIM_CONTINUITY_DECAY
    assert r_window["p4_continuity_bonus"] == pytest.approx(exp_decayed)
    assert r_only_prior_peak["p4_continuity_bonus"] > r_window["p4_continuity_bonus"]


def test_p4_recent_reclaim_window_newest_first() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
        RECLAIM_CONTINUITY_WINDOW,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim import (
        reclaim_shadow_commit_loop as _loop,
    )

    acc = [[1, 1], [2, 1], [3, 1]]
    w = _loop._p4_recent_reclaim_window_newest_first(acc, max_window=RECLAIM_CONTINUITY_WINDOW)
    assert w == ((3, 1), (2, 1), (1, 1))


def test_p4_frontier_orbit_streak_counts_trailing_near_previous() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
        RECLAIM_DIVERSITY_NEAR_RADIUS,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim import (
        reclaim_shadow_commit_loop as _loop,
    )

    acc = [[10, 1], [11, 1], [12, 1]]
    r_rad = RECLAIM_DIVERSITY_NEAR_RADIUS
    assert _loop._p4_frontier_orbit_streak_consecutive(acc, radius=r_rad) == 3
    acc_break = [[10, 1], [50, 1], [51, 1]]
    assert _loop._p4_frontier_orbit_streak_consecutive(acc_break, radius=r_rad) == 2
    a = _p4_bundle_eval(
        gain=2.0,
        additional_route_cost=1.0,
        gain_ratio=2.0,
        incremental_internal_transport_added=1,
        rejected_reason=None,
        accepted_shadow=True,
        anchor=(10, 4),
        extension=(10, 3),
        rotation=0,
        p4_total_diversity_penalty=1.0,
        p4_cluster_penalty=1.0,
        p4_continuity_bonus=0.0,
    )
    b = _p4_bundle_eval(
        gain=2.0,
        additional_route_cost=1.0,
        gain_ratio=2.0,
        incremental_internal_transport_added=1,
        rejected_reason=None,
        accepted_shadow=True,
        anchor=(10, 5),
        extension=(10, 6),
        rotation=0,
        p4_total_diversity_penalty=1.0,
        p4_cluster_penalty=1.0,
        p4_continuity_bonus=0.5,
    )
    assert a.p4_final_diversity_score == 1.0
    assert b.p4_final_diversity_score == 0.5
    best = select_best_accepted_p4_bundle([a, b])
    assert best is not None
    assert best.anchor == (10, 5)


def test_select_best_accepted_prefers_lower_diversity_penalty_at_same_gain() -> None:
    a = _p4_bundle_eval(
        gain=2.0,
        additional_route_cost=1.0,
        gain_ratio=2.0,
        incremental_internal_transport_added=1,
        rejected_reason=None,
        accepted_shadow=True,
        anchor=(10, 4),
        extension=(10, 3),
        rotation=0,
        p4_total_diversity_penalty=5.0,
        p4_cluster_penalty=5.0,
    )
    b = _p4_bundle_eval(
        gain=2.0,
        additional_route_cost=1.0,
        gain_ratio=2.0,
        incremental_internal_transport_added=1,
        rejected_reason=None,
        accepted_shadow=True,
        anchor=(10, 5),
        extension=(10, 6),
        rotation=0,
        p4_total_diversity_penalty=0.05,
        p4_cluster_penalty=0.05,
    )
    best = select_best_accepted_p4_bundle([a, b])
    assert best is not None
    assert best.anchor == (10, 5)


def test_path_additional_route_cost_detail_splits_first_hop() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_route_metrics import (  # noqa: E501
        _path_additional_route_cost,
        _path_additional_route_cost_detail,
    )

    path = [(0, 0), (1, 0), (2, 0)]
    ast = {(0, 0), (1, 0), (2, 0)}
    mine = {(0, 0), (1, 0), (2, 0)}
    b: dict = {}
    tc = {(0, 0): "belt"}
    tot, first, rest = _path_additional_route_cost_detail(
        path,
        asteroid_cells=ast,
        mineable_cells=mine,
        buildings=b,
        transport_cells=tc,
        fixed_stubs=frozenset({(0, 0)}),
        outlet_stub=(0, 0),
    )
    assert tot == _path_additional_route_cost(
        path,
        asteroid_cells=ast,
        mineable_cells=mine,
        buildings=b,
        transport_cells=tc,
        fixed_stubs=frozenset({(0, 0)}),
        outlet_stub=(0, 0),
    )
    assert first + rest == tot


def test_mineable_cur_smaller_soft_pool_includes_released_soft_cell() -> None:
    """Caller passes active soft only; released soft cells are not excluded."""

    mineable = frozenset({(1, 1), (2, 1), (3, 1)})
    cur_full = _mineable_cur_for_reclaim(
        mineable,
        final_route_cells=frozenset(),
        hard_protected_corridors=frozenset(),
        soft_protected_corridors=frozenset({(1, 1), (2, 1)}),
        committed_building_cells=frozenset(),
    )
    cur_active = _mineable_cur_for_reclaim(
        mineable,
        final_route_cells=frozenset(),
        hard_protected_corridors=frozenset(),
        soft_protected_corridors=frozenset({(1, 1)}),
        committed_building_cells=frozenset(),
    )
    assert (2, 1) not in cur_full
    assert (2, 1) in cur_active
