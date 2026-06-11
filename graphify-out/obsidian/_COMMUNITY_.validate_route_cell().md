---
type: community
cohesion: 0.47
members: 6
---

# .validate_route_cell()

**Cohesion:** 0.47 - moderately connected
**Members:** 6 nodes

## Members
- [[.validate_path()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/commit_validator.py
- [[.validate_route_cell()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/commit_validator.py
- [[Commit-time overlap rules for Layer 04 transport tiles.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/commit_validator.py
- [[L4CommitValidator]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/commit_validator.py
- [[Layer04FailureReason]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/commit_validator.py
- [[commit_validator.py]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/commit_validator.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/validate_route_cell
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_Coord]]
- 1 edge to [[_COMMUNITY_route_layer04_sequential()]]

## Top bridge nodes
- [[L4CommitValidator]] - degree 4, connects to 1 community
- [[.validate_route_cell()]] - degree 4, connects to 1 community
- [[.validate_path()]] - degree 4, connects to 1 community