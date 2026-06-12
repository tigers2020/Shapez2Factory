"""Finalize solver-runtime replay frames (overlay wire + metrics; assembler-owned)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import cast

from django_apps.asteroid_lab.replay.overlay_composition import compose_replay_overlay_cells
from django_apps.asteroid_lab.replay.overlay_wire_contract import overlay_cell_to_wire_dict
from django_apps.asteroid_lab.replay.replay_overlay_wire import ReplayOverlayCellWire
from django_apps.asteroid_lab.replay.segment_frame_spec import ReplaySegmentFrameSpec
from django_apps.asteroid_lab.replay.timeline_dtos import (
    ReplayMapView,
    ReplayOverlayCell,
    ReplayTimelineFrame,
    replay_map_view_is_renderable,
)
from django_apps.asteroid_lab.replay.timeline_serialization import (
    _mapping,
    replay_timeline_frame_to_json_dict,
)
from django_apps.asteroid_lab.services.lab_timeline_exterior_connector_enrichment import (
    METRICS_KEY,
)
from django_apps.asteroid_lab.typing_boundary import JsonValue


def structural_overlay_wire_from_source_frame(
    source_frame: Mapping[str, object] | None,
) -> list[dict[str, object]]:
    """Non-connector overlay rows from reconstruction source only (not L2 display overlay)."""

    if source_frame is None:
        return []
    map_view = source_frame.get("map_view")
    if not isinstance(map_view, dict):
        return []
    overlay = map_view.get("overlay_cells")
    if not isinstance(overlay, list):
        return []
    return [dict(row) for row in overlay if isinstance(row, dict)]


def transient_overlay_cells_to_wire(
    cells: Sequence[ReplayOverlayCell],
) -> list[ReplayOverlayCellWire]:
    return [overlay_cell_to_wire_dict(cell) for cell in cells]


def compose_runtime_overlay_wire(
    *,
    structural_overlay_wire: Sequence[Mapping[str, object]],
    persistent_overlay_wire: Sequence[Mapping[str, object]],
    transient_overlay_cells: Sequence[ReplayOverlayCell],
) -> list[dict[str, object]]:
    return compose_replay_overlay_cells(
        structural_overlay_cells=structural_overlay_wire,
        persistent_overlay_cells=persistent_overlay_wire,
        transient_overlay_cells=transient_overlay_cells_to_wire(transient_overlay_cells),
    )


def _metrics_with_exterior_plan(
    metrics: Mapping[str, JsonValue],
    *,
    exterior_plan_wire: Mapping[str, object] | None,
) -> dict[str, JsonValue]:
    merged: dict[str, JsonValue] = dict(metrics)
    if exterior_plan_wire is not None:
        merged[METRICS_KEY] = _mapping(exterior_plan_wire)
    return merged


def finalize_segment_spec_to_timeline_frame(
    spec: ReplaySegmentFrameSpec,
    *,
    structural_map_view: ReplayMapView,
    exterior_plan_wire: Mapping[str, object] | None,
) -> ReplayTimelineFrame:
    map_view = ReplayMapView(
        bbox=structural_map_view.bbox,
        base_ref=structural_map_view.base_ref,
        full_cells=structural_map_view.full_cells,
        cell_delta=structural_map_view.cell_delta,
        overlay_cells=(),
        annotations=structural_map_view.annotations,
    )
    if not replay_map_view_is_renderable(map_view):
        msg = "runtime segment frame must be renderable"
        raise ValueError(msg)
    inspector = dict(spec.inspector)
    if not inspector:
        inspector = {
            "lab_phase": spec.phase.value,
            "lab_phase_step": "",
            "lab_event_type": spec.event_type.value,
        }
    return ReplayTimelineFrame(
        frame_index=0,
        phase=spec.phase,
        event_type=spec.event_type,
        title=spec.title,
        description=spec.description,
        map_view=map_view,
        inspector=inspector,
        metrics=_metrics_with_exterior_plan(
            _mapping(spec.metrics),
            exterior_plan_wire=exterior_plan_wire,
        ),
    )


def finalize_timeline_frame_to_json_dict(
    frame: ReplayTimelineFrame,
    *,
    composed_overlay_wire: Sequence[Mapping[str, object]],
    exterior_plan_wire: Mapping[str, object] | None = None,
) -> dict[str, object]:
    wire = replay_timeline_frame_to_json_dict(frame)
    mv = dict(_mapping(wire.get("map_view")))
    mv["overlay_cells"] = [cast(dict[str, JsonValue], dict(row)) for row in composed_overlay_wire]
    wire["map_view"] = mv
    wire["metrics"] = _metrics_with_exterior_plan(
        _mapping(wire.get("metrics")),
        exterior_plan_wire=exterior_plan_wire,
    )
    return wire


def finalize_segment_spec_to_json_dict(
    spec: ReplaySegmentFrameSpec,
    *,
    structural_map_view: ReplayMapView,
    structural_overlay_wire: Sequence[Mapping[str, object]],
    persistent_overlay_wire: Sequence[Mapping[str, object]],
    exterior_plan_wire: Mapping[str, object] | None,
) -> dict[str, object]:
    composed = compose_runtime_overlay_wire(
        structural_overlay_wire=structural_overlay_wire,
        persistent_overlay_wire=persistent_overlay_wire,
        transient_overlay_cells=spec.transient_overlay_cells,
    )
    frame = finalize_segment_spec_to_timeline_frame(
        spec,
        structural_map_view=structural_map_view,
        exterior_plan_wire=exterior_plan_wire,
    )
    return finalize_timeline_frame_to_json_dict(
        frame,
        composed_overlay_wire=composed,
        exterior_plan_wire=exterior_plan_wire,
    )


def finalize_specs_to_timeline_frames(
    specs: Sequence[ReplaySegmentFrameSpec],
    *,
    structural_map_view: ReplayMapView,
    structural_overlay_wire: Sequence[Mapping[str, object]] = (),
    persistent_overlay_wire: Sequence[Mapping[str, object]] = (),
    exterior_plan_wire: Mapping[str, object] | None = None,
) -> tuple[ReplayTimelineFrame, ...]:
    """Test helper: timeline frames without wire overlay patch on map_view DTO."""

    return tuple(
        finalize_segment_spec_to_timeline_frame(
            spec,
            structural_map_view=structural_map_view,
            exterior_plan_wire=exterior_plan_wire,
        )
        for spec in specs
    )


__all__ = [
    "compose_runtime_overlay_wire",
    "finalize_segment_spec_to_json_dict",
    "finalize_segment_spec_to_timeline_frame",
    "finalize_specs_to_timeline_frames",
    "finalize_timeline_frame_to_json_dict",
    "structural_overlay_wire_from_source_frame",
    "transient_overlay_cells_to_wire",
]
