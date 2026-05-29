"""Central solver runtime replay frame assembler (L2→L3→L4; output-only)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from django_apps.asteroid_lab.layers.contracts.candidates import RimBundleCandidateSet
from django_apps.asteroid_lab.layers.contracts.rim_placement import Layer04RimPlacementResult
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.replay.layer02_segment import (
    build_layer02_exterior_transport_frame,
    map_view_from_complete_map,
)
from django_apps.asteroid_lab.replay.layer03_segment import build_layer03_runtime_segment_frames
from django_apps.asteroid_lab.replay.layer04_segment import build_layer04_runtime_segment_frames
from django_apps.asteroid_lab.replay.reconstruction_source import (
    find_reconstruction_complete_source_frame,
)
from django_apps.asteroid_lab.replay.timeline_dtos import (
    ReplayMapView,
    ReplayTimelineFrame,
    replay_map_view_is_renderable,
)
from django_apps.asteroid_lab.replay.timeline_serialization import (
    replay_map_view_from_json_dict,
    replay_timeline_frame_to_json_dict,
)

# Metadata-only solver runtime base when reconstruction has no field cells (e.g. empty copy).
_RUNTIME_EMPTY_RECONSTRUCTION_BASE_REF = "solver_runtime:empty_reconstruction"


def _with_empty_reconstruction_base_ref(map_view: ReplayMapView) -> ReplayMapView:
    if replay_map_view_is_renderable(map_view):
        return map_view
    return ReplayMapView(
        bbox=map_view.bbox,
        base_ref=_RUNTIME_EMPTY_RECONSTRUCTION_BASE_REF,
        full_cells=map_view.full_cells,
        cell_delta=map_view.cell_delta,
        overlay_cells=map_view.overlay_cells,
        annotations=map_view.annotations,
    )


def _ensure_renderable_base_map_view(
    map_view: ReplayMapView,
    *,
    complete_map: ReconstructionCompleteMap,
) -> ReplayMapView:
    if replay_map_view_is_renderable(map_view):
        return map_view
    fallback = map_view_from_complete_map(complete_map)
    if replay_map_view_is_renderable(fallback):
        return fallback
    return _with_empty_reconstruction_base_ref(fallback)


def build_solver_runtime_replay_frames(
    *,
    complete_map: ReconstructionCompleteMap,
    lab_frames_before_append: Sequence[Mapping[str, Any]],
    exterior_plan_wire: Mapping[str, Any] | None,
    layer03: RimBundleCandidateSet | None,
    layer04: Layer04RimPlacementResult | None,
) -> list[dict[str, Any]]:
    """JSON-serializable frames for ``SolverRun.config_json[solver_runtime_replay_frames]``."""

    source = find_reconstruction_complete_source_frame(list(lab_frames_before_append))
    if source is not None:
        structural_base_map_view = replay_map_view_from_json_dict(source["map_view"])
    else:
        structural_base_map_view = map_view_from_complete_map(complete_map)

    frames: list[ReplayTimelineFrame] = []

    if exterior_plan_wire is not None:
        l2_frame = build_layer02_exterior_transport_frame(
            plan_wire=dict(exterior_plan_wire),
            source_frame=source,
            complete_map=complete_map,
        )
        frames.append(l2_frame)
        structural_base_map_view = l2_frame.map_view

    if layer03 is not None:
        l3_base = _ensure_renderable_base_map_view(
            structural_base_map_view,
            complete_map=complete_map,
        )
        l3_frames = build_layer03_runtime_segment_frames(
            observability=layer03.observability,
            base_map_view=l3_base,
        )
        frames.extend(l3_frames)

    if layer04 is not None:
        l4_base = _ensure_renderable_base_map_view(
            structural_base_map_view,
            complete_map=complete_map,
        )
        l4_frames = build_layer04_runtime_segment_frames(
            base_map_view=l4_base,
            selected=layer04.selected_placements,
            rejected=layer04.rejected_candidates,
        )
        frames.extend(l4_frames)

    return [replay_timeline_frame_to_json_dict(fr) for fr in frames]


__all__ = ["build_solver_runtime_replay_frames"]
