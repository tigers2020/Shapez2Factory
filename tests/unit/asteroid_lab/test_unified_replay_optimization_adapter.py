"""Phase 9C — OptimizationReplayFrame → UnifiedReplayFrame adapter tests."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.optimization.enums import OptimizationReplayEventType
from django_apps.asteroid_lab.optimization.replay_frame import OptimizationReplayFrame
from django_apps.asteroid_lab.replay.optimization_unified_adapter import (
    REPLAY_EVENT_TYPE_TO_PHASE,
    OptimizationUnifiedAdapterError,
    optimization_replay_frame_to_unified,
)
from django_apps.asteroid_lab.replay.projection_context import ReplayProjectionContext
from django_apps.asteroid_lab.replay.unified_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.unified_event_coverage import (
    SUPPORTED_BY_9C_OPTIMIZATION_ADAPTER,
)
from django_apps.asteroid_lab.replay.unified_serialization import (
    unified_replay_frame_json_round_trip,
)

_PARAMS = (1, 0)


def _context() -> ReplayProjectionContext:
    return ReplayProjectionContext(server_xy_params=_PARAMS)


def _server_cell(*, sx: int, sy: int, kind: str = "asteroid") -> dict[str, object]:
    return {
        "server_x": sx,
        "server_y": sy,
        "cell_kind": kind,
        "transport_kind": "none",
    }


def _lab_cell(*, x: int, y: int, kind: str = "asteroid") -> dict[str, object]:
    return {"x": x, "y": y, "cell_kind": kind, "transport_kind": "none"}


def test_optimization_input_loaded_projects_server_to_lab() -> None:
    frame = OptimizationReplayFrame(
        frame_index=0,
        event_type=OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED,
        title="input",
        description="",
        visible_cells=(_server_cell(sx=0, sy=0),),
        metrics={"mineable_cell_count": 1},
    )
    unified = optimization_replay_frame_to_unified(frame, context=_context())
    assert unified.phase == ReplayPhase.OPTIMIZATION_INPUT
    assert unified.event_type == ReplayEventType.OPTIMIZATION_INPUT_LOADED
    assert len(unified.map_view.full_cells) == 1
    assert unified.map_view.full_cells[0].x == 2
    assert unified.map_view.full_cells[0].y == 0
    assert unified.inspector["optimization_event_type"] == "optimization.input_loaded"


def test_route_probe_overlay_frame() -> None:
    frame = OptimizationReplayFrame(
        frame_index=3,
        event_type=OptimizationReplayEventType.ROUTE_PROBE_SUCCEEDED,
        title="probe ok",
        description="",
        visible_cells=(),
        overlay_cells=(
            _server_cell(sx=0, sy=0, kind="route_probe_path"),
            _server_cell(sx=1, sy=0, kind="route_probe_path"),
        ),
        metrics={
            "reached_goal_kind": "external_margin",
            "goal_x": 2,
            "goal_y": 0,
        },
    )
    unified = optimization_replay_frame_to_unified(frame, context=_context())
    assert unified.phase == ReplayPhase.ROUTE_PROBE
    assert len(unified.map_view.overlay_cells) == 2
    assert unified.map_view.overlay_cells[0].kind == "route_probe_path"
    assert any(a.label == "external_margin" for a in unified.map_view.annotations)


def test_candidate_rejected_annotation() -> None:
    frame = OptimizationReplayFrame(
        frame_index=2,
        event_type=OptimizationReplayEventType.CANDIDATE_REJECTED,
        title="rejected",
        description="",
        overlay_cells=(_lab_cell(x=1, y=0, kind="candidate_reject"),),
        metrics={
            "candidate_reject_reason": "extractor_not_rim",
            "reject_x": 1,
            "reject_y": 0,
        },
    )
    unified = optimization_replay_frame_to_unified(frame, context=_context())
    assert unified.event_type == ReplayEventType.CANDIDATE_REJECTED
    labels = [a.label for a in unified.map_view.annotations]
    assert "extractor_not_rim" in labels


def test_route_materialized_visible_and_overlay() -> None:
    frame = OptimizationReplayFrame(
        frame_index=10,
        event_type=OptimizationReplayEventType.ROUTE_MATERIALIZED,
        title="materialized",
        description="",
        visible_cells=(_server_cell(sx=0, sy=0),),
        overlay_cells=(
            {
                "server_x": 1,
                "server_y": 0,
                "cell_kind": "route_materialized",
                "transport_kind": "shape_belt",
            },
        ),
    )
    unified = optimization_replay_frame_to_unified(frame, context=_context())
    assert len(unified.map_view.full_cells) == 1
    assert len(unified.map_view.overlay_cells) == 1
    assert unified.map_view.overlay_cells[0].transport == "shape_belt"


def test_adapter_uses_fallback_full_cells_when_visible_empty() -> None:
    from django_apps.asteroid_lab.replay.unified_dtos import ReplayCell

    fallback = (ReplayCell(x=1, y=0, kind="asteroid", transport="none"),)
    ctx = ReplayProjectionContext(
        server_xy_params=_PARAMS,
        fallback_full_cells=fallback,
    )
    frame = OptimizationReplayFrame(
        frame_index=5,
        event_type=OptimizationReplayEventType.CAPACITY_PLAN_CREATED,
        title="capacity",
        description="",
        metrics={},
    )
    unified = optimization_replay_frame_to_unified(frame, context=ctx)
    assert unified.map_view.full_cells == fallback


def test_optimization_adapter_marks_fallback_full_cells_usage() -> None:
    from django_apps.asteroid_lab.replay.unified_dtos import ReplayCell

    fallback = (ReplayCell(x=1, y=0, kind="asteroid", transport="none"),)
    ctx = ReplayProjectionContext(
        server_xy_params=_PARAMS,
        fallback_full_cells=fallback,
    )
    frame = OptimizationReplayFrame(
        frame_index=5,
        event_type=OptimizationReplayEventType.CAPACITY_PLAN_CREATED,
        title="capacity",
        description="",
        metrics={},
    )
    unified = optimization_replay_frame_to_unified(frame, context=ctx)
    assert unified.metrics["fallback_full_cells_used"] is True
    assert unified.metrics["fallback_full_cells_reason"] == "metadata_only_optimization_frame"


def test_adapter_promotes_visible_cells_to_overlay_when_fallback_available() -> None:
    from django_apps.asteroid_lab.replay.unified_dtos import ReplayCell

    fallback = (ReplayCell(x=1, y=0, kind="asteroid", transport="none"),)
    ctx = ReplayProjectionContext(
        server_xy_params=_PARAMS,
        fallback_full_cells=fallback,
    )
    frame = OptimizationReplayFrame(
        frame_index=0,
        event_type=OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED,
        title="input",
        description="",
        visible_cells=(_server_cell(sx=0, sy=0, kind="asteroid_shape_field"),),
        metrics={"mineable_cell_count": 1},
    )
    unified = optimization_replay_frame_to_unified(frame, context=ctx)
    assert unified.map_view.full_cells == fallback
    assert len(unified.map_view.overlay_cells) >= 1
    assert unified.map_view.overlay_cells[0].kind == "asteroid_shape_field"
    assert "fallback_full_cells_used" not in unified.metrics


def test_adapter_rejects_non_renderable_without_fallback() -> None:
    frame = OptimizationReplayFrame(
        frame_index=0,
        event_type=OptimizationReplayEventType.PATTERN_GENERATED,
        title="pattern",
        description="",
        metrics={},
    )
    with pytest.raises(OptimizationUnifiedAdapterError):
        optimization_replay_frame_to_unified(frame, context=_context())


def test_adapter_does_not_mutate_source_frame() -> None:
    frame = OptimizationReplayFrame(
        frame_index=0,
        event_type=OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED,
        title="t",
        description="",
        visible_cells=(_server_cell(sx=0, sy=0),),
        metrics={"k": 1},
    )
    before_cells = [dict(c) for c in frame.visible_cells]
    before_metrics = dict(frame.metrics)
    optimization_replay_frame_to_unified(frame, context=_context())
    assert [dict(c) for c in frame.visible_cells] == before_cells
    assert dict(frame.metrics) == before_metrics


def test_adapter_preserves_frame_index_override() -> None:
    frame = OptimizationReplayFrame(
        frame_index=99,
        event_type=OptimizationReplayEventType.VALIDATION_COMPLETED,
        title="v",
        description="",
        visible_cells=(_lab_cell(x=1, y=0),),
    )
    unified = optimization_replay_frame_to_unified(frame, context=_context(), frame_index=7)
    assert unified.frame_index == 7
    assert unified.inspector["source_frame_index"] == 99


def test_adapter_event_types_in_9c_set_only() -> None:
    frame = OptimizationReplayFrame(
        frame_index=0,
        event_type=OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED,
        title="t",
        description="",
        visible_cells=(_lab_cell(x=1, y=0),),
    )
    unified = optimization_replay_frame_to_unified(frame, context=_context())
    assert unified.event_type in SUPPORTED_BY_9C_OPTIMIZATION_ADAPTER


def test_adapter_deterministic_json_round_trip() -> None:
    frame = OptimizationReplayFrame(
        frame_index=0,
        event_type=OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED,
        title="t",
        description="",
        visible_cells=(_server_cell(sx=0, sy=0),),
    )
    unified = optimization_replay_frame_to_unified(frame, context=_context())
    assert unified_replay_frame_json_round_trip(unified) == unified


def test_adapter_phase_mapping_covers_all_9c_event_types() -> None:
    assert set(REPLAY_EVENT_TYPE_TO_PHASE.keys()) == SUPPORTED_BY_9C_OPTIMIZATION_ADAPTER


def test_adapter_validation_failed_event() -> None:
    frame = OptimizationReplayFrame(
        frame_index=1,
        event_type=OptimizationReplayEventType.VALIDATION_FAILED,
        title="fail",
        description="",
        visible_cells=(_lab_cell(x=1, y=0),),
        metrics={"issue_code": "orphan_transport"},
    )
    unified = optimization_replay_frame_to_unified(frame, context=_context())
    assert unified.event_type == ReplayEventType.VALIDATION_FAILED
    assert unified.phase == ReplayPhase.VALIDATION


def test_result_layout_unified_frame_has_full_cells_not_overlay_only() -> None:
    """RESULT_LAYOUT frame must produce non-empty full_cells (not just overlay)
    when visible_cells contain reconstruction base cells."""
    frame = OptimizationReplayFrame(
        frame_index=0,
        event_type=OptimizationReplayEventType.RESULT_LAYOUT,
        title="Final layout",
        description="",
        visible_cells=(_server_cell(sx=0, sy=0), _server_cell(sx=1, sy=0)),
        overlay_cells=(),
        metrics={"validation_passed": True, "cell_count": 2},
    )
    ctx = ReplayProjectionContext(server_xy_params=_PARAMS)
    unified = optimization_replay_frame_to_unified(frame, context=ctx)
    assert unified.event_type == ReplayEventType.RESULT_LAYOUT
    assert unified.phase == ReplayPhase.RESULT
    assert (
        len(unified.map_view.full_cells) >= 1
    ), "RESULT_LAYOUT unified frame must have full_cells, not overlay only"
