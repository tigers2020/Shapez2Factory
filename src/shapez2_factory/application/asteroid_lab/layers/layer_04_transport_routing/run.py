"""Layer 04 transport routing orchestrator (PR-L4-0 stub)."""

from __future__ import annotations

from shapez2_factory.adapters.asteroid_lab.space_transport_catalog_snapshot import (
    SpaceTransportTileCatalog,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
    LAYER04_ROUTE_PLAN_VERSION,
    Layer04Failure,
    Layer04FailureReason,
    Layer04Metrics,
    Layer04RoutePlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_inner_fill import (
    Layer04InnerFillResult,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    IntegratedRimGreedyResult,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import (
    ResourceKind,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.sequential_router import (  # noqa: E501
    route_layer04_sequential,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)


def run_layer_05_transport_routing(
    *,
    complete_map: ReconstructionCompleteMap | None = None,
    exterior_plan: ExteriorConnectionPlan | None = None,
    rim_result: IntegratedRimGreedyResult | None = None,
    resource_kind: ResourceKind | str | None = None,
    budget_ctx: LayerBudgetContext | None = None,
    transport_catalog: SpaceTransportTileCatalog | None = None,
    interior_occupied_cells: frozenset[tuple[int, int]] | None = None,
    inner_fill: Layer04InnerFillResult | None = None,
) -> Layer04RoutePlan:
    """MVP routing when map + rim + exterior plan are present (canonical L5 slug)."""
    _ = budget_ctx
    interior = (
        frozenset(interior_occupied_cells) if interior_occupied_cells is not None else frozenset()
    )
    if exterior_plan is None:
        return Layer04RoutePlan(
            version=LAYER04_ROUTE_PLAN_VERSION,
            resource_kind="",
            transport_kind="",
            routes=(),
            groups=(),
            transport_tiles=(),
            failures=(
                Layer04Failure(
                    placement_id=None,
                    reason=Layer04FailureReason.MISSING_L2_EXTERIOR_PLAN,
                ),
            ),
            metrics=Layer04Metrics(),
        )
    if isinstance(resource_kind, ResourceKind):
        rk = resource_kind.value
    else:
        rk = resource_kind or "shape"
    if complete_map is None or rim_result is None:
        tk = "space_belt" if rk == "shape" else "space_pipe"
        return Layer04RoutePlan.empty(resource_kind=rk, transport_kind=tk)
    return route_layer04_sequential(
        complete_map=complete_map,
        exterior_plan=exterior_plan,
        rim_result=rim_result,
        resource_kind=rk,
        transport_catalog=transport_catalog,
        interior_occupied_cells=interior,
        inner_fill=inner_fill,
    )


run_layer_04_transport_routing = run_layer_05_transport_routing

__all__ = ["run_layer_04_transport_routing", "run_layer_05_transport_routing"]
