"""Layer 03 transport profiles — space_belt / space_pipe expansion within one orchestrator."""

from __future__ import annotations

from dataclasses import dataclass

from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.route_goal import (
    RouteGoal,
    build_layer03_route_goals,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import (
    ResourceKind,
    TransportKind,
    map_resource_kind_to_transport_kind,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.resource_kinds import (
    detect_present_resource_kinds,
)

ANCHOR_FIELD_KIND_BY_TRANSPORT: dict[TransportKind, str] = {
    TransportKind.SPACE_BELT: ResourceKind.SHAPE.value,
    TransportKind.SPACE_PIPE: ResourceKind.FLUID.value,
}


@dataclass(frozen=True, slots=True)
class Layer03TransportProfile:
    """One L3 expansion pass: profile-local goals and transport kind."""

    transport_kind: TransportKind
    resource_kind: ResourceKind
    route_goals: tuple[RouteGoal, ...]


def build_layer03_transport_profiles(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan,
) -> tuple[Layer03TransportProfile, ...]:
    """Active profiles from reconstruction resource set (shape before fluid)."""

    if not exterior_plan.planned_connectors:
        return ()

    profiles: list[Layer03TransportProfile] = []
    for resource_value in detect_present_resource_kinds(complete_map):
        resource_kind = ResourceKind(resource_value)
        transport_kind = map_resource_kind_to_transport_kind(resource_kind)
        route_goals = build_layer03_route_goals(
            exterior_plan,
            transport_kind=transport_kind,
        )
        profiles.append(
            Layer03TransportProfile(
                transport_kind=transport_kind,
                resource_kind=resource_kind,
                route_goals=route_goals,
            ),
        )
    return tuple(profiles)


__all__ = [
    "ANCHOR_FIELD_KIND_BY_TRANSPORT",
    "Layer03TransportProfile",
    "build_layer03_transport_profiles",
]
