"""P1-A outer placement wired into ``build_solver_timeline`` (service layer only)."""

from __future__ import annotations

from unittest.mock import patch

from django.test import override_settings

from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
    build_solver_timeline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
    trace_run_scope,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    external_predicate_for_mining_map,
)
from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline


def _decoded_miners_with_belt_escape() -> dict:
    entries: list[dict] = []
    for x in range(10, 13):
        entries.append({"X": x, "Y": 0, "T": "Layout_ShapeMiner"})
    for x in range(13, 30):
        entries.append({"X": x, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0})
    return {"BP": {"Entries": entries}}


def _decoded_ring_with_interior() -> dict:
    return {
        "BP": {
            "Entries": [
                {"X": 1, "Y": 1, "T": "Layout_ShapeMiner"},
                {"X": 2, "Y": 1, "T": "Layout_ShapeMiner"},
                {"X": 3, "Y": 1, "T": "Layout_ShapeMiner"},
                {"X": 1, "Y": 2, "T": "Layout_ShapeMiner"},
                {"X": 3, "Y": 2, "T": "Layout_ShapeMiner"},
                {"X": 1, "Y": 3, "T": "Layout_ShapeMiner"},
                {"X": 2, "Y": 3, "T": "Layout_ShapeMiner"},
                {"X": 3, "Y": 3, "T": "Layout_ShapeMiner"},
                {"X": 10, "Y": 2, "T": "Layout_UndergroundBelt", "R": 0},
            ]
        }
    }


def test_build_solver_timeline_runs_pass1_outer_mvp() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
        pass1_outer_placement as p1_mod,
    )

    calls: list[int] = []

    def wrapped(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(1)
        return p1_mod.run_pass1_outer_placement_mvp(**kwargs)

    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass1_timeline_integration."
        "run_pass1_outer_placement_mvp",
        wrapped,
    ):
        out = build_solver_timeline(_decoded_miners_with_belt_escape())
    assert sum(calls) == 1
    assert out["solver_summary"]["pass1_outer_placements"] >= 0


def test_build_solver_timeline_simple_map_has_extractors_and_stub_transport() -> None:
    out = build_solver_timeline(_decoded_miners_with_belt_escape())
    fc = out["solver_summary"]["final_counts"]
    ss = out["solver_summary"]
    baseline = ss["after_pass2_baseline_counts"]
    assert ss["pass12_phase"] == "post_pass2_mvp"
    assert ss["pass12_mixed_surface_skipped"] is False
    assert fc["extractors"] >= 1
    assert fc["transport_cells"] >= 1
    assert baseline["extractors"] == fc["extractors"]
    assert baseline["extensions"] == fc["extensions"]
    assert fc["transport_cells"] >= baseline["transport_cells"]
    assert ss["pass1_new_transport_cells"] >= 0
    assert ss["pass1_new_extractor_cells"] >= 0
    assert "pass2_internal_placements" in ss
    assert ss["pass2_new_extractor_cells"] >= 0
    ids = [f["id"] for f in out["solver_timeline"]]
    assert "solver_pass2_internal" in ids
    assert "solver_step4_routing" in ids
    assert "solver_pass3_transport" in ids
    assert "solver_after_pass2_proxy" not in ids
    pass1_frame = next(f for f in out["solver_timeline"] if f["id"] == "solver_pass1_outer")
    assert pass1_frame["summary"]["pass1_outer_placements"] >= 0
    assert "pass2_internal_placements" not in pass1_frame["summary"]
    pass2_frame = next(f for f in out["solver_timeline"] if f["id"] == "solver_pass2_internal")

    def _has_shape_miner(mining_map: list) -> bool:
        return any(
            r.get("layout_kind") == "miner" and isinstance(r.get("r"), int)
            for r in mining_map
            if r.get("role") == "occupied"
        )

    assert _has_shape_miner(pass1_frame["mining_map"]) or _has_shape_miner(
        pass2_frame["mining_map"]
    )
    belt_maps = (pass1_frame["mining_map"], pass2_frame["mining_map"])
    by_xy = {(r["x"], r["y"]): r for mp in belt_maps for r in mp if r.get("role") == "belt"}
    assert by_xy, "expected at least one belt cell after Pass1/Pass2"
    assert pass2_frame["summary"]["after_pass2_placement_counts"] == baseline
    assert "pass1_outer_placements" not in pass2_frame["summary"]
    for fid in (
        "solver_init",
        "solver_pass1_outer",
        "solver_pass2_internal",
        "solver_step4_routing",
        "solver_pass3_transport",
        "solver_validate",
    ):
        fr = next(f for f in out["solver_timeline"] if f["id"] == fid)
        assert fr["summary"]["pass12_phase"] == "post_pass2_mvp"
        assert fr["summary"]["pass12_skipped"] is False
        assert fr["summary"]["pass12_skip_reason"] is None
        assert fr["summary"]["pass12_mixed_surface_skipped"] is False


def test_build_solver_timeline_solver_init_includes_inferred_interior() -> None:
    out = build_solver_timeline(_decoded_ring_with_interior())
    init = next(f for f in out["solver_timeline"] if f["id"] == "solver_init")
    by_xy = {(r["x"], r["y"]): r for r in init["mining_map"]}
    assert by_xy.get((2, 2), {}).get("role") == "inferred"


def test_build_solver_timeline_route_impossible_no_pass1_residue() -> None:
    decoded = {"BP": {"Entries": [{"X": 4, "Y": 0, "T": "Layout_ShapeMiner"}]}}
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_bundle_commit."
        "bundle_route_probe_or_reject",
        return_value=False,
    ):
        out = build_solver_timeline(decoded)
    assert out["solver_summary"]["pass1_outer_placements"] == 0
    assert out["solver_summary"]["pass1_new_extractor_cells"] == 0
    assert out["solver_summary"]["pass1_new_transport_cells"] == 0
    assert out["solver_summary"]["pass1_new_extension_cells"] == 0
    assert out["solver_summary"]["pass2_internal_placements"] == 0
    assert out["solver_summary"]["pass2_new_extractor_cells"] == 0
    assert out["solver_summary"]["final_counts"]["extractors"] == 1


def test_build_solver_timeline_emits_solver_summary_once_with_pass1() -> None:
    msgs: list[str] = []

    def cap(_loc: str, msg: str, _data: dict | None = None) -> None:
        if msg == "solver_summary":
            msgs.append(msg)

    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace.trace_event",
        cap,
    ):
        with trace_run_scope():
            build_solver_timeline(_decoded_miners_with_belt_escape())
    assert msgs.count("solver_summary") == 1


def test_build_solver_timeline_final_validation_reports_geometry_connectivity() -> None:
    out = build_solver_timeline(_decoded_miners_with_belt_escape())
    fv = out["final_validation"]
    assert "geometry_valid" in fv and "connectivity_valid" in fv
    assert "overlap_violation_count" in fv and "missing_stub_count" in fv
    assert "extractor_count" in fv and "transport_cell_count" in fv
    assert "transport_connectivity_ok" in fv
    ss = out["solver_summary"]
    assert ss.get("existing_layout_analysis") is not None
    brv = ss.get("before_return_validate")
    assert isinstance(brv, dict)
    assert "hard_protected_count" in brv and "soft_protected_count" in brv
    assert "candidate_protected_corridor_count" in brv
    assert out.get("existing_layout_analysis") is ss.get("existing_layout_analysis")
    val_frame = next(f for f in out["solver_timeline"] if f["id"] == "solver_validate")
    assert val_frame["summary"].get("before_return_validate") == brv


def test_build_solver_timeline_solver_summary_trace_contract_keys() -> None:
    """Regression: STEP10 / NDJSON consumers rely on a stable ``solver_summary`` core."""

    out = build_solver_timeline(_decoded_miners_with_belt_escape())
    ss = out["solver_summary"]
    for key in (
        "run_id",
        "return_reason",
        "capacity_mode",
        "trunk_load",
        "existing_layout_analysis",
        "before_return_validate",
        "recovery_context_chain",
        "recovery_trigger_reason",
        "p4_orchestration_entry_segment",
        "recovery_terminal_reason",
        "recovery_action_plan",
        "recovery_contract_phases",
        "optimization_baseline_internal_transport",
        "solver_state_hash",
        "step_hash_step4",
        "step_hash_pass3",
        "step_hash_p4",
    ):
        assert key in ss
    assert ss["capacity_mode"] == "accumulate_only"
    tl = ss["trunk_load"]
    assert isinstance(tl, dict) and tl.get("mode") == "accumulate_only"
    val_frame = next(f for f in out["solver_timeline"] if f["id"] == "solver_validate")
    for key in (
        "recovery_context_chain",
        "recovery_trigger_reason",
        "p4_orchestration_entry_segment",
        "recovery_terminal_reason",
        "before_return_validate",
    ):
        assert key in val_frame["summary"]


def test_build_solver_timeline_step_hashes_stable_across_two_runs() -> None:
    """동일 입력으로 두 번 실행해도 단계·최종 상태 해시가 같아야 한다 (결정론)."""

    decoded = _decoded_miners_with_belt_escape()
    sa = build_solver_timeline(decoded)["solver_summary"]
    sb = build_solver_timeline(decoded)["solver_summary"]
    for key in (
        "solver_state_hash",
        "step_hash_step4",
        "step_hash_pass3",
        "step_hash_p4",
    ):
        assert sa[key] == sb[key], key


def _replay_events_without_txn_ids(events: list) -> list:
    """``transaction_id``는 실행마다 달라질 수 있으므로 결정론 비교에서 제외한다."""

    out: list = []
    for e in events:
        if not isinstance(e, dict):
            out.append(e)
            continue
        e2 = dict(e)
        pl = e2.get("payload")
        if isinstance(pl, dict):
            e2["payload"] = {
                k: v for k, v in pl.items() if k not in ("transaction_id", "parent_txn_id")
            }
        out.append(e2)
    return out


def test_build_solver_timeline_replay_snapshot_stable_across_two_runs() -> None:
    """프레임 순서·요약 키 집합은 run_id 외 결정론이어야 한다 (replay contract)."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation import (
        constants as frame_ids,
    )

    order = frame_ids.SOLVER_TIMELINE_FRAME_ORDER

    decoded = _decoded_miners_with_belt_escape()
    ra = build_solver_timeline(decoded)["solver_replay"]
    rb = build_solver_timeline(decoded)["solver_replay"]
    assert ra["frame_order"] == list(order)
    assert rb["frame_order"] == list(order)
    for k in ("contract_version", "frame_order", "frames"):
        assert ra[k] == rb[k], k
    assert _replay_events_without_txn_ids(ra["events"]) == _replay_events_without_txn_ids(
        rb["events"]
    )


def test_pass2_zero_placements_pass1_frame_equals_pass2_mining_map() -> None:
    """When Pass2 commits nothing, post-Pass1 merged map matches post-Pass2 (no Pass2 delta)."""

    def _pass2_noop(**_kwargs):  # type: ignore[no-untyped-def]
        return 0

    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass1_timeline_integration."
        "run_pass2_internal_placement_mvp",
        _pass2_noop,
    ):
        out = build_solver_timeline(_decoded_miners_with_belt_escape())
    assert out["solver_summary"]["pass2_internal_placements"] == 0
    p1 = next(f for f in out["solver_timeline"] if f["id"] == "solver_pass1_outer")["mining_map"]
    p2 = next(f for f in out["solver_timeline"] if f["id"] == "solver_pass2_internal")["mining_map"]
    assert p1 == p2


def test_build_solver_timeline_pass12_phase_skipped_mixed_surface_from_stats() -> None:
    """``pass12_phase`` reflects MVP mixed-surface guard when Pass12 reports skip."""

    wm_snapshot: list[dict] = []

    def fake_integrate(  # noqa: ARG001
        *,
        working_map,
        final_mining_map,
        is_external,
        existing_layout_analysis=None,
        **kwargs: object,
    ):
        wm_snapshot[:] = working_map
        c = [dict(r) for r in working_map]
        stats = {
            "pass1_outer_placements": 0,
            "pass1_new_extractor_cells": 0,
            "pass1_new_extension_cells": 0,
            "pass1_preserved_transport_cells": 0,
            "pass1_new_transport_cells": 0,
            "pass1_total_transport_cells_after": 0,
            "pass2_internal_placements": 0,
            "pass2_new_extractor_cells": 0,
            "pass2_new_extension_cells": 0,
            "pass2_new_transport_cells": 0,
            "pass12_skipped": True,
            "pass12_skip_reason": "mixed_surface",
            "pass12_mixed_surface_skipped": True,
            "placement_records": {},
            "existing_layout_source_kind": None,
            "existing_layout_hint_coord_count": 0,
            "existing_layout_barrier_cell_count": 0,
        }
        return c, c, stats

    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass1_timeline_integration."
        "integrate_pass12_placement_into_working_map",
        fake_integrate,
    ):
        out = build_solver_timeline(_decoded_miners_with_belt_escape())
    ss = out["solver_summary"]
    assert ss["pass12_phase"] == "skipped_mixed_surface_mvp"
    assert ss["pass12_skipped"] is True
    assert ss["pass12_skip_reason"] == "mixed_surface"
    assert ss["pass12_mixed_surface_skipped"] is True
    assert ss["step4_skipped"] is True
    assert wm_snapshot, "integrate should receive working_map"
    for fid in (
        "solver_init",
        "solver_pass1_outer",
        "solver_pass2_internal",
        "solver_step4_routing",
        "solver_pass3_transport",
        "solver_validate",
    ):
        fr = next(f for f in out["solver_timeline"] if f["id"] == fid)
        assert fr["summary"]["pass12_phase"] == "skipped_mixed_surface_mvp"
        assert fr["summary"]["pass12_skipped"] is True
        assert fr["summary"]["pass12_skip_reason"] == "mixed_surface"
        assert fr["summary"]["pass12_mixed_surface_skipped"] is True
        if fid == "solver_step4_routing":
            assert fr["summary"]["step4_skipped"] is True
            assert fr["summary"]["step4_route_count"] == 0
        if fid == "solver_pass3_transport":
            assert fr["summary"].get("p3e2_shadow_would_commit") is False
            assert fr["summary"].get("p3e2_shadow_rejected_reason") == "pass3_not_eligible"
            assert "p3e2_outlet_count" in fr["summary"]
            assert fr["summary"].get("p3e3_guarded_rejected_reason") == "pass3_not_eligible"
            assert "p3e3_guarded_commit_enabled" in fr["summary"]


def test_integrate_pass12_skips_when_mixed_shape_and_fluid_surface() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
        pass1_timeline_integration as p12_tl,
    )

    wm = [{"x": 1, "y": 0, "role": "belt", "surface": "shape"}]
    fm = [
        {"x": 10, "y": 0, "role": "inferred", "surface": "shape"},
        {"x": 11, "y": 0, "role": "inferred", "surface": "fluid"},
    ]

    m1, m2, stats = p12_tl.integrate_pass12_placement_into_working_map(
        working_map=wm,
        final_mining_map=fm,
        is_external=lambda _: False,
    )
    assert stats["pass12_skipped"] is True
    assert stats["pass12_skip_reason"] == "mixed_surface"
    assert stats["pass12_mixed_surface_skipped"] is True
    assert stats["pass1_outer_placements"] == 0
    assert m1 == wm and m2 == wm


def test_integrate_pass1_outer_alias_matches_pass12_final_map() -> None:
    """Deprecated alias: same merged map/stats as Pass12 (post-Pass2), not Pass1-only."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
        pass1_timeline_integration as p12_tl,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
        external_predicate_for_decoded,
    )

    decoded = _decoded_miners_with_belt_escape()
    is_ext = external_predicate_for_decoded(decoded)
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    legacy_map, legacy_stats = p12_tl.integrate_pass1_outer_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    _, full_map, full_stats = p12_tl.integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    assert legacy_map == full_map
    assert legacy_stats == full_stats


def test_integrate_pass12_scratch_subset_assert_runs_when_settings_enabled() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
        pass1_timeline_integration as p12_tl,
    )

    decoded = _decoded_miners_with_belt_escape()
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])

    with override_settings(SHAPEZ_MINING_ASSERT_SCRATCH_TRANSPORT_SUBSET=True):
        _m1, _m2, stats = p12_tl.integrate_pass12_placement_into_working_map(
            working_map=wm,
            final_mining_map=fm,
            is_external=is_ext,
        )
    assert stats.get("pass12_skipped") is not True


def test_integrate_pass12_records_existing_layout_meta_and_pass2_barriers() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
        pass1_timeline_integration as p12_tl,
    )

    fm = [
        {
            "x": 5,
            "y": 5,
            "role": "inferred",
            "layout_kind": "asteroid_field",
            "surface": "shape",
        },
    ]
    wm = [dict(r) for r in fm]
    ela = {
        "source_kind": "existing_shape_layout",
        "solver_hints": {
            "trunk_seed_cell_union": [],
            "cleanup_candidate_cell_union": [[5, 5]],
        },
    }
    _m1, _m2, stats = p12_tl.integrate_pass12_placement_into_working_map(
        working_map=wm,
        final_mining_map=fm,
        is_external=lambda c: c[0] > 20,
        existing_layout_analysis=ela,
    )
    assert stats["existing_layout_source_kind"] == "existing_shape_layout"
    assert stats["existing_layout_hint_coord_count"] == 1
    assert stats["existing_layout_barrier_cell_count"] == 1


def test_build_solver_timeline_pass12_summary_includes_existing_layout_trace_fields() -> None:
    out = build_solver_timeline(_decoded_miners_with_belt_escape())
    ss = out["solver_summary"]
    assert "existing_layout_source_kind" in ss
    assert "existing_layout_hint_coord_count" in ss
    assert "existing_layout_barrier_cell_count" in ss
    assert isinstance(ss["existing_layout_hint_coord_count"], int)
    validate = next(f for f in out["solver_timeline"] if f["id"] == "solver_validate")
    summ = validate["summary"]
    assert "recovery_context_chain" in summ
    assert "before_return_validate" in summ
    assert isinstance(summ["before_return_validate"], dict)
    assert "capacity_mode" not in summ  # capacity lives on solver_summary / trunk_load
    assert ss.get("capacity_mode") == "accumulate_only"
    assert ss.get("existing_layout_analysis") is not None


def test_integrate_pass12_emits_pass2_spine_seed_count_observation() -> None:
    """Phase B: Pass2 spine seeds are observed (no behavior change), exposed in stats.

    `documents/Algorithm/mining_solver_cursor_sessions/07_step3_pass2_placement.md` §8 Pass2
    spine은 extension-인접 void 셀을 후보 시드로 본다. Pass1 종료 직후·Pass2 진입 전에
    `spine_seed_voids_adjacent_extensions`를 호출하고 카운트만 ``pass2_spine_seed_count``로
    노출한다(배치는 변경하지 않음).
    """

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
        pass1_timeline_integration as p12_tl,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
        external_predicate_for_decoded,
    )

    decoded = _decoded_miners_with_belt_escape()
    is_ext = external_predicate_for_decoded(decoded)
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]

    spine_calls: list[int] = []

    def wrapped_spine(buildings, asteroid_cells):  # type: ignore[no-untyped-def]
        spine_calls.append(len(buildings))
        from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
            pass2_spine,
        )

        return pass2_spine.spine_seed_voids_adjacent_extensions(buildings, asteroid_cells)

    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.placement."
        "pass1_timeline_integration.spine_seed_voids_adjacent_extensions",
        wrapped_spine,
    ):
        _m1, _m2, stats = p12_tl.integrate_pass12_placement_into_working_map(
            working_map=wm, final_mining_map=fm, is_external=is_ext
        )

    assert "pass2_spine_seed_count" in stats
    assert isinstance(stats["pass2_spine_seed_count"], int)
    assert stats["pass2_spine_seed_count"] >= 0
    assert spine_calls == [stats["pass1_new_extension_cells"]]


def test_build_solver_timeline_summary_includes_pass2_spine_seed_count() -> None:
    """``pass2_spine_seed_count``가 ``solver_summary``로 전파된다."""

    out = build_solver_timeline(_decoded_miners_with_belt_escape())
    ss = out["solver_summary"]
    assert "pass2_spine_seed_count" in ss
    assert isinstance(ss["pass2_spine_seed_count"], int)
    assert ss["pass2_spine_seed_count"] >= 0


def test_integrate_pass12_pass2_spine_priority_off_on_ab() -> None:
    """A/B 토글: OFF는 디폴트(기존 동일), ON은 시드 있을 때만 ``pass2_spine_priority_applied=True``.

    geometry/카운트 계약은 유지되고 토글 키만 달라진다.
    """

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
        pass1_timeline_integration as p12_tl,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
        external_predicate_for_decoded,
    )

    decoded = _decoded_miners_with_belt_escape()
    is_ext = external_predicate_for_decoded(decoded)
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]

    _m1_off, _m2_off, stats_off = p12_tl.integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    _m1_on, _m2_on, stats_on = p12_tl.integrate_pass12_placement_into_working_map(
        working_map=wm,
        final_mining_map=fm,
        is_external=is_ext,
        pass2_spine_priority_enabled=True,
    )

    assert stats_off["pass2_spine_priority_applied"] is False
    expected_on = stats_on["pass2_spine_seed_count"] > 0
    assert stats_on["pass2_spine_priority_applied"] is expected_on

    for k in ("pass2_spine_seed_count", "pass1_outer_placements", "pass12_skipped"):
        assert k in stats_off and k in stats_on


def test_integrate_pass12_skip_path_keeps_pass2_spine_seed_count_zero() -> None:
    """Mixed surface skip 시에도 ``pass2_spine_seed_count``가 0으로 노출된다."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
        pass1_timeline_integration as p12_tl,
    )

    wm = [{"x": 1, "y": 0, "role": "belt", "surface": "shape"}]
    fm = [
        {"x": 10, "y": 0, "role": "inferred", "surface": "shape"},
        {"x": 11, "y": 0, "role": "inferred", "surface": "fluid"},
    ]
    _m1, _m2, stats = p12_tl.integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=lambda _: False
    )
    assert stats["pass12_mixed_surface_skipped"] is True
    assert stats["pass2_spine_seed_count"] == 0
