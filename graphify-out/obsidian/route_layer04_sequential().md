---
source_file: "src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sequential_router.py"
type: "code"
community: "route_layer04_sequential()"
location: "L108"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/route_layer04_sequential
---

# route_layer04_sequential()

## Connections
- [[ExteriorConnectionPlan]] - `references` [EXTRACTED]
- [[IntegratedRimGreedyResult]] - `references` [EXTRACTED]
- [[L4CommitValidator]] - `calls` [INFERRED]
- [[Layer04InnerFillResult]] - `references` [EXTRACTED]
- [[Layer04RoutePlan]] - `calls` [EXTRACTED]
- [[ReconstructionCompleteMap]] - `references` [EXTRACTED]
- [[RouteGroupRegistry_1]] - `calls` [EXTRACTED]
- [[SpaceTransportTileCatalog]] - `references` [EXTRACTED]
- [[_build_goal_set()]] - `calls` [EXTRACTED]
- [[_collect_equipment()]] - `calls` [INFERRED]
- [[_route_not_found_detail()]] - `calls` [EXTRACTED]
- [[_sort_sources()]] - `calls` [INFERRED]
- [[_transport_kind_enum()]] - `calls` [INFERRED]
- [[_transport_kind_for_resource()]] - `calls` [INFERRED]
- [[_unit_capacity_m()]] - `calls` [INFERRED]
- [[astar_inner_source_via_space_lift()]] - `calls` [INFERRED]
- [[astar_to_nearest_goal()]] - `calls` [INFERRED]
- [[build_l4_route_search_domain()]] - `calls` [INFERRED]
- [[build_layer03_route_goals()]] - `calls` [INFERRED]
- [[build_layer04_sources()]] - `calls` [INFERRED]
- [[collect_inner_routeable_equipment()]] - `calls` [INFERRED]
- [[is_inner_lift_source()]] - `calls` [INFERRED]
- [[project_routes_to_tiles()]] - `calls` [INFERRED]
- [[route_layer04_mvp()]] - `calls` [INFERRED]
- [[run_layer_05_transport_routing()]] - `calls` [INFERRED]
- [[sequential_router.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/route_layer04_sequential