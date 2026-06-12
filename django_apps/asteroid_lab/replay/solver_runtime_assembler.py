"""Central solver runtime replay frame assembler (L2→L3→L4 fill→L5; output-only)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from django_apps.asteroid_lab.replay.layer02_segment import (
    build_layer02_exterior_transport_frame,
    map_view_from_complete_map,
)
from django_apps.asteroid_lab.replay.layer03_rim_greedy_segment import (
    build_layer03_rim_greedy_runtime_segment_specs,
    build_persistent_committed_equipment_overlay_wire,
)
from django_apps.asteroid_lab.replay.layer03_segment import build_layer03_runtime_segment_specs
from django_apps.asteroid_lab.replay.layer04_inner_pattern_fill_segment import (
    build_layer04_inner_pattern_fill_frames,
    build_persistent_inner_fill_overlay_wire,
)
from django_apps.asteroid_lab.replay.layer04_segment import build_layer04_runtime_segment_specs
from django_apps.asteroid_lab.replay.layer05_transport_segment import (
    build_layer05_transport_frames,
)
from django_apps.asteroid_lab.replay.persistent_connector_overlay_wire import (
    PersistentConnectorOverlayWire,
)
from django_apps.asteroid_lab.replay.persistent_exterior_overlay import (
    persistent_connector_overlays_from_wire,
)
from django_apps.asteroid_lab.replay.reconstruction_source import (
    find_reconstruction_complete_source_frame,
)
from django_apps.asteroid_lab.replay.runtime_frame_finalize import (
    compose_runtime_overlay_wire,
    finalize_segment_spec_to_json_dict,
    finalize_timeline_frame_to_json_dict,
    structural_overlay_wire_from_source_frame,
)
from django_apps.asteroid_lab.replay.segment_frame_spec import ReplaySegmentFrameSpec
from django_apps.asteroid_lab.replay.timeline_dtos import (
    ReplayMapView,
    replay_map_view_is_renderable,
)
from django_apps.asteroid_lab.replay.timeline_serialization import (
    replay_map_view_from_json_dict,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import (
    RimBundleCandidateSet,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_inner_fill import (
    Layer04InnerFillResult,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer05_route import (
    Layer05RoutePlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    IntegratedRimGreedyResult,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_placement import (
    Layer04RimPlacementResult,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
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


def _finalize_specs(
    specs: Sequence[ReplaySegmentFrameSpec],
    *,
    structural_map_view: ReplayMapView,
    structural_overlay_wire: Sequence[Mapping[str, object]],
    persistent_overlay_wire: Sequence[Mapping[str, object]],
    exterior_plan_wire: Mapping[str, object] | None,
) -> list[dict[str, Any]]:
    return [
        finalize_segment_spec_to_json_dict(
            spec,
            structural_map_view=structural_map_view,
            structural_overlay_wire=structural_overlay_wire,
            persistent_overlay_wire=persistent_overlay_wire,
            exterior_plan_wire=exterior_plan_wire,
        )
        for spec in specs
    ]


def build_solver_runtime_replay_frames(
    *,
    complete_map: ReconstructionCompleteMap,
    lab_frames_before_append: Sequence[Mapping[str, Any]],
    exterior_plan_wire: Mapping[str, Any] | None,
    layer03: RimBundleCandidateSet | IntegratedRimGreedyResult | None,
    layer04: Layer04RimPlacementResult | None,
    layer04_inner_fill: Layer04InnerFillResult | None = None,
    layer05_route_plan: Layer05RoutePlan | None = None,
    layer04_route_plan: Layer05RoutePlan | None = None,
    transport_kind: str = "space_belt",
) -> list[dict[str, Any]]:
    """JSON-serializable frames for ``SolverRun.config_json[solver_runtime_replay_frames]``."""

    source = find_reconstruction_complete_source_frame(
        [dict(frame) for frame in lab_frames_before_append]
    )
    if source is not None:
        structural_base_map_view = replay_map_view_from_json_dict(source["map_view"])
    else:
        structural_base_map_view = map_view_from_complete_map(complete_map)

    structural_overlay_wire = structural_overlay_wire_from_source_frame(source)
    plan_dict: dict[str, object] | None = (
        dict(exterior_plan_wire) if exterior_plan_wire is not None else None
    )
    persistent_overlay_wire: list[PersistentConnectorOverlayWire] = (
        persistent_connector_overlays_from_wire(plan_dict) if plan_dict is not None else []
    )

    out: list[dict[str, Any]] = []

    if plan_dict is not None:
        l2_frame = build_layer02_exterior_transport_frame(
            plan_wire=plan_dict,
            source_frame=source,
            complete_map=complete_map,
        )
        structural_base_map_view = l2_frame.map_view
        l2_composed = compose_runtime_overlay_wire(
            structural_overlay_wire=structural_overlay_wire,
            persistent_overlay_wire=persistent_overlay_wire,
            transient_overlay_cells=(),
        )
        out.append(
            finalize_timeline_frame_to_json_dict(
                l2_frame,
                composed_overlay_wire=l2_composed,
                exterior_plan_wire=plan_dict,
            )
        )

    display_base = _ensure_renderable_base_map_view(
        structural_base_map_view,
        complete_map=complete_map,
    )

    persistent_with_equipment: list[Mapping[str, object]] = list(persistent_overlay_wire)
    if isinstance(layer03, IntegratedRimGreedyResult):
        persistent_with_equipment.extend(
            build_persistent_committed_equipment_overlay_wire(layer03),
        )

    persistent_with_inner_fill: list[Mapping[str, object]] = list(persistent_with_equipment)
    if layer04_inner_fill is not None:
        persistent_with_inner_fill.extend(
            build_persistent_inner_fill_overlay_wire(
                layer04_inner_fill,
                transport_kind=transport_kind,
            )
        )

    if layer03 is not None:
        if isinstance(layer03, IntegratedRimGreedyResult):
            l3_specs = build_layer03_rim_greedy_runtime_segment_specs(layer03)
        else:
            l3_specs = build_layer03_runtime_segment_specs(
                observability=layer03.observability,
            )
        out.extend(
            _finalize_specs(
                l3_specs,
                structural_map_view=display_base,
                structural_overlay_wire=structural_overlay_wire,
                persistent_overlay_wire=persistent_overlay_wire,
                exterior_plan_wire=plan_dict,
            )
        )

    route_plan = layer05_route_plan if layer05_route_plan is not None else layer04_route_plan
    has_transport_replay = route_plan is not None and (
        bool(route_plan.routes) or bool(route_plan.transport_tiles)
    )

    if layer04_inner_fill is not None:
        l4_fill_specs = build_layer04_inner_pattern_fill_frames(
            layer04_inner_fill,
            transport_kind=transport_kind,
        )
        out.extend(
            _finalize_specs(
                l4_fill_specs,
                structural_map_view=display_base,
                structural_overlay_wire=structural_overlay_wire,
                persistent_overlay_wire=persistent_with_equipment,
                exterior_plan_wire=plan_dict,
            )
        )
    elif layer04 is not None and not has_transport_replay:
        l4_specs = build_layer04_runtime_segment_specs(
            selected=layer04.selected_placements,
            rejected=layer04.rejected_candidates,
            packing_observability=layer04.packing_observability,
        )
        out.extend(
            _finalize_specs(
                l4_specs,
                structural_map_view=display_base,
                structural_overlay_wire=structural_overlay_wire,
                persistent_overlay_wire=persistent_overlay_wire,
                exterior_plan_wire=plan_dict,
            )
        )

    if has_transport_replay:
        assert route_plan is not None
        l5_specs = build_layer05_transport_frames(route_plan)
        out.extend(
            _finalize_specs(
                l5_specs,
                structural_map_view=display_base,
                structural_overlay_wire=structural_overlay_wire,
                persistent_overlay_wire=persistent_with_inner_fill,
                exterior_plan_wire=plan_dict,
            )
        )

    return out


__all__ = ["build_solver_runtime_replay_frames"]
