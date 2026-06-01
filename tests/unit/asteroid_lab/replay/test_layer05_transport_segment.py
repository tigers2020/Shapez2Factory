"""Layer 05 transport routing replay segment (canonical wire)."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.event_types import (
    EVENT_TYPE_LAYER04_TRANSPORT_ROUTING_BEGIN,
    EVENT_TYPE_LAYER05_TRANSPORT_ROUTING_BEGIN,
    is_registered_event_type,
)
from django_apps.asteroid_lab.replay.layer05_transport_segment import (
    build_layer05_transport_frames,
)
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType
from shapez2_factory.application.asteroid_lab.layers.contracts.layer05_route import (
    LAYER05_ROUTE_PLAN_VERSION,
    Layer05Metrics,
    Layer05RoutePlan,
    ProjectedTransportTile,
)


def _minimal_plan() -> Layer05RoutePlan:
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
    return Layer05RoutePlan(
        version=LAYER05_ROUTE_PLAN_VERSION,
        resource_kind="shape",
        transport_kind="space_belt",
        routes=(),
        groups=(),
        transport_tiles=(tile,),
        failures=(),
        metrics=Layer05Metrics(source_count=1, routed_source_count=1),
    )


def test_transport_segment_emits_layer05_event_types() -> None:
    frames = build_layer05_transport_frames(_minimal_plan())
    assert frames[0].event_type == ReplayEventType.LAYER05_TRANSPORT_ROUTING_BEGIN
    assert frames[1].event_type == ReplayEventType.LAYER05_TRANSPORT_ROUTING_COMPLETE


def test_deprecated_layer04_event_types_remain_registered() -> None:
    assert is_registered_event_type(EVENT_TYPE_LAYER04_TRANSPORT_ROUTING_BEGIN)
    assert is_registered_event_type(EVENT_TYPE_LAYER05_TRANSPORT_ROUTING_BEGIN)
