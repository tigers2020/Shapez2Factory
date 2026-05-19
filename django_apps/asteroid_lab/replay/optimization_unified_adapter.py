"""OptimizationReplayFrame → UnifiedReplayFrame (Phase 9C; output-only)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from django_apps.asteroid_lab.optimization.replay_frame import OptimizationReplayFrame
from django_apps.asteroid_lab.replay.projection_context import (
    ReplayProjectionContext,
    lab_xy_from_server_xy,
)
from django_apps.asteroid_lab.replay.unified_dtos import (
    ReplayAnnotation,
    ReplayBBox,
    ReplayCell,
    ReplayCellDelta,
    ReplayMapView,
    ReplayOverlayCell,
    UnifiedReplayFrame,
    replay_map_view_is_renderable,
)
from django_apps.asteroid_lab.replay.unified_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.unified_event_coverage import (
    SUPPORTED_BY_9C_OPTIMIZATION_ADAPTER,
)
from django_apps.asteroid_lab.replay.unified_serialization import parse_replay_event_type

REPLAY_EVENT_TYPE_TO_PHASE: dict[ReplayEventType, ReplayPhase] = {
    ReplayEventType.OPTIMIZATION_INPUT_LOADED: ReplayPhase.OPTIMIZATION_INPUT,
    ReplayEventType.CAPACITY_PLAN_CREATED: ReplayPhase.OPTIMIZATION_INPUT,
    ReplayEventType.ROUTE_GOAL_GENERATED: ReplayPhase.OPTIMIZATION_INPUT,
    ReplayEventType.PATTERN_GENERATED: ReplayPhase.PATTERN_GENERATION,
    ReplayEventType.CANDIDATE_GENERATED: ReplayPhase.CANDIDATE_GENERATION,
    ReplayEventType.CANDIDATE_REJECTED: ReplayPhase.CANDIDATE_GENERATION,
    ReplayEventType.ROUTE_PROBE_SUCCEEDED: ReplayPhase.ROUTE_PROBE,
    ReplayEventType.ROUTE_PROBE_FAILED: ReplayPhase.ROUTE_PROBE,
    ReplayEventType.CANDIDATE_POOL_COMPLETED: ReplayPhase.CANDIDATE_GENERATION,
    ReplayEventType.CANDIDATE_SELECTION_COMPLETED: ReplayPhase.CANDIDATE_GENERATION,
    ReplayEventType.GENOME_GENERATED: ReplayPhase.GENOME_FITNESS,
    ReplayEventType.GENOME_EVALUATED: ReplayPhase.GENOME_FITNESS,
    ReplayEventType.GENERATION_COMPLETED: ReplayPhase.EVOLUTION,
    ReplayEventType.BEST_GENOME_SELECTED: ReplayPhase.GENOME_FITNESS,
    ReplayEventType.ROUTE_COMMIT_ATTEMPTED: ReplayPhase.INCREMENTAL_COMMIT,
    ReplayEventType.ROUTE_COMMITTED: ReplayPhase.INCREMENTAL_COMMIT,
    ReplayEventType.ROUTE_ROLLED_BACK: ReplayPhase.ROLLBACK,
    ReplayEventType.ROUTE_MATERIALIZED: ReplayPhase.INCREMENTAL_COMMIT,
    ReplayEventType.VALIDATION_COMPLETED: ReplayPhase.VALIDATION,
    ReplayEventType.VALIDATION_FAILED: ReplayPhase.VALIDATION,
    ReplayEventType.RESULT_LAYOUT: ReplayPhase.RESULT,
}


class OptimizationUnifiedAdapterError(ValueError):
    """Raised when an optimization replay frame cannot be wrapped for 9C."""


def _phase_for_event(event_type: ReplayEventType) -> ReplayPhase:
    try:
        return REPLAY_EVENT_TYPE_TO_PHASE[event_type]
    except KeyError as exc:
        msg = f"ReplayEventType has no 9C phase mapping: {event_type!r}"
        raise OptimizationUnifiedAdapterError(msg) from exc


def _event_type_from_wire(wire: str) -> ReplayEventType:
    try:
        unified = parse_replay_event_type(wire)
    except ValueError as exc:
        msg = f"optimization event_type not supported by 9C adapter: {wire!r}"
        raise OptimizationUnifiedAdapterError(msg) from exc
    if unified not in SUPPORTED_BY_9C_OPTIMIZATION_ADAPTER:
        msg = f"ReplayEventType not in 9C optimization set: {unified!r}"
        raise OptimizationUnifiedAdapterError(msg)
    return unified


def _lab_xy_from_row(row: Mapping[str, Any], context: ReplayProjectionContext) -> tuple[int, int]:
    if "x" in row and "y" in row:
        return int(row["x"]), int(row["y"])
    if "server_x" in row and "server_y" in row:
        return lab_xy_from_server_xy(
            int(row["server_x"]),
            int(row["server_y"]),
            server_xy_params=context.server_xy_params,
        )
    msg = "cell row must have x/y or server_x/server_y"
    raise OptimizationUnifiedAdapterError(msg)


def _cell_from_row(row: Mapping[str, Any], context: ReplayProjectionContext) -> ReplayCell:
    x, y = _lab_xy_from_row(row, context)
    return ReplayCell(
        x=x,
        y=y,
        kind=str(row.get("cell_kind") or row.get("kind") or ""),
        transport=str(row.get("transport_kind") or row.get("transport") or ""),
    )


def _overlay_from_row(
    row: Mapping[str, Any], context: ReplayProjectionContext
) -> ReplayOverlayCell:
    x, y = _lab_xy_from_row(row, context)
    return ReplayOverlayCell(
        x=x,
        y=y,
        kind=str(row.get("cell_kind") or row.get("kind") or ""),
        transport=str(row.get("transport_kind") or row.get("transport") or ""),
    )


def _delta_from_row(row: Mapping[str, Any], context: ReplayProjectionContext) -> ReplayCellDelta:
    x, y = _lab_xy_from_row(row, context)
    return ReplayCellDelta(
        x=x,
        y=y,
        kind=str(row.get("cell_kind") or row.get("kind") or ""),
        transport=str(row.get("transport_kind") or row.get("transport") or ""),
        op=str(row.get("op") or "set"),
    )


def _rows_to_full_cells(
    rows: tuple[dict[str, Any], ...],
    context: ReplayProjectionContext,
) -> tuple[ReplayCell, ...]:
    out: list[ReplayCell] = []
    for raw in rows:
        out.append(_cell_from_row(raw, context))
    return tuple(out)


def _rows_to_overlay_cells(
    rows: tuple[dict[str, Any], ...],
    context: ReplayProjectionContext,
) -> tuple[ReplayOverlayCell, ...]:
    return tuple(_overlay_from_row(raw, context) for raw in rows)


def _rows_to_cell_delta(
    rows: tuple[dict[str, Any], ...],
    context: ReplayProjectionContext,
) -> tuple[ReplayCellDelta, ...]:
    deltas: list[ReplayCellDelta] = []
    for raw in rows:
        if raw.get("op") or raw.get("cell_delta"):
            deltas.append(_delta_from_row(raw, context))
    return tuple(deltas)


def _bbox_from_map_parts(
    full_cells: tuple[ReplayCell, ...],
    overlay_cells: tuple[ReplayOverlayCell, ...],
    cell_delta: tuple[ReplayCellDelta, ...],
    annotations: tuple[ReplayAnnotation, ...],
) -> ReplayBBox:
    xs: list[int] = []
    ys: list[int] = []
    for c in full_cells:
        xs.append(c.x)
        ys.append(c.y)
    for o in overlay_cells:
        xs.append(o.x)
        ys.append(o.y)
    for d in cell_delta:
        xs.append(d.x)
        ys.append(d.y)
    for a in annotations:
        xs.append(a.x)
        ys.append(a.y)
    if not xs:
        return ReplayBBox(min_x=0, min_y=0, max_x=0, max_y=0)
    return ReplayBBox(min_x=min(xs), min_y=min(ys), max_x=max(xs), max_y=max(ys))


def _annotations_from_metrics(metrics: Mapping[str, Any]) -> tuple[ReplayAnnotation, ...]:
    out: list[ReplayAnnotation] = []
    reject = metrics.get("candidate_reject_reason")
    if reject and metrics.get("reject_x") is not None and metrics.get("reject_y") is not None:
        out.append(
            ReplayAnnotation(
                x=int(metrics["reject_x"]),
                y=int(metrics["reject_y"]),
                label=str(reject),
            )
        )
    probe_fail = metrics.get("route_probe_failure_reason")
    if probe_fail and metrics.get("probe_x") is not None and metrics.get("probe_y") is not None:
        out.append(
            ReplayAnnotation(
                x=int(metrics["probe_x"]),
                y=int(metrics["probe_y"]),
                label=str(probe_fail),
            )
        )
    goal = metrics.get("reached_goal_kind")
    if goal and metrics.get("goal_x") is not None and metrics.get("goal_y") is not None:
        out.append(
            ReplayAnnotation(
                x=int(metrics["goal_x"]),
                y=int(metrics["goal_y"]),
                label=str(goal),
            )
        )
    return tuple(out)


def _build_map_view(
    frame: OptimizationReplayFrame,
    context: ReplayProjectionContext,
) -> ReplayMapView:
    full_cells = _rows_to_full_cells(frame.visible_cells, context)
    overlay_cells = _rows_to_overlay_cells(frame.overlay_cells, context)
    cell_delta = _rows_to_cell_delta(frame.visible_cells + frame.overlay_cells, context)
    annotations = _annotations_from_metrics(frame.metrics)

    if not full_cells and context.fallback_full_cells:
        full_cells = context.fallback_full_cells

    base_ref = context.base_ref
    bbox = _bbox_from_map_parts(full_cells, overlay_cells, cell_delta, annotations)
    map_view = ReplayMapView(
        bbox=bbox,
        base_ref=base_ref,
        full_cells=full_cells,
        cell_delta=cell_delta,
        overlay_cells=overlay_cells,
        annotations=annotations,
    )
    if not replay_map_view_is_renderable(map_view):
        msg = "optimization frame has no renderable map_view"
        raise OptimizationUnifiedAdapterError(msg)
    return map_view


def optimization_replay_frame_to_unified(
    frame: OptimizationReplayFrame,
    *,
    context: ReplayProjectionContext,
    frame_index: int | None = None,
) -> UnifiedReplayFrame:
    """Wrap one optimization replay frame (does not mutate ``frame``)."""

    wire = frame.event_type.value
    unified_event = _event_type_from_wire(wire)
    idx = int(frame.frame_index) if frame_index is None else int(frame_index)
    map_view = _build_map_view(frame, context)
    return UnifiedReplayFrame(
        frame_index=idx,
        phase=_phase_for_event(unified_event),
        event_type=unified_event,
        title=str(frame.title),
        description=str(frame.description),
        map_view=map_view,
        inspector={
            "optimization_event_type": wire,
            "source_frame_index": int(frame.frame_index),
        },
        metrics=dict(frame.metrics),
    )
