"""Layer 04 inner pattern fill replay segment tests."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.event_types import (
    EVENT_TYPE_LAYER04_INNER_PATTERN_FILL_BEGIN,
    EVENT_TYPE_LAYER04_INNER_PATTERN_FILL_COMPLETE,
    is_registered_event_type,
)
from django_apps.asteroid_lab.replay.layer04_inner_pattern_fill_segment import (
    build_layer04_inner_pattern_fill_frames,
)
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_inner_fill import (
    InnerPlacement,
    Layer04FillMetrics,
    Layer04InnerFillResult,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.provisional_overlay import (
    ProvisionalLayoutOverlay,
)
from shapez2_factory.application.asteroid_lab.layers.layer_05_inner_pattern_fill.run import (
    run_layer_04_inner_pattern_fill,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
    golden_5x5_complete_map,
    minimal_l2_plan_for_golden,
)


def test_inner_fill_event_types_registered() -> None:
    assert is_registered_event_type(EVENT_TYPE_LAYER04_INNER_PATTERN_FILL_BEGIN)
    assert is_registered_event_type(EVENT_TYPE_LAYER04_INNER_PATTERN_FILL_COMPLETE)
    assert (
        ReplayEventType.LAYER04_INNER_PATTERN_FILL_BEGIN.value
        == EVENT_TYPE_LAYER04_INNER_PATTERN_FILL_BEGIN
    )


def test_inner_fill_segment_emits_begin_complete_pair() -> None:
    result = Layer04InnerFillResult(
        interior_occupied_cells=frozenset({(1, 1), (2, 1)}),
        placements=(
            InnerPlacement(coord=(1, 1), pattern_id="builtin_1x1_field_block", rotation=0),
            InnerPlacement(coord=(2, 1), pattern_id="builtin_1x1_field_block", rotation=0),
        ),
        metrics=Layer04FillMetrics(
            interior_occupied_cell_count=2,
            coverage_ratio=0.5,
        ),
    )
    frames = build_layer04_inner_pattern_fill_frames(result)
    assert len(frames) == 2
    assert frames[0].event_type is ReplayEventType.LAYER04_INNER_PATTERN_FILL_BEGIN
    assert frames[1].event_type is ReplayEventType.LAYER04_INNER_PATTERN_FILL_COMPLETE
    assert frames[0].inspector["lab_phase_step"] == "layer_04_inner_pattern_fill"
    assert frames[0].metrics["interior_occupied_cell_count"] == 2
    assert frames[0].metrics["placement_count"] == 2
    kinds = {cell.kind for cell in frames[0].transient_overlay_cells}
    assert "inner_field_block" in kinds


def test_golden_map_inner_fill_wires_into_assembler_order() -> None:
    from django_apps.asteroid_lab.replay.event_types import (
        EVENT_TYPE_LAYER05_TRANSPORT_ROUTING_BEGIN,
    )
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
        build_solver_runtime_replay_frames,
    )
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        exterior_plan_wire_for_golden,
        layer04_route_plan_with_transport_tiles_for_golden,
        reconstruction_complete_lab_frame_dict_for_golden,
        rim_bundle_candidate_set_with_observability_for_golden,
    )

    complete_map = golden_5x5_complete_map()
    inner_fill = run_layer_04_inner_pattern_fill(
        complete_map=complete_map,
        exterior_plan=minimal_l2_plan_for_golden(),
        provisional_overlay=ProvisionalLayoutOverlay.empty(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
    )
    frames = build_solver_runtime_replay_frames(
        complete_map=complete_map,
        lab_frames_before_append=[reconstruction_complete_lab_frame_dict_for_golden()],
        exterior_plan_wire=exterior_plan_wire_for_golden(),
        layer03=rim_bundle_candidate_set_with_observability_for_golden(),
        layer04=None,
        layer04_inner_fill=inner_fill,
        layer05_route_plan=layer04_route_plan_with_transport_tiles_for_golden(),
    )
    types = [str(f["event_type"]) for f in frames]
    assert EVENT_TYPE_LAYER04_INNER_PATTERN_FILL_BEGIN in types
    assert EVENT_TYPE_LAYER04_INNER_PATTERN_FILL_COMPLETE in types
    assert EVENT_TYPE_LAYER05_TRANSPORT_ROUTING_BEGIN in types
    assert types.index(EVENT_TYPE_LAYER04_INNER_PATTERN_FILL_COMPLETE) < types.index(
        EVENT_TYPE_LAYER05_TRANSPORT_ROUTING_BEGIN
    )


def test_l5_transport_complete_frame_carries_committed_inner_fill() -> None:
    from django_apps.asteroid_lab.replay.event_types import (
        EVENT_TYPE_LAYER05_TRANSPORT_ROUTING_COMPLETE,
    )
    from django_apps.asteroid_lab.replay.layer04_inner_pattern_fill_segment import (
        COMMITTED_INNER_FILL_OVERLAY_ROLE,
    )
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
        build_solver_runtime_replay_frames,
    )
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        exterior_plan_wire_for_golden,
        layer04_route_plan_with_transport_tiles_for_golden,
        reconstruction_complete_lab_frame_dict_for_golden,
        rim_bundle_candidate_set_with_observability_for_golden,
    )

    complete_map = golden_5x5_complete_map()
    inner_fill = Layer04InnerFillResult(
        interior_occupied_cells=frozenset({(1, 1), (2, 1)}),
        placements=(
            InnerPlacement(coord=(1, 1), pattern_id="builtin_1x1_field_block", rotation=0),
            InnerPlacement(coord=(2, 1), pattern_id="builtin_1x1_field_block", rotation=0),
        ),
        metrics=Layer04FillMetrics(
            interior_occupied_cell_count=2,
            coverage_ratio=0.5,
        ),
    )

    frames = build_solver_runtime_replay_frames(
        complete_map=complete_map,
        lab_frames_before_append=[reconstruction_complete_lab_frame_dict_for_golden()],
        exterior_plan_wire=exterior_plan_wire_for_golden(),
        layer03=rim_bundle_candidate_set_with_observability_for_golden(),
        layer04=None,
        layer04_inner_fill=inner_fill,
        layer05_route_plan=layer04_route_plan_with_transport_tiles_for_golden(),
    )
    complete = next(
        f for f in frames if f["event_type"] == EVENT_TYPE_LAYER05_TRANSPORT_ROUTING_COMPLETE
    )
    overlay = (complete.get("map_view") or {}).get("overlay_cells") or []
    kinds = {str(row.get("kind")) for row in overlay}
    roles = {str(row.get("overlay_role")) for row in overlay}
    assert "inner_field_block" in kinds
    assert COMMITTED_INNER_FILL_OVERLAY_ROLE in roles
    assert any(str(k).startswith("space_") for k in kinds if k)
