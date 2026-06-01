"""Replay uses L4 transport_tiles, not L3 route_probe_path (PR-L4-5)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
    LAYER04_ROUTE_PLAN_VERSION,
    Layer04Metrics,
    Layer04RoutePlan,
    ProjectedTransportTile,
)
from django_apps.asteroid_lab.replay.layer04_transport_segment import (
    OVERLAY_KIND_ROUTE_PROBE_PATH,
    build_layer04_transport_frames,
)


def _plan_with_tiles() -> Layer04RoutePlan:
    tile = ProjectedTransportTile(
        coord=(0, 0),
        transport_kind="space_belt",
        tile_id="SpaceBelt_Forward",
        rotation=0,
        input_dirs=("W",),
        output_dirs=("E",),
        group_id="conn_c0",
        source_route_ids=("route_p0",),
    )
    return Layer04RoutePlan(
        version=LAYER04_ROUTE_PLAN_VERSION,
        resource_kind="shape",
        transport_kind="space_belt",
        routes=(),
        groups=(),
        transport_tiles=(tile,),
        failures=(),
        metrics=Layer04Metrics(source_count=1, routed_source_count=1),
    )


def test_replay_uses_transport_tiles_not_probe_path() -> None:
    frames = build_layer04_transport_frames(_plan_with_tiles())
    kinds = {c.kind for spec in frames for c in spec.transient_overlay_cells}
    assert OVERLAY_KIND_ROUTE_PROBE_PATH not in kinds
    assert any(k.startswith("space_") for k in kinds)
    assert "SpaceBelt_Forward" in {c.tile_type for spec in frames for c in spec.transient_overlay_cells}


def test_replay_begin_and_complete_share_overlays() -> None:
    frames = build_layer04_transport_frames(_plan_with_tiles())
    assert len(frames) == 2
    begin_cells = frames[0].transient_overlay_cells
    complete_cells = frames[1].transient_overlay_cells
    assert begin_cells == complete_cells
    assert len(begin_cells) >= 1


def test_replay_falls_back_to_route_path_when_projection_empty() -> None:
    from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
        CommittedRoute,
    )

    plan = Layer04RoutePlan(
        version=LAYER04_ROUTE_PLAN_VERSION,
        resource_kind="shape",
        transport_kind="space_belt",
        routes=(
            CommittedRoute(
                route_id="route_p0",
                placement_id="p0",
                path_coords=((0, 0), (1, 0), (1, 1)),
                group_id="conn_c0",
                route_cost=3,
            ),
        ),
        groups=(),
        transport_tiles=(),
        failures=(),
        metrics=Layer04Metrics(source_count=1, routed_source_count=1),
    )
    frames = build_layer04_transport_frames(plan)
    kinds = {c.kind for spec in frames for c in spec.transient_overlay_cells}
    assert kinds == {OVERLAY_KIND_ROUTE_PROBE_PATH}
    assert frames[0].metrics.get("replay_overlay_mode") == "route_path_fallback"
