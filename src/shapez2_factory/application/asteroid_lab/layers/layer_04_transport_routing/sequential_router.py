"""Sequential merge-aware Layer 04 transport router."""

from __future__ import annotations

from shapez2_factory.adapters.asteroid_lab.space_transport_catalog_snapshot import (
    SpaceTransportTileCatalog,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
    LAYER04_ROUTE_PLAN_VERSION,
    CommittedRoute,
    Layer04Failure,
    Layer04FailureReason,
    Layer04Metrics,
    Layer04RoutePlan,
    ProjectedTransportTile,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    IntegratedRimGreedyResult,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.route_goal import (
    RouteGoal,
    build_layer03_route_goals,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.astar import (
    astar_to_nearest_goal,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.commit_validator import (  # noqa: E501
    L4CommitValidator,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.merge_groups import (  # noqa: E501
    RouteGroupRegistry,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.mvp_router import (  # noqa: E501
    L4_FLUID_UNIT_CAPACITY_M,
    L4_SHAPE_UNIT_CAPACITY_M,
    _collect_equipment,
    _sort_sources,
    _transport_kind_enum,
    _transport_kind_for_resource,
    _unit_capacity_m,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.route_domain import (  # noqa: E501
    build_l4_route_search_domain,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.source_adapter import (  # noqa: E501
    build_layer04_sources,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.sprite_projector import (  # noqa: E501
    project_routes_to_tiles,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)


def _connector_goals_with_capacity(
    connector_goals: tuple[RouteGoal, ...],
    registry: RouteGroupRegistry,
) -> tuple[RouteGoal, ...]:
    out: list[RouteGoal] = []
    for goal in connector_goals:
        gid = registry.connector_group(goal.goal_id)
        if registry.remaining_m(gid) > 0:
            out.append(goal)
    return tuple(out)


def _build_goal_set(
    connector_goals: tuple[RouteGoal, ...],
    registry: RouteGroupRegistry,
) -> tuple[RouteGoal, ...]:
    trunk = registry.trunk_goals()
    connector = _connector_goals_with_capacity(connector_goals, registry)
    return connector + trunk


def _route_not_found_detail(
    *,
    source_id: str,
    interior_occupied_cells: frozenset[tuple[int, int]],
    equipment_cells: frozenset[tuple[int, int]],
) -> str:
    return (
        f"source_id={source_id};"
        f"blocked_by_l4_interior_count={len(interior_occupied_cells)};"
        f"blocked_by_equipment_count={len(equipment_cells)}"
    )


def route_layer04_sequential(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan,
    rim_result: IntegratedRimGreedyResult,
    resource_kind: str,
    transport_catalog: SpaceTransportTileCatalog | None = None,
    interior_occupied_cells: frozenset[tuple[int, int]] = frozenset(),
) -> Layer04RoutePlan:
    transport_kind_slug = _transport_kind_for_resource(resource_kind)
    transport_enum = _transport_kind_enum(resource_kind)
    sources = build_layer04_sources(rim_result)
    if not sources:
        return Layer04RoutePlan(
            version=LAYER04_ROUTE_PLAN_VERSION,
            resource_kind=resource_kind,
            transport_kind=transport_kind_slug,
            routes=(),
            groups=(),
            transport_tiles=(),
            failures=(
                Layer04Failure(
                    placement_id=None,
                    reason=Layer04FailureReason.EMPTY_L3_PACKAGE,
                ),
            ),
            metrics=Layer04Metrics(),
        )

    connector_goals = build_layer03_route_goals(exterior_plan, transport_kind=transport_enum)
    if not connector_goals:
        return Layer04RoutePlan(
            version=LAYER04_ROUTE_PLAN_VERSION,
            resource_kind=resource_kind,
            transport_kind=transport_kind_slug,
            routes=(),
            groups=(),
            transport_tiles=(),
            failures=(
                Layer04Failure(
                    placement_id=None,
                    reason=Layer04FailureReason.NO_CONNECTOR_WITH_CAPACITY,
                ),
            ),
            metrics=Layer04Metrics(source_count=len(sources)),
        )

    miner_cells, extension_cells = _collect_equipment(rim_result)
    equipment_cells = miner_cells | extension_cells
    interior_block = frozenset(interior_occupied_cells)
    domain = build_l4_route_search_domain(
        complete_map=complete_map,
        miner_cells=miner_cells,
        extension_cells=extension_cells,
        interior_occupied_cells=interior_block,
    )
    stub_cells = frozenset(s.m_output_stub for s in sources)
    connector_cells = frozenset(g.coord for g in connector_goals)
    registry = RouteGroupRegistry(
        unit_capacity_m=_unit_capacity_m(resource_kind),
        transport_kind=transport_enum,
    )
    for goal in connector_goals:
        registry.connector_group(goal.goal_id)

    routes: list[CommittedRoute] = []
    failures: list[Layer04Failure] = []

    for source in _sort_sources(sources, connector_goals):
        goals = _build_goal_set(connector_goals, registry)
        if not goals:
            failures.append(
                Layer04Failure(
                    placement_id=source.placement_id,
                    reason=Layer04FailureReason.NO_CONNECTOR_WITH_CAPACITY,
                )
            )
            continue

        result = astar_to_nearest_goal(
            domain=domain,
            start=source.m_output_stub,
            goals=goals,
        )
        if result is None:
            failures.append(
                Layer04Failure(
                    placement_id=source.placement_id,
                    reason=Layer04FailureReason.ROUTE_NOT_FOUND,
                    detail=_route_not_found_detail(
                        source_id=source.placement_id,
                        interior_occupied_cells=interior_block,
                        equipment_cells=equipment_cells,
                    ),
                )
            )
            continue

        if result.goal_coord in connector_cells:
            target_gid = registry.connector_group(result.goal_id)
        else:
            cell_group = registry.group_at_cell(result.goal_coord)
            if cell_group is None:
                failures.append(
                    Layer04Failure(
                        placement_id=source.placement_id,
                        reason=Layer04FailureReason.ROUTE_NOT_FOUND,
                        detail="trunk_goal_missing_group",
                    )
                )
                continue
            target_gid = cell_group
        if registry.remaining_m(target_gid) < source.source_load_m:
            failures.append(
                Layer04Failure(
                    placement_id=source.placement_id,
                    reason=Layer04FailureReason.CAPACITY_OVERFLOW,
                    detail=result.goal_id,
                )
            )
            continue

        trunk_attach = registry.trunk_goals()
        trunk_cells = frozenset(g.coord for g in trunk_attach)
        commit_validator = L4CommitValidator(
            equipment_cells=equipment_cells,
            connector_cells=connector_cells,
            stub_cells=stub_cells,
            interior_occupied_cells=interior_block,
            trunk_attach_cells=trunk_cells,
        )
        commit_err = commit_validator.validate_path(result.path)
        if commit_err is not None:
            failures.append(
                Layer04Failure(
                    placement_id=source.placement_id,
                    reason=commit_err,
                )
            )
            continue

        is_connector = result.goal_coord in connector_cells
        connector_id = result.goal_id if is_connector else None
        group_id = registry.commit_path(
            path=result.path,
            placement_id=source.placement_id,
            connector_id=connector_id,
            source_load_m=source.source_load_m,
        )
        routes.append(
            CommittedRoute(
                route_id=f"route_{source.placement_id}",
                placement_id=source.placement_id,
                path_coords=result.path,
                group_id=group_id,
                route_cost=result.route_cost,
            )
        )

    groups = registry.summaries(transport_kind_slug=transport_kind_slug)
    committed_routes = tuple(routes)
    transport_tiles: tuple[ProjectedTransportTile, ...] = ()
    if transport_catalog is not None and committed_routes:
        transport_tiles = project_routes_to_tiles(
            routes=committed_routes,
            transport_kind=transport_kind_slug,
            catalog=transport_catalog,
        )
        if not transport_tiles:
            failures.append(
                Layer04Failure(
                    placement_id=None,
                    reason=Layer04FailureReason.UNSUPPORTED_IO_SIGNATURE,
                    detail="sprite_projection_produced_no_tiles",
                )
            )

    return Layer04RoutePlan(
        version=LAYER04_ROUTE_PLAN_VERSION,
        resource_kind=resource_kind,
        transport_kind=transport_kind_slug,
        routes=committed_routes,
        groups=groups,
        transport_tiles=transport_tiles,
        failures=tuple(failures),
        metrics=Layer04Metrics(
            source_count=len(sources),
            routed_source_count=len(routes),
            failed_source_count=len(failures),
            total_route_cells=sum(len(r.path_coords) for r in routes),
            total_route_cost=sum(r.route_cost for r in routes),
        ),
    )


__all__ = [
    "L4_FLUID_UNIT_CAPACITY_M",
    "L4_SHAPE_UNIT_CAPACITY_M",
    "route_layer04_sequential",
]
