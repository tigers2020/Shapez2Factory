"""Pass3 transport minimization: commit safety, mixed-kind skip, solver rollback."""

from __future__ import annotations

import math
from dataclasses import replace
from unittest.mock import patch

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    COMMIT_REASON_DEGRADED_CONNECTED_RECOVERY,
    COMMIT_REASON_GUARDED_ATOMIC,
    P3E2_GUARD_FROM_ROUTING_CORRIDOR_POOL,
    P3F_COMMIT_REASON_NORMAL_GAIN,
    P4_ORCHESTRATION_ENTRY_SEGMENT_VALUE,
    PASS3_GREEDY_REJECT_DETAIL_CONNECTIVITY,
    RECOVERY_TRIGGER_PASS3_CONNECTIVITY_BREAK,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3 import pass3_greedy_core
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_greedy_core import (
    _new_pass3_greedy_local_replacement_stats,
    _try_greedy_local_replacement_reroute,
    reconstruct_mining_priority_transport,
    transport_connects_outlets_to_anchor,
    transport_outlets_disconnected_from_anchor,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_transport import (
    MAX_ROUTE_LENGTH_RATIO,
    P3E3_ATOMIC_SKIPPED_SHADOW_LEX_INCOMPLETE,
    P3E3_REJECT_CONNECTIVITY,
    P3E3_REJECT_DISCONNECTED_STUB,
    P3E3_REJECT_FIXED_STUB_REMOVAL,
    P3E3_REJECT_HARD_PROTECTED_CORRIDOR,
    P3E3_REJECT_NO_INTERNAL_TRANSPORT_GAIN,
    P3E3_REJECT_NO_REPLACEMENT_ROUTE,
    P3E3_REJECT_PRECHECK_NO_REPLACEMENT_ROUTE,
    P3E3_REJECT_ROUTE_LENGTH_RATIO,
    _p3e3_build_atomic_candidate_map,
    _p3e3_route_length_ratio_allowed,
    mining_map_after_transport_reconstruction,
    run_pass3_transport_minimization_from_maps,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.recovery_context import (
    RECOVERY_SEGMENT_P4_RECLAIM,
    RECOVERY_SEGMENT_POST_RECLAIM_PASS3,
    RECOVERY_SEGMENT_SOFT_REPLACE_V2,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
    _post_reclaim_pass3_gate,
    build_solver_timeline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_state_hash import (
    mining_map_state_hash,
    normalized_mining_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    FinalValidationReport,
    validate_final_mining_layout,
)


def _patch_validation_recovery_attempts_zero():
    """Solvers tests assume one Pass3→P4 leg (no validation retry loop)."""

    return patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline."
        "recovery_orchestrator.MAX_VALIDATION_RECOVERY_ATTEMPTS",
        0,
    )


def _p3e3_shrink_candidate_cells_one_internal(fc: frozenset, is_external) -> frozenset:
    """Drop one internal transport coord so P3-E3 internal-transport delta gate allows commit."""

    internal = [c for c in fc if not is_external(c)]
    if internal:
        return frozenset(fc - {internal[0]})
    return fc


def test_transport_connects_outlets_requires_adjacent_tiles_no_void_jump() -> None:
    """Gap cells are not belt/pipe — graph must not jump void (Pass3 commit safety)."""

    mineable = {(x, y) for x in range(0, 6) for y in range(3)}
    asteroid = set(mineable)
    stub = (0, 1)
    gap = (2, 1)
    anchor = (4, 1)
    tc = {
        stub: "belt",
        (1, 1): "belt",
        gap: "belt",
        (3, 1): "belt",
        anchor: "belt",
    }
    assert transport_connects_outlets_to_anchor(
        tc,
        outlets_order=[stub],
        anchor=anchor,
        mineable_cells=mineable,
        asteroid_cells=asteroid,
    )
    gap_removed = {k: v for k, v in tc.items() if k != gap}
    assert not transport_connects_outlets_to_anchor(
        gap_removed,
        outlets_order=[stub],
        anchor=anchor,
        mineable_cells=mineable,
        asteroid_cells=asteroid,
    )


def test_transport_connects_requires_every_outlet_to_reach_anchor() -> None:
    """All listed outlets must lie in the anchor's transport component (P3-C)."""

    transport = {
        (0, 0): "belt",
        (1, 0): "belt",
        (2, 0): "belt",
        (10, 0): "belt",
    }
    assert not transport_connects_outlets_to_anchor(
        transport,
        outlets_order=[(0, 0), (10, 0)],
        anchor=(2, 0),
    )
    assert transport_connects_outlets_to_anchor(
        transport,
        outlets_order=[(0, 0)],
        anchor=(2, 0),
    )


def test_pass3_rewrite_preserves_non_target_transport_kind() -> None:
    mining_map = [
        {"x": 1, "y": 0, "role": "belt"},
        {"x": 2, "y": 0, "role": "pipe"},
    ]
    out = mining_map_after_transport_reconstruction(
        mining_map,
        {(1, 0): "belt"},
        target_role="belt",
    )
    assert any(r["role"] == "pipe" and r["x"] == 2 and r["y"] == 0 for r in out)
    assert any(r["role"] == "belt" and r["x"] == 1 and r["y"] == 0 for r in out)


def test_run_pass3_mixed_transport_kind_skips() -> None:
    """Two extractors with different transport_kind → MVP skip."""

    rows = [
        {
            "x": 5,
            "y": 1,
            "role": "occupied",
            "layout_kind": "miner",
            "surface": "shape",
            "r": 0,
        },
        {"x": 6, "y": 1, "role": "belt"},
        {
            "x": 5,
            "y": 3,
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "surface": "fluid",
            "r": 0,
        },
        {"x": 6, "y": 3, "role": "pipe"},
    ]
    final_rows = [{"x": x, "y": y, "role": "inferred"} for x in range(4, 10) for y in range(0, 6)]

    def never_ext(_c: tuple[int, int]) -> bool:
        return False

    _m, _res, trace = run_pass3_transport_minimization_from_maps(
        rows,
        final_mining_map=final_rows,
        is_external=never_ext,
    )
    assert trace["pass3_skipped"] is True
    assert trace["pass3_skip_reason"] == "mixed_transport_kind_mvp"
    assert trace.get("p3e2_shadow_rejected_reason") == "pass3_skipped_mixed_transport_kind_mvp"
    assert trace.get("p3e3_guarded_commit_enabled") is None
    assert trace.get("p3e3_guarded_rejected_reason") == "pass3_skipped_mixed_transport_kind_mvp"
    assert trace.get("pass3_greedy_committed") is None


def test_pass3_rejected_reason_in_solver_summary_when_zero_gain() -> None:
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
                    "pass3_skipped": False,
                    "pass3_committed": False,
                    "pass3_greedy_committed": False,
                    "gain": 0,
                    "rejected_reason": "rejected_by_gain_or_length",
                    "before_transport_count": 3,
                    "after_transport_count": 3,
                    "before_internal_transport_count": 3,
                    "after_internal_transport_count": 3,
                    "pass3_transport_cells_removed_total": 0,
                    "pass3_internal_transport_saved": 0,
                },
            ),
        ),
    ):
        out = build_solver_timeline(decoded)
    ss = out["solver_summary"]
    assert ss.get("pass3_rejected_reason") == "rejected_by_gain_or_length"
    assert ss.get("pass3_commit_reason") is None
    assert ss.get("pass3_attempted_commit") is False
    assert ss.get("pass3_final_committed") is True
    assert ss.get("pass3_map_accepted") is True
    assert ss.get("pass3_greedy_committed") is False


def test_pass3_final_validation_failure_sets_rollback_reason() -> None:
    from tests.unit.shapez_asteroid.test_pass1_timeline_integration import (
        _decoded_miners_with_belt_escape,
    )

    holder: list[list[dict]] = []

    def fake_pass3(map_after_routing: list[dict], **kwargs: object) -> tuple:
        _ = kwargs
        attempt = list(map_after_routing)
        holder[:] = [attempt]
        return (
            attempt,
            None,
            {
                "pass3_skipped": False,
                "pass3_committed": True,
                "pass3_greedy_committed": True,
                "gain": 1,
                "commit_reason": "normal_gain",
                "before_transport_count": 10,
                "after_transport_count": 9,
                "before_internal_transport_count": 8,
                "after_internal_transport_count": 7,
                "pass3_transport_cells_removed_total": 1,
                "pass3_internal_transport_saved": 1,
            },
        )

    real_val = validate_final_mining_layout

    def val_wrap(m: list[dict]) -> FinalValidationReport:
        r = real_val(m)
        if holder and m is holder[0]:
            return replace(r, connectivity_valid=False, disconnected_stub_count=1)
        return r

    decoded = _decoded_miners_with_belt_escape()
    with (
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service."
            "run_pass3_transport_minimization_from_maps",
            fake_pass3,
        ),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service."
            "validate_final_mining_layout",
            val_wrap,
        ),
    ):
        out = build_solver_timeline(decoded)
    ss = out["solver_summary"]
    assert ss.get("pass3_skipped") is False
    assert ss.get("pass3_reverted") is True
    assert ss.get("pass3_rollback_reason") == "final_validation_failed_after_pass3"
    assert ss.get("pass3_attempted_commit") is True
    assert ss.get("pass3_final_committed") is False
    assert ss.get("pass3_committed") is True
    assert ss.get("pass3_map_accepted") is False
    assert ss.get("pass3_greedy_committed") is True
    assert ss.get("p4_reclaim_shadow_enabled") is False
    assert ss.get("p4_reclaim_shadow_skip_reason") == "pass3_reverted"
    assert ss.get("recovery_pass3_connectivity_break") is True
    assert ss.get("recovery_trigger") == RECOVERY_TRIGGER_PASS3_CONNECTIVITY_BREAK
    sample = ss.get("pass3_connectivity_reject_sample")
    assert isinstance(sample, dict)
    assert sample.get("source") == "final_validation_after_pass3_commit"


def test_pass3_timeline_frame_includes_before_after_counts_when_eligible() -> None:
    from tests.unit.shapez_asteroid.test_pass1_timeline_integration import (
        _decoded_miners_with_belt_escape,
    )

    out = build_solver_timeline(_decoded_miners_with_belt_escape())
    p3f = next(f for f in out["solver_timeline"] if f["id"] == "solver_pass3_transport")
    s = p3f["summary"]
    ss = out["solver_summary"]
    assert s.get("before_pass3_counts") is not None
    assert s.get("after_pass3_counts") is not None
    assert "pass3_transport_cells_removed" in s
    assert "before_internal_transport_count" in s
    assert "pass3_transport_cells_removed_total" in s
    assert "pass3_greedy_committed" in s
    assert isinstance(s.get("pass3_map_accepted"), bool)
    if s.get("pass3_transport_cells_removed_total") is not None:
        tot = int(s["pass3_transport_cells_removed_total"])
        internal = int(s.get("pass3_internal_transport_saved") or 0)
        assert internal <= tot
    assert ss.get("p3e3_guarded_commit_enabled") is True
    assert ss.get("p3e3_guarded_commit_attempted") is True
    assert ss.get("p3e3_guarded_rejected_reason") != "guarded_disabled"
    assert isinstance(ss.get("p3e3_guarded_committed"), bool)
    if not s.get("pass3_skipped"):
        assert s.get("p3e2_shadow_enabled") is True
        assert "p3e2_lex_found" in s
        assert "p3e2_shadow_would_commit" in s
        assert "p3e2_outlet_count" in s
        assert "p3e2_hard_protected_guard_state" in s
        assert s.get("p3e2_hard_protected_guard_state") == P3E2_GUARD_FROM_ROUTING_CORRIDOR_POOL


def test_pass3_internal_saved_implied_matches_saved_on_timeline_frame() -> None:
    from tests.unit.shapez_asteroid.test_pass1_timeline_integration import (
        _decoded_miners_with_belt_escape,
    )

    out = build_solver_timeline(_decoded_miners_with_belt_escape())
    p3f = next(f for f in out["solver_timeline"] if f["id"] == "solver_pass3_transport")
    s = p3f["summary"]
    if s.get("pass3_skipped"):
        pytest.skip("pass3 skipped in fixture")
    implied = int(s.get("pass3_internal_transport_saved_implied") or 0)
    saved = int(s.get("pass3_internal_transport_saved") or 0)
    assert implied == saved


def test_pass3_run_emits_exit_transport_count_and_map_hash() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
        build_solver_timeline,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
        external_predicate_for_mining_map,
    )
    from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline
    from tests.unit.shapez_asteroid.test_pass1_timeline_integration import (
        _decoded_miners_with_belt_escape,
    )

    decoded = _decoded_miners_with_belt_escape()
    out = build_solver_timeline(decoded)
    step4 = next(f for f in out["solver_timeline"] if f["id"] == "solver_step4_routing")
    map_after_routing = step4["mining_map"]
    mt = build_map_timeline(decoded)
    final_map = mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    _m, _res, trace = run_pass3_transport_minimization_from_maps(
        map_after_routing,
        final_mining_map=final_map,
        is_external=is_ext,
    )
    if trace.get("pass3_skipped"):
        pytest.skip("pass3 skipped in fixture")
    implied_sv = trace["pass3_internal_transport_saved_implied"]
    assert implied_sv == trace["pass3_internal_transport_saved"]
    assert isinstance(trace.get("pass3_exit_mining_map_state_hash"), str)
    assert isinstance(trace.get("pass3_exit_transport_cell_count"), int)


def test_transport_outlets_disconnected_from_anchor_matches_bfs() -> None:
    transport = {
        (0, 0): "belt",
        (1, 0): "belt",
        (2, 0): "belt",
        (10, 0): "belt",
    }
    assert transport_outlets_disconnected_from_anchor(
        transport,
        outlets_order=[(0, 0), (10, 0)],
        anchor=(2, 0),
        limit=5,
    ) == [(10, 0)]


def test_reconstruct_mining_priority_transport_reject_detail_connectivity_spine() -> None:
    """Single interior belt cell: removal breaks stub→anchor connectivity → detail taxonomy."""

    res = reconstruct_mining_priority_transport(
        anchor=(3, 0),
        asteroid_cells=set(),
        mineable_cells={(1, 0), (2, 0), (3, 0)},
        buildings={},
        transport_cells={(1, 0): "belt", (2, 0): "belt", (3, 0): "belt"},
        outlets_order=[(1, 0)],
        transport_role="belt",
    )
    assert res.committed is False
    assert res.metrics.get("pass3_greedy_reject_detail") == PASS3_GREEDY_REJECT_DETAIL_CONNECTIVITY
    sample = res.metrics.get("pass3_connectivity_reject_sample")
    assert isinstance(sample, dict)
    assert sample["victim_cell"] == [2, 0]
    assert sample["affected_stub_count"] == 1
    assert sample["disconnected_stub_samples"] == [[1, 0]]
    assert sample["nearest_anchor_distance"] == 1
    assert sample["transport_cell_count_before_trial"] == 3
    assert sample["transport_cell_count_after_trial"] == 2
    lr = res.metrics.get("pass3_greedy_local_replacement")
    assert isinstance(lr, dict)
    assert lr["enabled"] is False
    assert lr["attempted_count"] == 0
    assert lr["accepted_count"] == 0
    assert lr["rejected_by_no_path"] == 0


def test_reconstruct_mining_priority_transport_local_reroute_saves_internal_when_enabled() -> None:
    """Delete-only breaks spine; detour on y=1 (external) restores link and drops internal count."""

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
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.internal_transport_metrics import (  # noqa: E501
        count_internal_transport_cells,
    )

    before_i = count_internal_transport_cells(tc.keys(), is_external=is_ext_y_ne_0)
    after_i = count_internal_transport_cells(res.transport_cells.keys(), is_external=is_ext_y_ne_0)
    assert res.committed is True
    assert res.metrics.get("commit_reason") == "normal_gain"
    assert after_i < before_i
    assert transport_connects_outlets_to_anchor(
        res.transport_cells,
        outlets_order=[(1, 0)],
        anchor=(5, 0),
    )
    lr = res.metrics.get("pass3_greedy_local_replacement")
    assert isinstance(lr, dict)
    assert lr["enabled"] is True
    assert lr["attempted_count"] >= 1
    assert lr["accepted_count"] >= 1
    assert set(res.transport_cells.values()) == {"belt"}


def test_reconstruct_mining_priority_transport_local_reroute_preserves_other_pipe_role() -> None:
    """Same-kind reroute must not rewrite unrelated ``pipe`` rows (belt Pass3 scope)."""

    def is_ext_y_ne_0(c: tuple[int, int]) -> bool:
        return c[1] != 0

    mineable = {(x, y) for x in range(1, 22) for y in range(0, 3)}
    tc = {
        (1, 0): "belt",
        (2, 0): "belt",
        (3, 0): "belt",
        (4, 0): "belt",
        (5, 0): "belt",
    }

    def mining_map_from_belt_transport(transport: dict[tuple[int, int], str]) -> list[dict]:
        rows: list[dict] = []
        for p in sorted(mineable, key=lambda c: (c[1], c[0])):
            rows.append({"x": p[0], "y": p[1], "role": "inferred"})
        for p in sorted(transport, key=lambda c: (c[1], c[0])):
            rows.append({"x": p[0], "y": p[1], "role": "belt"})
        rows.append({"x": 20, "y": 0, "role": "pipe"})
        return rows

    map_before = mining_map_from_belt_transport(tc)
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_greedy_core."
        "PASS3_GREEDY_LOCAL_REPLACEMENT_ENABLED",
        True,
    ):
        res = reconstruct_mining_priority_transport(
            anchor=(5, 0),
            asteroid_cells=set(mineable),
            mineable_cells=mineable,
            buildings={},
            transport_cells=dict(tc),
            outlets_order=[(1, 0)],
            transport_role="shape_belt",
            is_external=is_ext_y_ne_0,
        )
    new_map = mining_map_after_transport_reconstruction(
        map_before,
        res.transport_cells,
        target_role="belt",
    )
    pipe_rows = [r for r in new_map if r.get("x") == 20 and r.get("y") == 0]
    assert pipe_rows and pipe_rows[0].get("role") == "pipe"


def test_try_greedy_local_replacement_no_net_internal_gain_rejects() -> None:
    """Reroute may connect, but zero internal tiles (all external) cannot satisfy strict gain."""

    def all_external(_c: tuple[int, int]) -> bool:
        return True

    mineable = {(x, y) for x in range(1, 12) for y in range(0, 3)}
    asteroid = set(mineable)
    pre = {(i, 0): "belt" for i in range(1, 6)}
    trial = {k: v for k, v in pre.items() if k != (3, 0)}
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_greedy_core."
        "PASS3_GREEDY_LOCAL_REPLACEMENT_ENABLED",
        True,
    ):
        stats = _new_pass3_greedy_local_replacement_stats()
        out = _try_greedy_local_replacement_reroute(
            pre,
            trial,
            wr="belt",
            anchor=(5, 0),
            outlets_order=[(1, 0)],
            mineable_cells=mineable,
            asteroid_cells=asteroid,
            buildings={},
            is_external=all_external,
            stats=stats,
        )
    assert out is None
    assert stats["attempted_count"] == 1
    assert stats["accepted_count"] == 0
    assert int(stats["rejected_by_no_net_internal_gain"]) >= 1


def test_try_greedy_local_replacement_path_len_reject_does_not_merge_path() -> None:
    """``rejected_by_path_len`` returns ``None`` before writing the too-long path to ``merged``."""

    mineable = {(x, y) for x in range(1, 12) for y in range(0, 3)}
    asteroid = set(mineable)
    pre = {(i, 0): "belt" for i in range(1, 6)}
    trial = {k: v for k, v in pre.items() if k != (3, 0)}

    def long_path(**_kwargs: object) -> list[tuple[int, int]]:
        return [(1, 0), (1, 1), (2, 1), (3, 1)]

    with (
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_greedy_core."
            "PASS3_GREEDY_LOCAL_REPLACEMENT_ENABLED",
            True,
        ),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_greedy_core."
            "PASS3_GREEDY_LOCAL_REPLACEMENT_MAX_PATH_LEN",
            2,
        ),
        patch.object(pass3_greedy_core, "placement_stub_route_probe_path", long_path),
    ):
        stats = _new_pass3_greedy_local_replacement_stats()
        out = _try_greedy_local_replacement_reroute(
            pre,
            trial,
            wr="belt",
            anchor=(5, 0),
            outlets_order=[(1, 0)],
            mineable_cells=mineable,
            asteroid_cells=asteroid,
            buildings={},
            is_external=lambda _c: False,
            stats=stats,
        )
    assert out is None
    assert stats["accepted_count"] == 0
    assert stats["rejected_by_path_len"] == 1
    assert (1, 1) not in trial


def test_pass3_internal_saved_implies_reclaimed_interior_nonempty() -> None:
    """Interior saved > 0 ⇒ ``_reclaimed_interior_transport_cells`` is non-empty (P4 handoff)."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim import (
        reclaim_map_ops,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.internal_transport_metrics import (  # noqa: E501
        count_internal_transport_cells,
    )

    def is_ext_y_ne_0(c: tuple[int, int]) -> bool:
        return c[1] != 0

    mineable = {(x, y) for x in range(1, 8) for y in range(0, 3)}
    tc = {
        (1, 0): "belt",
        (2, 0): "belt",
        (3, 0): "belt",
        (4, 0): "belt",
        (5, 0): "belt",
    }

    def mining_map_from_belt_transport(transport: dict[tuple[int, int], str]) -> list[dict]:
        rows: list[dict] = []
        for p in sorted(mineable, key=lambda c: (c[1], c[0])):
            rows.append({"x": p[0], "y": p[1], "role": "inferred"})
        for p in sorted(transport, key=lambda c: (c[1], c[0])):
            rows.append({"x": p[0], "y": p[1], "role": "belt"})
        return rows

    map_before = mining_map_from_belt_transport(tc)
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_greedy_core."
        "PASS3_GREEDY_LOCAL_REPLACEMENT_ENABLED",
        True,
    ):
        res = reconstruct_mining_priority_transport(
            anchor=(5, 0),
            asteroid_cells=set(mineable),
            mineable_cells=mineable,
            buildings={},
            transport_cells=dict(tc),
            outlets_order=[(1, 0)],
            transport_role="shape_belt",
            is_external=is_ext_y_ne_0,
        )
    map_after = mining_map_after_transport_reconstruction(
        map_before,
        res.transport_cells,
        target_role="belt",
    )
    bi = count_internal_transport_cells(tc.keys(), is_external=is_ext_y_ne_0)
    ai = count_internal_transport_cells(res.transport_cells.keys(), is_external=is_ext_y_ne_0)
    saved = max(0, bi - ai)
    assert saved > 0
    reclaimed = reclaim_map_ops._reclaimed_interior_transport_cells(
        map_before,
        map_after,
        is_external=is_ext_y_ne_0,
    )
    assert len(reclaimed) > 0


def test_p3e3_rollback_guarded_transport_cells_copies_role_map() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_transport import (
        _p3e3_rollback_guarded_transport_cells,
    )

    snap = {(5, 1): "belt", (10, 1): "belt"}
    out = _p3e3_rollback_guarded_transport_cells(known_good_transport_snapshot=snap)
    assert out == snap
    assert out is not snap


def test_run_pass3_p3e3_guarded_enabled_emits_precheck_trace() -> None:
    """Opt-in guarded flag: precheck + E3b atomic path; commit iff pre + post validation pass."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
        external_predicate_for_mining_map,
    )
    from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline
    from tests.unit.shapez_asteroid.test_pass1_timeline_integration import (
        _decoded_miners_with_belt_escape,
    )

    decoded = _decoded_miners_with_belt_escape()
    out = build_solver_timeline(decoded)
    step4 = next(f for f in out["solver_timeline"] if f["id"] == "solver_step4_routing")
    map_after_routing = step4["mining_map"]
    mt = build_map_timeline(decoded)
    final_map = mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    _m, res, trace = run_pass3_transport_minimization_from_maps(
        map_after_routing,
        final_mining_map=final_map,
        is_external=is_ext,
        p3e3_guarded_commit_enabled=True,
    )
    assert trace.get("pass3_skipped") is False
    assert isinstance(trace.get("pass3_greedy_committed"), bool)
    assert trace.get("pass3_committed") == bool(
        trace.get("pass3_greedy_committed") or trace.get("p3e3_guarded_committed")
    )
    assert trace.get("p3e3_guarded_commit_enabled") is True
    assert trace.get("p3e3_guarded_commit_attempted") is True
    wa = trace.get("p3e3_guarded_commit_would_accept")
    gc = trace.get("p3e3_guarded_commit_committed")
    post = trace.get("p3e3_guarded_post_commit_validation_passed")
    assert gc == bool(wa and post)
    assert trace.get("p3e3_guarded_committed") == gc
    r = trace.get("p3e3_guarded_rejected_reason")
    assert isinstance(r, str) and r.startswith("precheck_")
    cand = trace.get("p3e3_guarded_precheck_candidate")
    assert isinstance(cand, dict)
    assert "outlet_stub_cells" in cand
    assert trace.get("p3e3_guarded_precheck_shadow_rejected_reason") == trace.get(
        "p3e2_shadow_rejected_reason"
    )
    assert trace.get("p3e3_atomic_candidate_built") is not None
    assert trace.get("p3e3_candidate_validation_passed") is not None
    assert wa is not None
    assert isinstance(trace.get("p3e3_guarded_commit_candidate"), dict)
    assert isinstance(trace.get("p3e3_guarded_known_good_transport_cell_count"), int)
    if wa is True and post is True:
        assert trace.get("p3e3_guarded_commit_rollback_performed") is False
        assert trace.get("p3e3_guarded_commit_rollback_reason") is None
        assert trace.get("p3e3_guarded_commit_mode") == "atomic_candidate_swap"
        assert trace.get("commit_reason") == P3F_COMMIT_REASON_NORMAL_GAIN
        assert trace.get("pass3_commit_subtype") == COMMIT_REASON_GUARDED_ATOMIC
        assert res is not None and res.committed is True
    elif wa is True and post is False:
        assert trace.get("p3e3_guarded_commit_mode") == "atomic_candidate_swap"
        assert trace.get("p3e3_guarded_commit_rollback_performed") is True
        rr = trace.get("p3e3_guarded_commit_rollback_reason")
        assert rr in (P3E3_REJECT_CONNECTIVITY, P3E3_REJECT_DISCONNECTED_STUB)
    elif wa is True and post is None:
        assert trace.get("p3e3_guarded_commit_mode") == "internal_transport_delta_gate"
        assert trace.get("p3e3_guarded_commit_rollback_performed") is False
        assert trace.get("p3e3_internal_transport_delta_gate_evaluated") is True
        delta_iv = trace.get("p3e3_candidate_internal_transport_delta")
        assert isinstance(delta_iv, int) and delta_iv >= 0
        assert trace.get("p3e3_internal_transport_delta_gate_reject") == (
            P3E3_REJECT_NO_INTERNAL_TRANSPORT_GAIN
        )
        assert trace.get("p3f_rejected_reason") == P3E3_REJECT_NO_INTERNAL_TRANSPORT_GAIN
        assert trace.get("p3e3_guarded_commit_committed") is not True
        assert trace.get("p3e3_guarded_committed") is not True
    else:
        assert trace.get("p3e3_guarded_commit_mode") is None
        assert trace.get("p3e3_guarded_commit_rollback_performed") is False


def test_pass3_guarded_skips_atomic_when_shadow_lex_incomplete() -> None:
    """P3-E3 checklist: shadow lex incomplete → no E3b atomic (same policy as greedy-only skip)."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3 import (
        pass3_transport as p3_mod,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
        external_predicate_for_mining_map,
    )
    from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline
    from tests.unit.shapez_asteroid.test_pass1_timeline_integration import (
        _decoded_miners_with_belt_escape,
    )

    decoded = _decoded_miners_with_belt_escape()
    out = build_solver_timeline(decoded)
    step4 = next(f for f in out["solver_timeline"] if f["id"] == "solver_step4_routing")
    map_after_routing = step4["mining_map"]
    mt = build_map_timeline(decoded)
    final_map = mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])

    orig_shadow = p3_mod._p3e2_shadow_trace

    def shadow_lex_incomplete(**kw: object) -> dict[str, object]:
        d = orig_shadow(**kw)
        return {
            **d,
            "p3e2_lex_found": False,
            "p3e2_shadow_would_commit": False,
            "p3e2_shadow_rejected_reason": "lex_not_found",
        }

    with patch.object(p3_mod, "_p3e2_shadow_trace", side_effect=shadow_lex_incomplete):
        _m, _res, trace = run_pass3_transport_minimization_from_maps(
            map_after_routing,
            final_mining_map=final_map,
            is_external=is_ext,
            p3e3_guarded_commit_enabled=True,
        )
    skipped = trace.get("p3e3_guarded_atomic_skipped_reason")
    assert skipped == P3E3_ATOMIC_SKIPPED_SHADOW_LEX_INCOMPLETE
    assert trace.get("p3e3_atomic_candidate_built") is None
    assert trace.get("p3e3_guarded_commit_committed") is False


def test_run_pass3_allow_degraded_connected_follows_recovery_context() -> None:
    """Non-recovery runs must not enable ``degraded_connected_recovery`` on the greedy core."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3 import (
        pass3_transport as p3_mod,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
        external_predicate_for_mining_map,
    )
    from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline
    from tests.unit.shapez_asteroid.test_pass1_timeline_integration import (
        _decoded_miners_with_belt_escape,
    )

    decoded = _decoded_miners_with_belt_escape()
    out = build_solver_timeline(decoded)
    step4 = next(f for f in out["solver_timeline"] if f["id"] == "solver_step4_routing")
    map_after_routing = step4["mining_map"]
    mt = build_map_timeline(decoded)
    final_map = mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])

    orig = p3_mod.reconstruct_mining_priority_transport
    captured: list[bool] = []

    def cap(*args: object, **kw: object) -> object:
        captured.append(bool(kw.get("allow_degraded_connected_commit")))
        return orig(*args, **kw)

    for want_recovery in (False, True):
        captured.clear()
        with patch.object(p3_mod, "reconstruct_mining_priority_transport", side_effect=cap):
            run_pass3_transport_minimization_from_maps(
                map_after_routing,
                final_mining_map=final_map,
                is_external=is_ext,
                pass3_recovery_context=want_recovery,
            )
        assert captured == [want_recovery]


def test_p3e3_should_commit_guarded_candidate_helper() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_transport import (
        P3E3GuardedCommitCandidate,
        _p3e3_should_commit_guarded_candidate,
    )

    dto = P3E3GuardedCommitCandidate(
        attempted=True,
        candidate_transport_cells=frozenset({(1, 1)}),
        removed_transport_cells=frozenset(),
        added_transport_cells=frozenset(),
        preserved_stub_cells=frozenset({(1, 1)}),
        touched_hard_protected_cells=frozenset(),
        touched_soft_protected_cells=frozenset(),
        replacement_route_cells=frozenset({(1, 1)}),
        baseline_route_length=1,
        candidate_route_length=1,
        route_length_ratio=1.0,
        precheck_passed=True,
        rejected_reason=None,
        hard_protected_corridors=frozenset(),
    )
    assert _p3e3_should_commit_guarded_candidate(
        guarded_enabled=True,
        candidate=dto,
        candidate_validation_passed=True,
        would_accept=True,
    )
    assert not _p3e3_should_commit_guarded_candidate(
        guarded_enabled=False,
        candidate=dto,
        candidate_validation_passed=True,
        would_accept=True,
    )


def test_guarded_off_matches_guarded_on_when_atomic_commit_disabled() -> None:
    """Regression: default greedy transport when guarded swap gate does not fire."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
        external_predicate_for_mining_map,
    )
    from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline
    from tests.unit.shapez_asteroid.test_pass1_timeline_integration import (
        _decoded_miners_with_belt_escape,
    )

    decoded = _decoded_miners_with_belt_escape()
    out = build_solver_timeline(decoded)
    step4 = next(f for f in out["solver_timeline"] if f["id"] == "solver_step4_routing")
    map_after_routing = step4["mining_map"]
    mt = build_map_timeline(decoded)
    final_map = mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    _, res_off, _ = run_pass3_transport_minimization_from_maps(
        map_after_routing,
        final_mining_map=final_map,
        is_external=is_ext,
        p3e3_guarded_commit_enabled=False,
    )
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_transport."
        "_p3e3_should_commit_guarded_candidate",
        return_value=False,
    ):
        _, res_on, _ = run_pass3_transport_minimization_from_maps(
            map_after_routing,
            final_mining_map=final_map,
            is_external=is_ext,
            p3e3_guarded_commit_enabled=True,
        )
    assert res_off is not None and res_on is not None
    assert frozenset(res_off.transport_cells) == frozenset(res_on.transport_cells)


def test_guarded_atomic_swap_applies_candidate_transport_cells() -> None:
    """E3b-2a: would_accept + gate True → final transport dict matches candidate frozenset."""

    import django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_transport as p3_mod  # noqa: E501
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_transport import (
        P3E3GuardedCommitCandidate,
        _p3e3_atomic_trace_from_dto,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
        external_predicate_for_mining_map,
    )
    from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline
    from tests.unit.shapez_asteroid.test_pass1_timeline_integration import (
        _decoded_miners_with_belt_escape,
    )

    decoded = _decoded_miners_with_belt_escape()
    out = build_solver_timeline(decoded)
    step4 = next(f for f in out["solver_timeline"] if f["id"] == "solver_step4_routing")
    map_after_routing = step4["mining_map"]
    mt = build_map_timeline(decoded)
    final_map = mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])

    captured: list[frozenset] = []

    def fake_phase(**kw: object) -> tuple:
        tc_in = kw["transport_cells"]
        assert isinstance(tc_in, dict)
        fc0 = frozenset(tc_in.keys())
        is_ext_fn = kw["is_external"]
        assert callable(is_ext_fn)
        fc = _p3e3_shrink_candidate_cells_one_internal(fc0, is_ext_fn)
        captured.append(fc)
        stubs = frozenset(kw["outlets_order"])
        dto = P3E3GuardedCommitCandidate(
            attempted=True,
            candidate_transport_cells=fc,
            removed_transport_cells=frozenset(),
            added_transport_cells=frozenset(),
            preserved_stub_cells=stubs,
            touched_hard_protected_cells=frozenset(),
            touched_soft_protected_cells=frozenset(),
            replacement_route_cells=fc,
            baseline_route_length=3,
            candidate_route_length=3,
            route_length_ratio=1.0,
            precheck_passed=True,
            rejected_reason=None,
            hard_protected_corridors=frozenset(),
        )
        tr = _p3e3_atomic_trace_from_dto(
            dto,
            atomic_candidate_built=True,
            validation_passed=True,
            would_accept=True,
            atomic_rejected=None,
        )
        return dto, tr

    with (
        patch.object(p3_mod, "_p3e3_run_atomic_candidate_phase", fake_phase),
        patch.object(
            p3_mod,
            "_p3e3_validate_guarded_swap_mining_map",
            return_value=(True, None, None),
        ),
    ):
        _m, res, trace = run_pass3_transport_minimization_from_maps(
            map_after_routing,
            final_mining_map=final_map,
            is_external=is_ext,
            p3e3_guarded_commit_enabled=True,
        )
    assert res is not None
    assert trace.get("p3e3_guarded_commit_committed") is True
    assert frozenset(res.transport_cells) == captured[0]
    assert trace.get("commit_reason") == P3F_COMMIT_REASON_NORMAL_GAIN
    assert trace.get("pass3_commit_subtype") == COMMIT_REASON_GUARDED_ATOMIC


def test_guarded_recovery_atomic_non_negative_internal_delta_commit_reason() -> None:
    """Recovery: delta gate does not block delta>=0; guarded commit uses degraded_connected."""

    import django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_transport as p3_mod  # noqa: E501
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_transport import (
        P3E3GuardedCommitCandidate,
        _p3e3_atomic_trace_from_dto,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
        external_predicate_for_mining_map,
    )
    from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline
    from tests.unit.shapez_asteroid.test_pass1_timeline_integration import (
        _decoded_miners_with_belt_escape,
    )

    decoded = _decoded_miners_with_belt_escape()
    out = build_solver_timeline(decoded)
    step4 = next(f for f in out["solver_timeline"] if f["id"] == "solver_step4_routing")
    map_after_routing = step4["mining_map"]
    mt = build_map_timeline(decoded)
    final_map = mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])

    def fake_phase(**kw: object) -> tuple:
        tc_in = kw["transport_cells"]
        assert isinstance(tc_in, dict)
        fc0 = frozenset(tc_in.keys())
        stubs = frozenset(kw["outlets_order"])
        dto = P3E3GuardedCommitCandidate(
            attempted=True,
            candidate_transport_cells=fc0,
            removed_transport_cells=frozenset(),
            added_transport_cells=frozenset(),
            preserved_stub_cells=stubs,
            touched_hard_protected_cells=frozenset(),
            touched_soft_protected_cells=frozenset(),
            replacement_route_cells=fc0,
            baseline_route_length=3,
            candidate_route_length=3,
            route_length_ratio=1.0,
            precheck_passed=True,
            rejected_reason=None,
            hard_protected_corridors=frozenset(),
        )
        tr = _p3e3_atomic_trace_from_dto(
            dto,
            atomic_candidate_built=True,
            validation_passed=True,
            would_accept=True,
            atomic_rejected=None,
        )
        return dto, tr

    with (
        patch.object(p3_mod, "_p3e3_run_atomic_candidate_phase", fake_phase),
        patch.object(
            p3_mod,
            "_p3e3_validate_guarded_swap_mining_map",
            return_value=(True, None, None),
        ),
    ):
        _m, res, trace = run_pass3_transport_minimization_from_maps(
            map_after_routing,
            final_mining_map=final_map,
            is_external=is_ext,
            p3e3_guarded_commit_enabled=True,
            pass3_recovery_context=True,
        )
    assert res is not None and res.committed is True
    assert trace.get("p3e3_guarded_commit_committed") is True
    assert trace.get("p3e3_guarded_commit_mode") == "atomic_candidate_swap"
    assert trace.get("p3e3_internal_transport_delta_gate_reject") is None
    d = trace.get("p3e3_candidate_internal_transport_delta")
    assert isinstance(d, int) and d >= 0
    assert trace.get("commit_reason") == COMMIT_REASON_DEGRADED_CONNECTED_RECOVERY
    assert trace.get("pass3_commit_subtype") == COMMIT_REASON_GUARDED_ATOMIC


def test_p3e3_build_rejects_fixed_stub_removal() -> None:
    stub = (5, 1)
    current = frozenset({stub, (6, 1), (7, 1)})
    remove = frozenset({stub})
    rep = frozenset({(6, 1), (7, 1)})
    out = _p3e3_build_atomic_candidate_map(
        current_transport_cells=current,
        cells_to_remove=remove,
        replacement_route_cells=rep,
        fixed_output_stubs=frozenset({stub}),
        hard_protected_corridors=frozenset(),
        soft_protected_corridors=frozenset(),
        baseline_route_length=10,
        candidate_route_length=10,
        attempted=True,
    )
    assert out.precheck_passed is False
    assert out.rejected_reason == P3E3_REJECT_FIXED_STUB_REMOVAL


def test_p3e3_build_rejects_hard_protected_corridor() -> None:
    hard_cell = (4, 1)
    current = frozenset({(3, 1), hard_cell, (5, 1)})
    out = _p3e3_build_atomic_candidate_map(
        current_transport_cells=current,
        cells_to_remove=frozenset({hard_cell}),
        replacement_route_cells=frozenset({(3, 1), (5, 1)}),
        fixed_output_stubs=frozenset({(3, 1)}),
        hard_protected_corridors=frozenset({hard_cell}),
        soft_protected_corridors=frozenset(),
        baseline_route_length=3,
        candidate_route_length=3,
        attempted=True,
    )
    assert out.precheck_passed is False
    assert out.rejected_reason == P3E3_REJECT_HARD_PROTECTED_CORRIDOR


def test_p3e3_build_rejects_soft_without_replacement_route() -> None:
    soft_cell = (8, 1)
    out = _p3e3_build_atomic_candidate_map(
        current_transport_cells=frozenset({(7, 1), soft_cell}),
        cells_to_remove=frozenset({soft_cell}),
        replacement_route_cells=frozenset(),
        fixed_output_stubs=frozenset({(7, 1)}),
        hard_protected_corridors=frozenset(),
        soft_protected_corridors=frozenset({soft_cell}),
        baseline_route_length=2,
        candidate_route_length=2,
        attempted=True,
    )
    assert out.precheck_passed is False
    assert out.rejected_reason == P3E3_REJECT_NO_REPLACEMENT_ROUTE


def test_p3e3_route_length_ratio_ceil_policy() -> None:
    """candidate <= ceil(baseline * 1.35)."""

    assert _p3e3_route_length_ratio_allowed(baseline_route_length=100, candidate_route_length=135)
    assert not _p3e3_route_length_ratio_allowed(
        baseline_route_length=100,
        candidate_route_length=136,
    )
    allowed = math.ceil(100 * MAX_ROUTE_LENGTH_RATIO)
    assert allowed == 135
    assert _p3e3_route_length_ratio_allowed(
        baseline_route_length=100,
        candidate_route_length=122,
        max_route_length_ratio=1.22,
    )
    assert not _p3e3_route_length_ratio_allowed(
        baseline_route_length=100,
        candidate_route_length=123,
        max_route_length_ratio=1.22,
    )


def test_p3e3_atomic_trace_route_ratio_telemetry() -> None:
    """Reject path exposes cap, allowed max length, slack (cells)."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_e3_guarded_dto import (  # noqa: E501
        P3E3GuardedCommitCandidate,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_e3_guarded_trace import (  # noqa: E501
        _p3e3_atomic_trace_from_dto,
    )

    dto = P3E3GuardedCommitCandidate(
        attempted=True,
        candidate_transport_cells=frozenset(),
        removed_transport_cells=frozenset(),
        added_transport_cells=frozenset(),
        preserved_stub_cells=frozenset(),
        touched_hard_protected_cells=frozenset(),
        touched_soft_protected_cells=frozenset(),
        replacement_route_cells=frozenset(),
        baseline_route_length=10,
        candidate_route_length=50,
        route_length_ratio=5.0,
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
        route_length_ratio_cap=MAX_ROUTE_LENGTH_RATIO,
    )
    assert tr["p3e3_route_length_ratio_cap"] == MAX_ROUTE_LENGTH_RATIO
    assert tr["p3e3_route_allowed_max_length"] == math.ceil(10 * MAX_ROUTE_LENGTH_RATIO)
    assert tr["p3e3_route_length_slack_cells"] == tr["p3e3_route_allowed_max_length"] - 50


def test_post_reclaim_p3e3_route_ratio_max_formula() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
        POST_RECLAIM_P3E3_ROUTE_RATIO_BASE,
        POST_RECLAIM_P3E3_ROUTE_RATIO_CAP,
        POST_RECLAIM_P3E3_ROUTE_RATIO_K,
        post_reclaim_p3e3_route_ratio_max,
    )

    assert post_reclaim_p3e3_route_ratio_max(pass3_internal_transport_saved=0) == pytest.approx(
        POST_RECLAIM_P3E3_ROUTE_RATIO_BASE
    )
    assert post_reclaim_p3e3_route_ratio_max(pass3_internal_transport_saved=10) == pytest.approx(
        POST_RECLAIM_P3E3_ROUTE_RATIO_BASE + 10 * POST_RECLAIM_P3E3_ROUTE_RATIO_K
    )
    assert post_reclaim_p3e3_route_ratio_max(
        pass3_internal_transport_saved=10**9
    ) == pytest.approx(float(POST_RECLAIM_P3E3_ROUTE_RATIO_CAP))


def test_run_post_reclaim_pass3_forwards_adaptive_route_cap() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
        post_reclaim_p3e3_route_ratio_max,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_timeline import (
        _run_post_reclaim_pass3_once,
    )

    kw: dict[str, object] = {}

    def fake_pass3(mm: object, **kwargs: object) -> tuple:
        kw.update(kwargs)
        return (
            mm,
            None,
            {"pass3_skipped": True, "pass3_skip_reason": "unit_stub"},
        )

    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service."
        "run_pass3_transport_minimization_from_maps",
        side_effect=fake_pass3,
    ):
        _run_post_reclaim_pass3_once(
            [],
            final_mining_map=[],
            is_external=lambda c: False,
            pass3_summary={"pass3_internal_transport_saved": 20},
        )
    assert kw.get("p3e3_atomic_route_ratio_max") == post_reclaim_p3e3_route_ratio_max(
        pass3_internal_transport_saved=20
    )


def test_p3e3_atomic_phase_collect_abort_trace() -> None:
    """Collect failure → atomic_candidate_built False and precheck_no_replacement_route."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_transport import (
        _p3e3_run_atomic_candidate_phase,
    )

    def fake_collect(**_kwargs: object) -> tuple:
        return (
            frozenset(),
            frozenset(),
            None,
            None,
            frozenset(),
            frozenset(),
            P3E3_REJECT_PRECHECK_NO_REPLACEMENT_ROUTE,
        )

    cells = {(5, 1): {"x": 5, "y": 1, "role": "belt"}}
    tc = {(5, 1): "belt"}
    mining_map = [{"x": 5, "y": 1, "role": "belt"}]
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_e3_guarded."
        "_p3e3_collect_guarded_lex_replacement",
        fake_collect,
    ):
        _dto, tr = _p3e3_run_atomic_candidate_phase(
            mining_map=mining_map,
            cells=cells,
            transport_cells=tc,
            outlets_order=[(5, 1)],
            anchor=(10, 1),
            want_role="belt",
            transport_kind="shape_belt",
            asteroid_cells={(5, 1), (6, 1), (10, 1)},
            mineable_f=frozenset(),
            asteroid_f=frozenset({(5, 1), (6, 1), (10, 1)}),
            is_external=lambda c: c[0] > 20,
        )
    assert tr.get("p3e3_atomic_candidate_built") is False
    assert (
        tr.get("p3e3_guarded_commit_rejected_reason") == P3E3_REJECT_PRECHECK_NO_REPLACEMENT_ROUTE
    )
    assert tr.get("p3e3_guarded_commit_would_accept") is False
    assert tr.get("p3e3_route_length_ratio_cap") == MAX_ROUTE_LENGTH_RATIO
    assert tr.get("p3e3_route_allowed_max_length") is None
    assert tr.get("p3e3_route_length_slack_cells") is None


def test_p3e3_atomic_phase_route_length_ratio_reject() -> None:
    """candidate length over ceil(baseline * 1.35) → rejected_by_route_length_ratio."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_transport import (
        _p3e3_run_atomic_candidate_phase,
    )

    def fake_collect(**_kwargs: object) -> tuple:
        return (
            frozenset(),
            frozenset({(5, 1), (6, 1), (10, 1)}),
            10,
            50,
            frozenset(),
            frozenset(),
            None,
        )

    cells = {
        (5, 1): {"x": 5, "y": 1, "role": "belt"},
        (6, 1): {"x": 6, "y": 1, "role": "belt"},
        (10, 1): {"x": 10, "y": 1, "role": "belt"},
    }
    tc = {(5, 1): "belt", (6, 1): "belt", (10, 1): "belt"}
    mining_map = list(cells[c] for c in sorted(cells, key=lambda p: (p[1], p[0])))
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_e3_guarded."
        "_p3e3_collect_guarded_lex_replacement",
        fake_collect,
    ):
        _dto, tr = _p3e3_run_atomic_candidate_phase(
            mining_map=mining_map,
            cells=cells,
            transport_cells=tc,
            outlets_order=[(5, 1)],
            anchor=(10, 1),
            want_role="belt",
            transport_kind="shape_belt",
            asteroid_cells={(5, 1), (6, 1), (10, 1)},
            mineable_f=frozenset(),
            asteroid_f=frozenset({(5, 1), (6, 1), (10, 1)}),
            is_external=lambda c: c[0] > 20,
        )
    assert tr.get("p3e3_atomic_candidate_built") is True
    assert tr.get("p3e3_guarded_commit_rejected_reason") == P3E3_REJECT_ROUTE_LENGTH_RATIO
    assert tr.get("p3e3_guarded_commit_would_accept") is False
    assert tr.get("p3e3_route_length_ratio_cap") == MAX_ROUTE_LENGTH_RATIO
    assert tr.get("p3e3_route_allowed_max_length") == math.ceil(10 * MAX_ROUTE_LENGTH_RATIO)
    assert tr.get("p3e3_route_length_slack_cells") == tr.get("p3e3_route_allowed_max_length") - 50


def test_guarded_post_commit_validation_failure_restores_greedy_snapshot() -> None:
    """E3b-2b: would_accept + swap gate True but post-commit validation fails → greedy snapshot."""

    import django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_transport as p3_mod  # noqa: E501
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_transport import (
        P3E3GuardedCommitCandidate,
        _p3e3_atomic_trace_from_dto,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
        external_predicate_for_mining_map,
    )
    from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline
    from tests.unit.shapez_asteroid.test_pass1_timeline_integration import (
        _decoded_miners_with_belt_escape,
    )

    decoded = _decoded_miners_with_belt_escape()
    out = build_solver_timeline(decoded)
    step4 = next(f for f in out["solver_timeline"] if f["id"] == "solver_step4_routing")
    map_after_routing = step4["mining_map"]
    mt = build_map_timeline(decoded)
    final_map = mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])

    greedy_holder: list[dict] = []
    orig_reconstruct = p3_mod.reconstruct_mining_priority_transport

    def capture_reconstruct(**kw: object) -> object:
        r = orig_reconstruct(**kw)
        greedy_holder.append(dict(r.transport_cells))
        return r

    def fake_phase(**kw: object) -> tuple:
        tc_in = kw["transport_cells"]
        assert isinstance(tc_in, dict)
        fc0 = frozenset(tc_in.keys())
        is_ext_fn = kw["is_external"]
        assert callable(is_ext_fn)
        fc = _p3e3_shrink_candidate_cells_one_internal(fc0, is_ext_fn)
        stubs = frozenset(kw["outlets_order"])
        dto = P3E3GuardedCommitCandidate(
            attempted=True,
            candidate_transport_cells=fc,
            removed_transport_cells=frozenset(),
            added_transport_cells=frozenset(),
            preserved_stub_cells=stubs,
            touched_hard_protected_cells=frozenset(),
            touched_soft_protected_cells=frozenset(),
            replacement_route_cells=fc,
            baseline_route_length=3,
            candidate_route_length=3,
            route_length_ratio=1.0,
            precheck_passed=True,
            rejected_reason=None,
            hard_protected_corridors=frozenset(),
        )
        tr = _p3e3_atomic_trace_from_dto(
            dto,
            atomic_candidate_built=True,
            validation_passed=True,
            would_accept=True,
            atomic_rejected=None,
        )
        return dto, tr

    with (
        patch.object(p3_mod, "reconstruct_mining_priority_transport", capture_reconstruct),
        patch.object(p3_mod, "_p3e3_run_atomic_candidate_phase", fake_phase),
        patch.object(
            p3_mod,
            "_p3e3_validate_guarded_swap_mining_map",
            return_value=(False, P3E3_REJECT_CONNECTIVITY, None),
        ),
    ):
        _m, res, trace = run_pass3_transport_minimization_from_maps(
            map_after_routing,
            final_mining_map=final_map,
            is_external=is_ext,
            p3e3_guarded_commit_enabled=True,
        )
    assert greedy_holder
    assert res is not None
    assert res.transport_cells == greedy_holder[0]
    assert trace.get("p3e3_guarded_commit_would_accept") is True
    assert trace.get("p3e3_guarded_commit_committed") is False
    assert trace.get("p3e3_guarded_commit_rollback_performed") is True
    assert trace.get("p3e3_guarded_commit_rollback_reason") == P3E3_REJECT_CONNECTIVITY
    assert trace.get("p3e3_guarded_post_commit_validation_passed") is False

    _m2, _, _ = run_pass3_transport_minimization_from_maps(
        map_after_routing,
        final_mining_map=final_map,
        is_external=is_ext,
        p3e3_guarded_commit_enabled=False,
    )
    assert mining_map_state_hash(_m) == mining_map_state_hash(_m2)
    assert normalized_mining_map(_m) == normalized_mining_map(_m2)


def test_guarded_post_commit_success_keeps_candidate_when_would_accept() -> None:
    """E3b-2b success path: explicit post-commit OK preserves atomic transport map."""

    import django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_transport as p3_mod  # noqa: E501
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_transport import (
        P3E3GuardedCommitCandidate,
        _p3e3_atomic_trace_from_dto,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
        external_predicate_for_mining_map,
    )
    from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline
    from tests.unit.shapez_asteroid.test_pass1_timeline_integration import (
        _decoded_miners_with_belt_escape,
    )

    decoded = _decoded_miners_with_belt_escape()
    out = build_solver_timeline(decoded)
    step4 = next(f for f in out["solver_timeline"] if f["id"] == "solver_step4_routing")
    map_after_routing = step4["mining_map"]
    mt = build_map_timeline(decoded)
    final_map = mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])

    captured: list[frozenset] = []

    def fake_phase(**kw: object) -> tuple:
        tc_in = kw["transport_cells"]
        assert isinstance(tc_in, dict)
        fc0 = frozenset(tc_in.keys())
        is_ext_fn = kw["is_external"]
        assert callable(is_ext_fn)
        fc = _p3e3_shrink_candidate_cells_one_internal(fc0, is_ext_fn)
        captured.append(fc)
        stubs = frozenset(kw["outlets_order"])
        dto = P3E3GuardedCommitCandidate(
            attempted=True,
            candidate_transport_cells=fc,
            removed_transport_cells=frozenset(),
            added_transport_cells=frozenset(),
            preserved_stub_cells=stubs,
            touched_hard_protected_cells=frozenset(),
            touched_soft_protected_cells=frozenset(),
            replacement_route_cells=fc,
            baseline_route_length=3,
            candidate_route_length=3,
            route_length_ratio=1.0,
            precheck_passed=True,
            rejected_reason=None,
            hard_protected_corridors=frozenset(),
        )
        tr = _p3e3_atomic_trace_from_dto(
            dto,
            atomic_candidate_built=True,
            validation_passed=True,
            would_accept=True,
            atomic_rejected=None,
        )
        return dto, tr

    with (
        patch.object(p3_mod, "_p3e3_run_atomic_candidate_phase", fake_phase),
        patch.object(
            p3_mod,
            "_p3e3_validate_guarded_swap_mining_map",
            return_value=(True, None, None),
        ),
    ):
        _m, res, trace = run_pass3_transport_minimization_from_maps(
            map_after_routing,
            final_mining_map=final_map,
            is_external=is_ext,
            p3e3_guarded_commit_enabled=True,
        )
    assert res is not None
    assert trace.get("p3e3_guarded_commit_committed") is True
    assert trace.get("p3e3_guarded_post_commit_validation_passed") is True
    assert trace.get("p3e3_guarded_commit_rollback_performed") is False
    assert frozenset(res.transport_cells) == captured[0]


def test_guarded_commit_accepts_real_layout_candidate_snapshot() -> None:
    """E3b-3: belt fixture builds atomic candidate; post-commit validates reconstructed map.

    Lex/greedy-equal candidate can still break full-layout connectivity on
    ``mining_map_after_transport_reconstruction``; gate must rollback (no false accept).
    """

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
        external_predicate_for_mining_map,
    )
    from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline
    from tests.unit.shapez_asteroid.test_pass1_timeline_integration import (
        _decoded_miners_with_belt_escape,
    )

    decoded = _decoded_miners_with_belt_escape()
    out = build_solver_timeline(decoded)
    step4 = next(f for f in out["solver_timeline"] if f["id"] == "solver_step4_routing")
    map_after_routing = step4["mining_map"]
    mt = build_map_timeline(decoded)
    final_map = mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])

    _m_off, res_off, _tr_off = run_pass3_transport_minimization_from_maps(
        map_after_routing,
        final_mining_map=final_map,
        is_external=is_ext,
        p3e3_guarded_commit_enabled=False,
        pass3_recovery_context=True,
    )
    _m_on, res_on, trace = run_pass3_transport_minimization_from_maps(
        map_after_routing,
        final_mining_map=final_map,
        is_external=is_ext,
        p3e3_guarded_commit_enabled=True,
        pass3_recovery_context=True,
    )

    assert trace["p3e3_atomic_candidate_built"] is True
    assert trace["p3e3_candidate_validation_passed"] is True
    assert trace["p3e3_guarded_commit_would_accept"] is True
    assert trace["p3e3_guarded_post_commit_validation_passed"] is False
    assert trace["p3e3_guarded_commit_committed"] is False
    assert trace["p3e3_guarded_commit_rollback_performed"] is True
    assert trace["p3e3_guarded_commit_rollback_reason"] in (
        P3E3_REJECT_CONNECTIVITY,
        P3E3_REJECT_DISCONNECTED_STUB,
    )
    assert trace["p3e3_guarded_commit_mode"] == "atomic_candidate_swap"

    cand = trace["p3e3_guarded_commit_candidate"]
    assert cand["precheck_passed"] is True
    assert cand["rejected_reason"] is None
    assert cand["baseline_route_length"] == cand["candidate_route_length"]
    assert cand["route_length_ratio"] == 1.0
    assert len(cand["candidate_transport_cells"]) == 37
    assert len(cand["removed_transport_cells"]) == 2
    assert len(cand["added_transport_cells"]) == 18
    assert len(cand["preserved_stub_cells"]) == 2
    assert cand["touched_hard_protected_cells"] == []

    assert res_on is not None and res_off is not None
    assert frozenset(res_on.transport_cells) == frozenset(res_off.transport_cells)
    assert all(role == "belt" for role in res_on.transport_cells.values())


def test_post_reclaim_pass3_gate_requires_commits_transport_and_net_save() -> None:
    base = {
        "post_reclaim_pass3_reruns_used": 0,
        "p4_reclaim_loop_successful_commits": 1,
        "p4_reclaim_loop_internal_transport_cumulative_added": 1,
        "pass3_internal_transport_saved": 2,
        "provisional_net_internal_transport_saved_after_reclaim": 1,
    }
    assert _post_reclaim_pass3_gate(dict(base)) == (True, None)
    assert _post_reclaim_pass3_gate({**base, "p4_reclaim_loop_successful_commits": 0}) == (
        False,
        "reclaim_commits_zero",
    )
    assert _post_reclaim_pass3_gate(
        {**base, "p4_reclaim_loop_internal_transport_cumulative_added": 0}
    ) == (
        False,
        "reclaim_internal_transport_not_added",
    )
    assert _post_reclaim_pass3_gate(
        {**base, "provisional_net_internal_transport_saved_after_reclaim": 0}
    ) == (
        False,
        "provisional_net_internal_transport_nonpositive",
    )
    assert _post_reclaim_pass3_gate(
        {**base, "provisional_net_internal_transport_saved_after_reclaim": None}
    ) == (
        False,
        "provisional_net_internal_transport_missing",
    )
    assert _post_reclaim_pass3_gate({**base, "post_reclaim_pass3_reruns_used": 1}) == (
        False,
        "max_post_reclaim_pass3_reruns_reached",
    )
    assert _post_reclaim_pass3_gate(dict(base), post_reclaim_reruns_lifetime_used=1) == (
        False,
        "max_post_reclaim_pass3_reruns_lifetime",
    )


def test_build_solver_timeline_sets_post_reclaim_skip_when_reclaim_did_not_commit() -> None:
    """§12.5: gate skips second Pass3 when reclaim loop made no successful commits."""

    from tests.unit.shapez_asteroid.test_pass1_timeline_integration import (
        _decoded_miners_with_belt_escape,
    )

    decoded = _decoded_miners_with_belt_escape()

    def fake_p4_loop(
        _map_before_pass3: list[dict],
        map_after_pass3_initial: list[dict],
        **kwargs: object,
    ) -> tuple[list[dict], dict]:
        _ = kwargs
        trace = {
            "p4_reclaim_shadow_enabled": True,
            "p4_reclaim_shadow_skip_reason": None,
            "p4_reclaim_candidate_count": 0,
            "p4_reclaim_accepted_shadow_count": 0,
            "p4_reclaim_rejected_shadow_count": 0,
            "p4_reclaim_internal_transport_budget": None,
            "p4_reclaim_internal_transport_projected_added": None,
            "p4_reclaim_best_candidate": None,
            "p4_reclaim_protected_corridor_source": None,
            "p4_reclaim_hard_protected_count": None,
            "p4_reclaim_soft_protected_count": None,
            "p4_reclaim_provisional_commit_attempted": False,
            "p4_reclaim_provisional_commit_committed": False,
            "p4_reclaim_provisional_commit_rollback_performed": False,
            "p4_reclaim_provisional_commit_rollback_reason": None,
            "p4_reclaim_selected_candidate": None,
            "p4_reclaim_selected_candidate_rank": None,
            "p4_reclaim_added_extractor_cells": [],
            "p4_reclaim_added_extension_cells": [],
            "p4_reclaim_added_stub_cells": [],
            "p4_reclaim_provisional_commit_skip_reason": None,
            "p4_reclaim_incremental_route_attempted": False,
            "p4_reclaim_incremental_route_committed": False,
            "p4_reclaim_incremental_route_rollback_performed": False,
            "p4_reclaim_incremental_route_rollback_reason": None,
            "p4_reclaim_incremental_route_skip_reason": None,
            "p4_reclaim_incremental_route_path_cells": None,
            "p4_reclaim_incremental_route_cells_added": [],
            "p4_reclaim_incremental_route_b2_internal_transport_added": None,
            "p4_reclaim_shadow_scan_limit": 16,
            "p4_reclaim_loop_max_iterations": 3,
            "p4_reclaim_loop_iterations_executed": 1,
            "p4_reclaim_loop_successful_commits": 0,
            "p4_reclaim_loop_internal_transport_cumulative_added": 0,
            "p4_reclaim_loop_terminated_reason": "no_accepted_shadow",
            "recovery_context_chain": [RECOVERY_SEGMENT_P4_RECLAIM],
        }
        return map_after_pass3_initial, trace

    pass3_calls: list[int] = []

    def counting_pass3(mm: list[dict], **kwargs: object) -> tuple:
        _ = kwargs
        pass3_calls.append(1)
        return run_pass3_transport_minimization_from_maps(mm, **kwargs)

    with (
        _patch_validation_recovery_attempts_zero(),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "run_p4_reclaim_loop_after_pass3",
            fake_p4_loop,
        ),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service."
            "run_pass3_transport_minimization_from_maps",
            counting_pass3,
        ),
    ):
        out = build_solver_timeline(decoded)
    ss = out["solver_summary"]
    assert len(pass3_calls) == 1
    assert ss.get("post_reclaim_pass3_skip_reason") == "reclaim_commits_zero"
    assert ss.get("post_reclaim_pass3_attempted") is False
    assert ss.get("post_reclaim_pass3_ran") is False
    assert isinstance(ss.get("baseline_internal_transport_at_reclaim_entry"), int)
    assert ss.get("net_internal_transport_saved_after_reclaim") == 0
    assert ss.get("p4_orchestration_entry_segment") == P4_ORCHESTRATION_ENTRY_SEGMENT_VALUE
    assert ss.get("recovery_trigger_reason") in (None, RECOVERY_TRIGGER_PASS3_CONNECTIVITY_BREAK)
    assert ss.get("recovery_context_chain") == [RECOVERY_SEGMENT_P4_RECLAIM]
    assert ss.get("recovery_terminal_reason") == "reclaim_commits_zero"


def _solver_summary_post_reclaim_gate_passes() -> tuple[dict[str, object], list[int]]:
    """Stub P4 with one reclaim commit; second Pass3 runs (for §12.5 / §13 tests)."""

    from tests.unit.shapez_asteroid.test_pass1_timeline_integration import (
        _decoded_miners_with_belt_escape,
    )

    decoded = _decoded_miners_with_belt_escape()

    def fake_p4_loop(
        _map_before_pass3: list[dict],
        map_after_pass3_initial: list[dict],
        **kwargs: object,
    ) -> tuple[list[dict], dict]:
        _ = kwargs
        trace = {
            "p4_reclaim_shadow_enabled": True,
            "p4_reclaim_shadow_skip_reason": None,
            "p4_reclaim_candidate_count": 1,
            "p4_reclaim_accepted_shadow_count": 1,
            "p4_reclaim_rejected_shadow_count": 0,
            "p4_reclaim_internal_transport_budget": 35,
            "p4_reclaim_internal_transport_projected_added": 1,
            "p4_reclaim_best_candidate": {"gain": 1.0, "rejected_reason": None},
            "p4_reclaim_protected_corridor_source": "pass3_trace",
            "p4_reclaim_hard_protected_count": 0,
            "p4_reclaim_soft_protected_count": 0,
            "p4_reclaim_provisional_commit_attempted": True,
            "p4_reclaim_provisional_commit_committed": True,
            "p4_reclaim_provisional_commit_rollback_performed": False,
            "p4_reclaim_provisional_commit_rollback_reason": None,
            "p4_reclaim_selected_candidate": None,
            "p4_reclaim_selected_candidate_rank": 0,
            "p4_reclaim_added_extractor_cells": [[10, 1]],
            "p4_reclaim_added_extension_cells": [],
            "p4_reclaim_added_stub_cells": [],
            "p4_reclaim_provisional_commit_skip_reason": None,
            "p4_reclaim_incremental_route_attempted": True,
            "p4_reclaim_incremental_route_committed": True,
            "p4_reclaim_incremental_route_rollback_performed": False,
            "p4_reclaim_incremental_route_rollback_reason": None,
            "p4_reclaim_incremental_route_skip_reason": None,
            "p4_reclaim_incremental_route_path_cells": None,
            "p4_reclaim_incremental_route_cells_added": [],
            "p4_reclaim_incremental_route_b2_internal_transport_added": 1,
            "p4_reclaim_shadow_scan_limit": 16,
            "p4_reclaim_loop_max_iterations": 3,
            "p4_reclaim_loop_iterations_executed": 2,
            "p4_reclaim_loop_successful_commits": 1,
            "p4_reclaim_loop_internal_transport_cumulative_added": 1,
            "p4_reclaim_loop_terminated_reason": "no_accepted_shadow",
            "recovery_context_chain": [
                RECOVERY_SEGMENT_P4_RECLAIM,
                RECOVERY_SEGMENT_SOFT_REPLACE_V2,
            ],
        }
        return map_after_pass3_initial, trace

    pass3_calls: list[int] = []
    pass3_invocation_index = {"n": 0}

    _p4_it_calls = {"n": 0}

    def _stub_internal_transport_count_for_p4_gate(
        mm: list[dict],
        *,
        is_external,
        **kwargs: object,
    ) -> int:
        from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import (
            solver_timeline as _st,
        )

        _p4_it_calls["n"] += 1
        v = int(_st._internal_transport_count_for_pass3_kind(mm, is_external=is_external, **kwargs))
        if _p4_it_calls["n"] == 2:
            return max(0, v - 1)
        return v

    def pass3_twice(mm: list[dict], **kwargs: object) -> tuple:
        pass3_calls.append(1)
        pass3_invocation_index["n"] += 1
        m, res, tr = run_pass3_transport_minimization_from_maps(mm, **kwargs)
        if pass3_invocation_index["n"] == 1 and not tr.get("pass3_skipped"):
            tr = dict(tr)
            cur = int(tr.get("pass3_internal_transport_saved") or 0)
            tr["pass3_internal_transport_saved"] = max(5, cur)
        return m, res, tr

    with (
        _patch_validation_recovery_attempts_zero(),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow."
            "run_p4_reclaim_loop_after_pass3",
            fake_p4_loop,
        ),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service."
            "run_pass3_transport_minimization_from_maps",
            pass3_twice,
        ),
        patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.p4_reclaim."
            "_internal_transport_count_for_pass3_kind",
            _stub_internal_transport_count_for_p4_gate,
        ),
    ):
        out = build_solver_timeline(decoded)
    return out["solver_summary"], pass3_calls


def test_solver_runs_post_reclaim_pass3_once_when_gate_passes() -> None:
    """§12.5: initial Pass3, stubbed P4 with one commit, then post-reclaim Pass3 (2 total calls)."""

    ss, pass3_calls = _solver_summary_post_reclaim_gate_passes()
    assert len(pass3_calls) == 2
    assert ss.get("p4_reclaim_loop_successful_commits") == 1
    assert ss.get("p4_reclaim_loop_internal_transport_cumulative_added") == 1
    assert ss.get("post_reclaim_pass3_reruns_used") == 1
    assert ss.get("post_reclaim_pass3_ran") is True
    assert ss.get("post_reclaim_pass3_attempted") is True
    assert isinstance(ss.get("baseline_internal_transport_at_reclaim_entry"), int)
    assert isinstance(ss.get("net_internal_transport_saved_after_reclaim"), int)
    assert ss.get("post_reclaim_pass3_before_count") == ss.get(
        "post_reclaim_pass3_before_internal_transport_count"
    )
    assert ss.get("post_reclaim_pass3_after_count") == ss.get(
        "post_reclaim_pass3_after_internal_transport_count"
    )
    assert ss.get("post_reclaim_pass3_delta") == (
        int(ss.get("post_reclaim_pass3_before_count") or 0)
        - int(ss.get("post_reclaim_pass3_after_count") or 0)
    )


def test_post_reclaim_pass3_keeps_recovery_context_chain() -> None:
    """§13: solver appends ``post_reclaim_pass3`` after P4 merge chain (stubbed trace)."""

    ss, _ = _solver_summary_post_reclaim_gate_passes()
    assert ss.get("p4_orchestration_entry_segment") == P4_ORCHESTRATION_ENTRY_SEGMENT_VALUE
    assert ss.get("recovery_trigger_reason") in (None, RECOVERY_TRIGGER_PASS3_CONNECTIVITY_BREAK)
    assert ss.get("recovery_context_chain") == [
        RECOVERY_SEGMENT_P4_RECLAIM,
        RECOVERY_SEGMENT_SOFT_REPLACE_V2,
        RECOVERY_SEGMENT_POST_RECLAIM_PASS3,
    ]
    assert ss.get("recovery_terminal_reason") == "post_reclaim_pass3_success"


def test_run_post_reclaim_pass3_once_greedy_local_replacement_telemetry_and_alias() -> None:
    """``p3_trace`` telemetry is copied under long and short ``post_reclaim_pass3_*`` keys."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import solver_service
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_timeline import (
        _run_post_reclaim_pass3_once,
    )

    lr: dict[str, object] = {
        "enabled": True,
        "attempted_count": 2,
        "accepted_count": 0,
        "rejected_by_path_len": 0,
        "rejected_by_disconnected_stub_limit": 0,
        "rejected_by_no_path": 0,
        "rejected_by_no_net_internal_gain": 1,
    }
    trace = {
        "pass3_skipped": True,
        "pass3_skip_reason": "fixture_skip",
        "pass3_greedy_local_replacement": lr,
    }

    def _fake_run(
        *_a: object,
        **_kw: object,
    ) -> tuple[list[dict[str, object]], object, dict[str, object]]:
        return ([], object(), trace)

    with patch.object(solver_service, "run_pass3_transport_minimization_from_maps", _fake_run):
        _map, out = _run_post_reclaim_pass3_once(
            [],
            final_mining_map=[],
            is_external=lambda _c: False,
        )
    assert _map == []
    assert out["post_reclaim_pass3_pass3_greedy_local_replacement"] == lr
    assert out["post_reclaim_pass3_greedy_local_replacement"] == lr


def test_apply_exception_summary_defaults_includes_greedy_local_replacement_keys() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline import (
        finalize as finalize_mod,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.pass3 import (
        initial_pass3_summary,
    )

    d: dict[str, object] = {}
    finalize_mod.apply_exception_summary_defaults(d)
    # Exception summary: hash/ELA seed keys come from solver_service._initial_summary_fields,
    # not duplicated via apply_exception_summary_defaults (D5 deletion group).
    assert "step_hash_step4" not in d
    assert "existing_layout_analysis" not in d
    assert "pass3_greedy_local_replacement" in d
    assert d["pass3_greedy_local_replacement"] is None
    assert "post_reclaim_pass3_greedy_local_replacement" in d
    assert d["post_reclaim_pass3_greedy_local_replacement"] is None
    assert "post_reclaim_pass3_pass3_greedy_local_replacement" in d
    assert d["post_reclaim_pass3_pass3_greedy_local_replacement"] is None
    assert (
        d["post_reclaim_pass3_greedy_local_replacement"]
        == d["post_reclaim_pass3_pass3_greedy_local_replacement"]
    )
    # D5-3: reclaim shadow diagnostics are produced by reclaim_shadow_scan, not exception defaults.
    assert "reclaim_anchor_candidate_count" not in d
    assert "reclaim_anchor_failure_samples" not in d
    assert "nearest_freed_cell_to_candidate_sample" not in d
    # D5-4: soft-replace payload from reclaim_soft_replace_trace, not exception defaults.
    assert "p4_soft_replace_old_cells" not in d
    assert "p4_soft_replace_new_cells" not in d
    assert "p4_soft_replace_selected_job_index" not in d

    p3 = initial_pass3_summary()
    assert "pass3_greedy_local_replacement" in p3
    assert p3.get("pass3_greedy_local_replacement") is None
