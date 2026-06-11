---
type: community
cohesion: 0.18
members: 18
---

# placement.py

**Cohesion:** 0.18 - loosely connected
**Members:** 18 nodes

## Members
- [[CardinalEdge_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/slots.py
- [[EDGE_WEIGHTED_EVEN_SPACING_V1 connector count and slot selection.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/placement.py
- [[InsufficientConnectorSlotsError]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/placement.py
- [[NoConnectorSlotsError]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/placement.py
- [[Pick spare connectors as far from required slots as the edge allows.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/placement.py
- [[Raised when even slot selection needs more slots than available.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/placement.py
- [[Raised when no candidate slots exist for distribution.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/placement.py
- [[_is_between_required()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/placement.py
- [[_min_index_distance()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/placement.py
- [[_spare_candidate_rank()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/placement.py
- [[choose_even_slots()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/placement.py
- [[choose_spare_slots()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/placement.py
- [[distribute_connector_counts()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/placement.py
- [[even_slot_index()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/placement.py
- [[nearest_unused_index()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/placement.py
- [[placement.py]] - code - django_apps/asteroid_lab/layers/layer_02_exterior_transport/placement.py
- [[placement.py_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/placement.py
- [[remaining_slots_after_selection()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/placement.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/placementpy
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_Coord]]
- 4 edges to [[_COMMUNITY_Decimal]]
- 2 edges to [[_COMMUNITY_ValueError]]
- 1 edge to [[_COMMUNITY_ReconstructionCompleteMap]]

## Top bridge nodes
- [[choose_spare_slots()]] - degree 8, connects to 2 communities
- [[choose_even_slots()]] - degree 7, connects to 2 communities
- [[distribute_connector_counts()]] - degree 5, connects to 2 communities
- [[CardinalEdge_1]] - degree 4, connects to 2 communities
- [[InsufficientConnectorSlotsError]] - degree 5, connects to 1 community