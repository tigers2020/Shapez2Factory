"""Central solver runtime replay assembler tests."""

from __future__ import annotations


def test_layer03_event_types_registered() -> None:
    from django_apps.asteroid_lab.replay.event_types import (
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
    from django_apps.asteroid_lab.layers.contracts.candidates import (
        Layer03ExpansionMetrics,
        build_rim_bundle_candidate_set,
    )
    from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
    from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.run import (
        run_layer_04_rim_bundle_placement,
    )
    from django_apps.asteroid_lab.replay.event_types import (
        EVENT_TYPE_LAYER04_RIM_PLACEMENT_BEGIN,
        EVENT_TYPE_LAYER04_RIM_PLACEMENT_COMPLETE,
    )
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
        build_solver_runtime_replay_frames,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
        minimal_l2_plan_for_golden,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
        succeeded_probe_at,
    )
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        exterior_plan_wire_for_golden,
        golden_complete_map,
        reconstruction_complete_lab_frame_dict_for_golden,
    )

    entry = succeeded_probe_at((6, 4))
    candidate_set = build_rim_bundle_candidate_set(
        normal_candidates=(entry,),
        diagnostic_rejected_candidates=(),
        metrics=Layer03ExpansionMetrics(
            rim_anchor_count=1,
            seed_projection_attempt_count=0,
            local_geometry_rejected_count=0,
            route_probe_attempt_count=1,
            route_probe_succeeded_count=1,
            route_probe_failed_count=0,
            dedupe_duplicate_count=0,
            normal_candidate_count=1,
            diagnostic_rejected_count=0,
            budget_skipped_count=0,
            layer_skip_reason=Layer03ExpansionMetrics.empty().layer_skip_reason,
        ),
    )
    layer04 = run_layer_04_rim_bundle_placement(
        complete_map=golden_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        candidate_set=candidate_set,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
    )
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


def test_replay_limits_layer03_top_n_constant() -> None:
    from django_apps.asteroid_lab.replay.replay_limits import (
        LAYER03_REPLAY_TOP_N,
        MAX_LAYER04_REPLAY_SELECTED,
    )

    assert LAYER03_REPLAY_TOP_N == 8
    assert MAX_LAYER04_REPLAY_SELECTED == 32
