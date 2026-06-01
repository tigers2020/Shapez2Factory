"""Deprecated L4 transport replay path; delegates to ``layer05_transport_segment``."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.layer05_transport_segment import (
    LAYER05_TRANSPORT_PHASE,
    OVERLAY_KIND_ROUTE_PROBE_PATH,
    build_layer05_transport_frames,
)
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
    Layer04RoutePlan,
)

LAYER04_TRANSPORT_PHASE = "layer_04_transport_routing"


def build_layer04_transport_frames(
    plan: Layer04RoutePlan,
) -> tuple[object, ...]:
    return build_layer05_transport_frames(
        plan,
        event_types=(
            ReplayEventType.LAYER04_TRANSPORT_ROUTING_BEGIN,
            ReplayEventType.LAYER04_TRANSPORT_ROUTING_COMPLETE,
        ),
    )


__all__ = [
    "LAYER04_TRANSPORT_PHASE",
    "LAYER05_TRANSPORT_PHASE",
    "OVERLAY_KIND_ROUTE_PROBE_PATH",
    "build_layer04_transport_frames",
]
