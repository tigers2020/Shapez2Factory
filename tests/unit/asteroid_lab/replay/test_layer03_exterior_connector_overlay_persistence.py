"""L3 runtime frames must retain L2 exterior connector observability."""

from __future__ import annotations

_CANDIDATE_KINDS = frozenset(
    {
        "candidate_miner",
        "candidate_transport_stub",
        "candidate_route_path",
    }
)


def _has_connector_overlay(frame: dict) -> bool:
    mv = frame.get("map_view") or {}
    for row in mv.get("overlay_cells") or []:
        if isinstance(row, dict) and row.get("overlay_role") == "planned_exterior_connector":
            return True
    return False


def _frames_with_plan() -> list[dict]:
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
        build_solver_runtime_replay_frames,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import golden_5x5_complete_map
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        exterior_plan_wire_for_golden,
        reconstruction_complete_lab_frame_dict_for_golden,
        rim_bundle_candidate_set_with_observability_for_golden,
    )

    return build_solver_runtime_replay_frames(
        complete_map=golden_5x5_complete_map(),
        lab_frames_before_append=[reconstruction_complete_lab_frame_dict_for_golden()],
        exterior_plan_wire=exterior_plan_wire_for_golden(),
        layer03=rim_bundle_candidate_set_with_observability_for_golden(),
        layer04=None,
    )


def test_l3_scan_begin_preserves_planned_exterior_connector_overlay() -> None:
    frames = _frames_with_plan()
    begin = next(f for f in frames if f["event_type"] == "layer03_rim_bundle_scan_begin")
    assert _has_connector_overlay(begin)


def test_l3_probe_window_preserves_connector_and_candidate_overlay() -> None:
    frames = _frames_with_plan()
    probe = next(
        f for f in frames if f["event_type"] == "layer03_rim_bundle_pool_probe_window"
    )
    assert _has_connector_overlay(probe)
    kinds = {
        str(c.get("kind"))
        for c in (probe.get("map_view") or {}).get("overlay_cells") or []
        if isinstance(c, dict)
    }
    assert kinds & _CANDIDATE_KINDS


def test_l3_runtime_frame_has_exterior_connector_plan_metrics() -> None:
    from django_apps.asteroid_lab.services.lab_timeline_exterior_connector_enrichment import (
        METRICS_KEY,
    )

    frames = _frames_with_plan()
    begin = next(f for f in frames if f["event_type"] == "layer03_rim_bundle_scan_begin")
    wire = (begin.get("metrics") or {}).get(METRICS_KEY)
    assert isinstance(wire, dict)
    assert isinstance(wire.get("planned_connectors"), list)


def test_l3_pool_summary_has_no_candidate_overlay_but_has_connector() -> None:
    frames = _frames_with_plan()
    summary = next(f for f in frames if f["event_type"] == "layer03_rim_bundle_pool_summary")
    overlay = summary["map_view"]["overlay_cells"]
    assert not any(
        isinstance(c, dict) and str(c.get("kind") or "") in _CANDIDATE_KINDS for c in overlay
    )
    assert _has_connector_overlay(summary)


def test_l4_placement_begin_preserves_planned_exterior_connector_overlay() -> None:
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
        build_solver_runtime_replay_frames,
    )
    from django_apps.asteroid_lab.services.lab_timeline_exterior_connector_enrichment import (
        METRICS_KEY,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import golden_5x5_complete_map
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        exterior_plan_wire_for_golden,
        layer04_result_with_selection_for_golden,
        reconstruction_complete_lab_frame_dict_for_golden,
        rim_bundle_candidate_set_with_observability_for_golden,
    )

    frames = build_solver_runtime_replay_frames(
        complete_map=golden_5x5_complete_map(),
        lab_frames_before_append=[reconstruction_complete_lab_frame_dict_for_golden()],
        exterior_plan_wire=exterior_plan_wire_for_golden(),
        layer03=rim_bundle_candidate_set_with_observability_for_golden(),
        layer04=layer04_result_with_selection_for_golden(),
    )
    begin = next(f for f in frames if f["event_type"] == "layer04_rim_placement_begin")
    assert _has_connector_overlay(begin)
    assert (begin.get("metrics") or {}).get(METRICS_KEY)
