"""Central solver runtime replay assembler tests."""

from __future__ import annotations


def test_layer03_event_types_registered() -> None:
    from django_apps.asteroid_lab.replay.event_types import (
        EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW,
        EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_SUMMARY,
        EVENT_TYPE_LAYER03_RIM_BUNDLE_SCAN_BEGIN,
        EVENT_TYPE_LAYER03_RIM_BUNDLE_SCAN_COMPLETE,
        SNAPSHOT_EVENT_TYPES,
        is_registered_event_type,
    )

    for wire in (
        EVENT_TYPE_LAYER03_RIM_BUNDLE_SCAN_BEGIN,
        EVENT_TYPE_LAYER03_RIM_BUNDLE_SCAN_COMPLETE,
        EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_SUMMARY,
        EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW,
    ):
        assert wire in SNAPSHOT_EVENT_TYPES
        assert is_registered_event_type(wire)


def test_decoded_cell_row_round_trip_preserves_kind_and_transport() -> None:
    from django_apps.asteroid_lab.replay.layer02_segment import _decoded_cell_to_row
    from django_apps.asteroid_lab.replay.timeline_serialization import (
        replay_map_view_from_json_dict,
    )
    from django_apps.asteroid_lab.services.dto import DecodedCellDTO

    sample = DecodedCellDTO(
        x=3,
        y=4,
        layer=None,
        rotation=0,
        tile_type="",
        cell_kind="asteroid_shape_field",
        transport_kind="shape_belt",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={},
    )
    row = _decoded_cell_to_row(sample)
    map_view = replay_map_view_from_json_dict(
        {
            "full_cells": [row],
            "overlay_cells": [],
            "cell_delta": [],
            "annotations": [],
            "bbox": {"min_x": 3, "min_y": 4, "max_x": 3, "max_y": 4},
        }
    )
    cell = map_view.full_cells[0]
    assert cell.kind == "asteroid_shape_field"
    assert cell.transport == "shape_belt"


def test_cell_from_dict_accepts_cell_kind_aliases() -> None:
    from django_apps.asteroid_lab.replay.timeline_serialization import (
        replay_map_view_from_json_dict,
    )

    map_view = replay_map_view_from_json_dict(
        {
            "full_cells": [
                {
                    "x": 1,
                    "y": 2,
                    "cell_kind": "asteroid_shape_field",
                    "transport_kind": "shape_belt",
                    "rotation": 0,
                }
            ],
            "overlay_cells": [],
            "cell_delta": [],
            "annotations": [],
            "bbox": {"min_x": 1, "min_y": 2, "max_x": 1, "max_y": 2},
        }
    )
    assert map_view.full_cells[0].kind == "asteroid_shape_field"
    assert map_view.full_cells[0].transport == "shape_belt"


def test_layer02_segment_matches_legacy_timeline_wire() -> None:
    from django_apps.asteroid_lab.replay.layer02_segment import (
        build_layer02_exterior_transport_frame,
        build_layer02_timeline_frame_wire_dict,
    )
    from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType
    from django_apps.asteroid_lab.replay.timeline_dtos import replay_map_view_is_renderable
    from django_apps.asteroid_lab.services.lab_layer02_timeline import (
        build_layer02_timeline_frame_dict,
    )
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        exterior_plan_wire_for_golden,
        golden_complete_map,
        reconstruction_complete_lab_frame_dict_for_golden,
    )

    plan_wire = exterior_plan_wire_for_golden()
    complete = golden_complete_map()
    source = reconstruction_complete_lab_frame_dict_for_golden()
    legacy = build_layer02_timeline_frame_dict(
        plan_wire=plan_wire,
        source_frame=source,
        complete_map=complete,
    )
    wire = build_layer02_timeline_frame_wire_dict(
        plan_wire=plan_wire,
        source_frame=source,
        complete_map=complete,
    )
    assert wire == legacy

    frame = build_layer02_exterior_transport_frame(
        plan_wire=plan_wire,
        source_frame=source,
        complete_map=complete,
    )
    assert frame.event_type is ReplayEventType.EXTERIOR_TRANSPORT_COMPLETED
    assert replay_map_view_is_renderable(frame.map_view)
    assert len(frame.map_view.overlay_cells) >= 1


def test_assembler_emits_l2_only_when_plan_wire_present() -> None:
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
        build_solver_runtime_replay_frames,
    )
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        exterior_plan_wire_for_golden,
        golden_complete_map,
        reconstruction_complete_lab_frame_dict_for_golden,
    )

    frames = build_solver_runtime_replay_frames(
        complete_map=golden_complete_map(),
        lab_frames_before_append=[reconstruction_complete_lab_frame_dict_for_golden()],
        exterior_plan_wire=exterior_plan_wire_for_golden(),
        layer03=None,
        layer04=None,
    )
    types = [f["event_type"] for f in frames]
    assert types == ["exterior_transport.completed"]


def test_assembler_skips_l2_when_exterior_plan_wire_none() -> None:
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
        build_solver_runtime_replay_frames,
    )
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        golden_complete_map,
        reconstruction_complete_lab_frame_dict_for_golden,
    )

    frames = build_solver_runtime_replay_frames(
        complete_map=golden_complete_map(),
        lab_frames_before_append=[reconstruction_complete_lab_frame_dict_for_golden()],
        exterior_plan_wire=None,
        layer03=None,
        layer04=None,
    )
    assert frames == []


def test_assembler_emits_l2_then_l4_when_layer04_present() -> None:
    from django_apps.asteroid_lab.replay.event_types import (
        EVENT_TYPE_LAYER04_RIM_PLACEMENT_BEGIN,
        EVENT_TYPE_LAYER04_RIM_PLACEMENT_COMPLETE,
    )
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
        build_solver_runtime_replay_frames,
    )
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        exterior_plan_wire_for_golden,
        golden_complete_map,
        layer04_result_with_selection_for_golden,
        reconstruction_complete_lab_frame_dict_for_golden,
    )

    layer04 = layer04_result_with_selection_for_golden()
    frames = build_solver_runtime_replay_frames(
        complete_map=golden_complete_map(),
        lab_frames_before_append=[reconstruction_complete_lab_frame_dict_for_golden()],
        exterior_plan_wire=exterior_plan_wire_for_golden(),
        layer03=None,
        layer04=layer04,
    )
    types = [f["event_type"] for f in frames]
    assert types[0] == "exterior_transport.completed"
    assert EVENT_TYPE_LAYER04_RIM_PLACEMENT_BEGIN in types
    assert types[-1] == EVENT_TYPE_LAYER04_RIM_PLACEMENT_COMPLETE


def test_assembler_emits_l3_begin_after_l2_when_plan_wire_present() -> None:
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
        build_solver_runtime_replay_frames,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import golden_5x5_complete_map
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        exterior_plan_wire_for_golden,
        reconstruction_complete_lab_frame_dict_for_golden,
        rim_bundle_candidate_set_with_observability_for_golden,
    )

    frames = build_solver_runtime_replay_frames(
        complete_map=golden_5x5_complete_map(),
        lab_frames_before_append=[reconstruction_complete_lab_frame_dict_for_golden()],
        exterior_plan_wire=exterior_plan_wire_for_golden(),
        layer03=rim_bundle_candidate_set_with_observability_for_golden(),
        layer04=None,
    )
    types = [f["event_type"] for f in frames]
    assert types.index("layer03_rim_bundle_scan_begin") > types.index(
        "exterior_transport.completed"
    )


def test_assembler_skips_l2_completed_when_exterior_plan_wire_none() -> None:
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
        build_solver_runtime_replay_frames,
    )
    from django_apps.asteroid_lab.replay.timeline_dtos import replay_map_view_is_renderable
    from django_apps.asteroid_lab.replay.timeline_serialization import (
        replay_map_view_from_json_dict,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import golden_5x5_complete_map
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        reconstruction_complete_lab_frame_dict_for_golden,
        rim_bundle_candidate_set_missing_exterior_plan,
    )

    frames = build_solver_runtime_replay_frames(
        complete_map=golden_5x5_complete_map(),
        lab_frames_before_append=[reconstruction_complete_lab_frame_dict_for_golden()],
        exterior_plan_wire=None,
        layer03=rim_bundle_candidate_set_missing_exterior_plan(),
        layer04=None,
    )
    types = [f["event_type"] for f in frames]
    assert "exterior_transport.completed" not in types

    begin = next(f for f in frames if f["event_type"] == "layer03_rim_bundle_scan_begin")
    assert begin["map_view"]["full_cells"]
    assert replay_map_view_is_renderable(replay_map_view_from_json_dict(begin["map_view"]))

    complete = next(f for f in frames if f["event_type"] == "layer03_rim_bundle_scan_complete")
    assert complete["metrics"]["layer03_skip_reason"] == "missing_exterior_connection_plan"


def test_layer03_pool_summary_has_no_candidate_overlay_but_has_connector() -> None:
    from django_apps.asteroid_lab.replay.event_types import (
        EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_SUMMARY,
    )
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
        build_solver_runtime_replay_frames,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import golden_5x5_complete_map
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        exterior_plan_wire_for_golden,
        reconstruction_complete_lab_frame_dict_for_golden,
        rim_bundle_candidate_set_with_observability_for_golden,
    )

    candidate_kinds = frozenset(
        {
            "candidate_miner",
            "candidate_transport_stub",
            "candidate_route_path",
        }
    )

    candidate_set = rim_bundle_candidate_set_with_observability_for_golden()
    assert candidate_set.observability.replay_pool_candidates

    frames = build_solver_runtime_replay_frames(
        complete_map=golden_5x5_complete_map(),
        lab_frames_before_append=[reconstruction_complete_lab_frame_dict_for_golden()],
        exterior_plan_wire=exterior_plan_wire_for_golden(),
        layer03=candidate_set,
        layer04=None,
    )
    summary = next(
        f for f in frames if f["event_type"] == EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_SUMMARY
    )
    overlay = summary["map_view"]["overlay_cells"]
    assert not any(
        isinstance(c, dict) and str(c.get("kind") or "") in candidate_kinds for c in overlay
    )
    assert any(
        isinstance(c, dict) and c.get("overlay_role") == "planned_exterior_connector"
        for c in overlay
    )
    assert summary["metrics"]["logical_window_count"] >= 1
    assert summary["metrics"]["shows_all_candidates"] is True
    assert summary["metrics"]["pool_preview_overlay_mode"] == "candidate_observation"


def test_layer03_probe_windows_cover_full_replay_pool_by_candidate_ids() -> None:
    from django_apps.asteroid_lab.replay.event_types import (
        EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW,
    )
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
        build_solver_runtime_replay_frames,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import golden_5x5_complete_map
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        exterior_plan_wire_for_golden,
        reconstruction_complete_lab_frame_dict_for_golden,
        rim_bundle_candidate_set_with_observability_for_golden,
    )

    candidate_set = rim_bundle_candidate_set_with_observability_for_golden()
    expected_ids = [
        entry.candidate.candidate_id for entry in candidate_set.observability.replay_pool_candidates
    ]
    frames = build_solver_runtime_replay_frames(
        complete_map=golden_5x5_complete_map(),
        lab_frames_before_append=[reconstruction_complete_lab_frame_dict_for_golden()],
        exterior_plan_wire=exterior_plan_wire_for_golden(),
        layer03=candidate_set,
        layer04=None,
    )
    window_frames = [
        f for f in frames if f["event_type"] == EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW
    ]
    assert window_frames

    seen_ids = [cid for fr in window_frames for cid in fr["metrics"]["candidate_ids"]]

    assert seen_ids == expected_ids
    assert len(seen_ids) == len(set(seen_ids))

    for fr in window_frames:
        metrics = fr["metrics"]
        assert metrics["candidate_count_in_window"] == len(metrics["candidate_ids"])
        assert metrics["candidate_start_index"] <= metrics["candidate_end_index"]

    from django_apps.asteroid_lab.replay.pattern_bundle_highlight import METRICS_KEY

    multi_candidates = [
        fr for fr in window_frames if len((fr.get("metrics") or {}).get("candidate_ids") or []) >= 2
    ]
    if multi_candidates:
        highlights = (multi_candidates[0].get("metrics") or {}).get(METRICS_KEY)
        assert isinstance(highlights, dict)
        bundles = highlights.get("bundles")
        assert isinstance(bundles, list) and len(bundles) >= 2
        color_indices = {b["color_index"] for b in bundles}
        assert len(color_indices) >= 2


def test_assembler_l3_probe_windows_follow_summary() -> None:
    from django_apps.asteroid_lab.replay.event_types import (
        EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW,
        EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_SUMMARY,
    )
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
        build_solver_runtime_replay_frames,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import golden_5x5_complete_map
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        exterior_plan_wire_for_golden,
        reconstruction_complete_lab_frame_dict_for_golden,
        rim_bundle_candidate_set_with_observability_for_golden,
    )

    frames = build_solver_runtime_replay_frames(
        complete_map=golden_5x5_complete_map(),
        lab_frames_before_append=[reconstruction_complete_lab_frame_dict_for_golden()],
        exterior_plan_wire=exterior_plan_wire_for_golden(),
        layer03=rim_bundle_candidate_set_with_observability_for_golden(),
        layer04=None,
    )
    types = [f["event_type"] for f in frames]
    assert types.index(EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_SUMMARY) < types.index(
        EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW
    )


def test_assembler_prefers_transport_routing_segment_over_legacy_rim_placement() -> None:
    from django_apps.asteroid_lab.replay.event_types import (
        EVENT_TYPE_LAYER04_RIM_PLACEMENT_BEGIN,
        EVENT_TYPE_LAYER05_TRANSPORT_ROUTING_BEGIN,
    )
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
        build_solver_runtime_replay_frames,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import golden_5x5_complete_map
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        exterior_plan_wire_for_golden,
        layer04_result_with_selection_for_golden,
        layer04_route_plan_with_transport_tiles_for_golden,
        reconstruction_complete_lab_frame_dict_for_golden,
        rim_bundle_candidate_set_with_observability_for_golden,
    )

    frames = build_solver_runtime_replay_frames(
        complete_map=golden_5x5_complete_map(),
        lab_frames_before_append=[reconstruction_complete_lab_frame_dict_for_golden()],
        exterior_plan_wire=exterior_plan_wire_for_golden(),
        layer03=rim_bundle_candidate_set_with_observability_for_golden(),
        layer04=layer04_result_with_selection_for_golden(),
        layer05_route_plan=layer04_route_plan_with_transport_tiles_for_golden(),
    )
    types = [str(f["event_type"]) for f in frames]
    assert EVENT_TYPE_LAYER05_TRANSPORT_ROUTING_BEGIN in types
    assert EVENT_TYPE_LAYER04_RIM_PLACEMENT_BEGIN not in types
    kinds = {
        row.get("kind")
        for f in frames
        for row in (f.get("map_view") or {}).get("overlay_cells") or []
    }
    assert "route_probe_path" not in kinds
    assert any(str(k).startswith("space_") for k in kinds if k)


def test_l4_segment_does_not_inherit_l3_candidate_overlay() -> None:
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
        build_solver_runtime_replay_frames,
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

    l4_frames = [f for f in frames if str(f["event_type"]).startswith("layer04_")]

    for fr in l4_frames:
        map_view = fr["map_view"]
        inherited = [
            row
            for row in (map_view.get("full_cells") or []) + (map_view.get("overlay_cells") or [])
            if str(row.get("kind", "")).startswith("candidate_")
        ]
        assert inherited == []


def test_replay_limits_layer03_pool_preview_windows_constant() -> None:
    from django_apps.asteroid_lab.replay.replay_limits import (
        LAYER03_REPLAY_MAX_POOL_PREVIEW_WINDOWS,
        MAX_LAYER04_REPLAY_SELECTED,
    )

    assert LAYER03_REPLAY_MAX_POOL_PREVIEW_WINDOWS == 10
    assert MAX_LAYER04_REPLAY_SELECTED == 32


def test_layer03_probe_window_event_type_registered() -> None:
    from django_apps.asteroid_lab.replay.event_types import (
        EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW,
        SNAPSHOT_EVENT_TYPES,
        is_registered_event_type,
    )
    from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType

    assert EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW in SNAPSHOT_EVENT_TYPES
    assert is_registered_event_type(EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW)
    assert (
        ReplayEventType.LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW.value
        == EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW
    )
