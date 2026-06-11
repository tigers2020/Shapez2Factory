"""Layer 05 transport routing replay segment (canonical L5 slug)."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.event_types import assert_registered_event_type
from django_apps.asteroid_lab.replay.overlay_wire_contract import (
    build_output_hint_overlay_cell,
    build_routed_transport_overlay_cell,
)
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.segment_frame_spec import ReplaySegmentFrameSpec
from django_apps.asteroid_lab.replay.timeline_dtos import ReplayOverlayCell
from shapez2_factory.application.asteroid_lab.layers.contracts.layer05_route import (
    CommittedRoute,
    Layer05RoutePlan,
    ProjectedTransportTile,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord

LAYER05_TRANSPORT_PHASE = "layer_05_transport_routing"
OVERLAY_KIND_ROUTE_PROBE_PATH = "route_probe_path"

_L5_TRANSPORT_INSPECTOR = {
    "lab_phase": "route_probe",
    "lab_phase_step": LAYER05_TRANSPORT_PHASE,
}


def _union_route_path_coords(routes: tuple[CommittedRoute, ...]) -> tuple[Coord, ...]:
    seen: set[Coord] = set()
    out: list[Coord] = []
    for route in routes:
        for coord in route.path_coords:
            if coord in seen:
                continue
            seen.add(coord)
            out.append(coord)
    return tuple(out)


def _overlay_from_route_path_fallback(plan: Layer05RoutePlan) -> tuple[ReplayOverlayCell, ...]:
    return tuple(
        build_output_hint_overlay_cell(
            x=x,
            y=y,
            kind=OVERLAY_KIND_ROUTE_PROBE_PATH,
            profile_transport_kind=plan.transport_kind,
        )
        for x, y in _union_route_path_coords(plan.routes)
    )


def _overlays_for_plan(plan: Layer05RoutePlan) -> tuple[ReplayOverlayCell, ...]:
    if plan.transport_tiles:
        return tuple(_overlay_from_tile(t) for t in plan.transport_tiles)
    if plan.routes:
        return _overlay_from_route_path_fallback(plan)
    return ()


def _overlay_from_tile(tile: ProjectedTransportTile) -> ReplayOverlayCell:
    x, y = tile.coord
    return build_routed_transport_overlay_cell(
        x=x,
        y=y,
        transport_kind=tile.transport_kind,
        tile_id=tile.tile_id,
        rotation=tile.rotation,
    )


def _spec(
    *,
    event_type: ReplayEventType,
    title: str,
    description: str,
    metrics: dict[str, object],
    transient_overlay_cells: tuple[ReplayOverlayCell, ...] = (),
) -> ReplaySegmentFrameSpec:
    assert_registered_event_type(event_type.value)
    return ReplaySegmentFrameSpec(
        event_type=event_type,
        phase=ReplayPhase.ROUTE_PROBE,
        title=title,
        description=description,
        metrics=metrics,
        transient_overlay_cells=transient_overlay_cells,
        inspector=dict(_L5_TRANSPORT_INSPECTOR),
    )


def build_layer05_transport_frames(
    plan: Layer05RoutePlan,
    *,
    event_types: tuple[ReplayEventType, ReplayEventType] | None = None,
) -> tuple[ReplaySegmentFrameSpec, ...]:
    begin_type, complete_type = event_types or (
        ReplayEventType.LAYER05_TRANSPORT_ROUTING_BEGIN,
        ReplayEventType.LAYER05_TRANSPORT_ROUTING_COMPLETE,
    )
    overlays = _overlays_for_plan(plan)
    replay_overlay_mode = (
        "transport_tiles"
        if plan.transport_tiles
        else ("route_path_fallback" if plan.routes else "none")
    )
    begin_metrics: dict[str, object] = {
        "layer": LAYER05_TRANSPORT_PHASE,
        "source_count": plan.metrics.source_count,
        "transport_kind": plan.transport_kind,
        "replay_overlay_mode": replay_overlay_mode,
    }
    begin = _spec(
        event_type=begin_type,
        title="Layer 05 transport routing begin",
        description="Sequential merge-aware transport routing",
        metrics=begin_metrics,
        transient_overlay_cells=overlays,
    )
    complete = _spec(
        event_type=complete_type,
        title="Layer 05 transport routing complete",
        description=(
            f"Routed {plan.metrics.routed_source_count}/{plan.metrics.source_count} sources; "
            f"{len(plan.transport_tiles)} transport tile(s)"
        ),
        metrics={
            "layer": LAYER05_TRANSPORT_PHASE,
            "route_count": len(plan.routes),
            "group_count": len(plan.groups),
            "transport_tile_count": len(plan.transport_tiles),
            "failed_source_count": plan.metrics.failed_source_count,
            "failure_reasons": [f.reason.value for f in plan.failures],
            "replay_overlay_mode": replay_overlay_mode,
        },
        transient_overlay_cells=overlays,
    )
    return (begin, complete)


__all__ = [
    "LAYER05_TRANSPORT_PHASE",
    "OVERLAY_KIND_ROUTE_PROBE_PATH",
    "build_layer05_transport_frames",
]
