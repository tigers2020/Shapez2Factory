---
type: community
cohesion: 0.15
members: 17
---

# bbox_from_coords()

**Cohesion:** 0.15 - loosely connected
**Members:** 17 nodes

## Members
- [[.step_cost()_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/route_domain.py
- [[All integer grid coords inside inclusive ``bb``.]] - rationale - src/shapez2_factory/domain/asteroid_lab/grid_contract.py
- [[BBox_1]] - code - src/shapez2_factory/domain/asteroid_lab/grid_contract.py
- [[Expand inclusive bbox by ``padding`` cells on each side.]] - rationale - src/shapez2_factory/domain/asteroid_lab/grid_contract.py
- [[Inclusive bbox over ``coords``; empty becomes ``BBox(0, 0, 0, 0)``.]] - rationale - src/shapez2_factory/domain/asteroid_lab/grid_contract.py
- [[Inclusive topology bounding box in the active raw coordinate frame.]] - rationale - src/shapez2_factory/domain/asteroid_lab/grid_contract.py
- [[Integer topology grid helpers (reconstruction + optimization + lab).  ``Coord`]] - rationale - src/shapez2_factory/domain/asteroid_lab/grid_contract.py
- [[L4 weighted route search domain (separate from L3 ``WeightedTransportRouteDomain]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/route_domain.py
- [[L4RouteSearchDomain_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/route_domain.py
- [[L4TerrainKind]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/route_domain.py
- [[bbox_from_coords()]] - code - src/shapez2_factory/domain/asteroid_lab/grid_contract.py
- [[build_l4_route_search_domain()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/route_domain.py
- [[cells_in_bbox()]] - code - src/shapez2_factory/domain/asteroid_lab/grid_contract.py
- [[expand_bbox()]] - code - src/shapez2_factory/domain/asteroid_lab/grid_contract.py
- [[grid_contract.py]] - code - src/shapez2_factory/domain/asteroid_lab/grid_contract.py
- [[route_domain.py]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/route_domain.py
- [[terrain_kind_at()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/route_domain.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/bbox_from_coords
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_Coord]]
- 3 edges to [[_COMMUNITY_ReconstructionResult]]
- 2 edges to [[_COMMUNITY_ReconstructionCompleteMap]]
- 1 edge to [[_COMMUNITY_generate_candidates()]]
- 1 edge to [[_COMMUNITY_ExteriorConnectionPlan]]
- 1 edge to [[_COMMUNITY_route_layer04_sequential()]]
- 1 edge to [[_COMMUNITY_build_normalized_reconstruction_topology]]

## Top bridge nodes
- [[bbox_from_coords()]] - degree 11, connects to 6 communities
- [[build_l4_route_search_domain()]] - degree 7, connects to 3 communities
- [[cells_in_bbox()]] - degree 5, connects to 2 communities
- [[grid_contract.py]] - degree 6, connects to 1 community
- [[terrain_kind_at()]] - degree 4, connects to 1 community