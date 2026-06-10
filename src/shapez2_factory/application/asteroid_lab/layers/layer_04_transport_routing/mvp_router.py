"""Layer 04 shared router helpers + MVP delegate to sequential router."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
    Layer04RoutePlan,
    Layer04SourceView,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    IntegratedRimGreedyResult,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.route_goal import (
    RouteGoal,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import (
    TransportKind,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)

L4_SHAPE_UNIT_CAPACITY_M = 12
L4_FLUID_UNIT_CAPACITY_M = 72


def _transport_kind_for_resource(resource_kind: str) -> str:
    return "space_pipe" if resource_kind == "fluid" else "space_belt"


def _transport_kind_enum(resource_kind: str) -> TransportKind:
    return TransportKind.FLUID_PIPE if resource_kind == "fluid" else TransportKind.SHAPE_BELT


def _unit_capacity_m(resource_kind: str) -> int:
    return L4_FLUID_UNIT_CAPACITY_M if resource_kind == "fluid" else L4_SHAPE_UNIT_CAPACITY_M


def _manhattan(a: Coord, b: Coord) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _nearest_goal_estimate(source: Layer04SourceView, goals: tuple[RouteGoal, ...]) -> int:
    if not goals:
        return 0
    return min(_manhattan(source.m_output_stub, g.coord) for g in goals)


def _sort_sources(
    sources: tuple[Layer04SourceView, ...],
    goals: tuple[RouteGoal, ...],
) -> tuple[Layer04SourceView, ...]:
    return tuple(
        sorted(
            sources,
            key=lambda s: (
                -_nearest_goal_estimate(s, goals),
                -s.source_load_m,
                s.m_output_stub[0],
                s.m_output_stub[1],
                s.placement_id,
            ),
        )
    )


def _collect_equipment(
    rim_result: IntegratedRimGreedyResult,
) -> tuple[frozenset[Coord], frozenset[Coord]]:
    miners: set[Coord] = set()
    extensions: set[Coord] = set()
    for placement in rim_result.committed_placements:
        miners |= set(placement.miner_cells)
        extensions |= set(placement.extension_cells)
    return frozenset(miners), frozenset(extensions)


def route_layer04_mvp(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan,
    rim_result: IntegratedRimGreedyResult,
    resource_kind: str,
) -> Layer04RoutePlan:
    from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.sequential_router import (  # noqa: E501
        route_layer04_sequential,
    )

    return route_layer04_sequential(
        complete_map=complete_map,
        exterior_plan=exterior_plan,
        rim_result=rim_result,
        resource_kind=resource_kind,
        transport_catalog=None,
    )


__all__ = [
    "L4_FLUID_UNIT_CAPACITY_M",
    "L4_SHAPE_UNIT_CAPACITY_M",
    "_collect_equipment",
    "_manhattan",
    "_nearest_goal_estimate",
    "_sort_sources",
    "_transport_kind_enum",
    "_transport_kind_for_resource",
    "_unit_capacity_m",
    "route_layer04_mvp",
]
