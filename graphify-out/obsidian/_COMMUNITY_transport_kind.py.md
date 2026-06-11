---
type: community
cohesion: 0.43
members: 7
---

# transport_kind.py

**Cohesion:** 0.43 - moderately connected
**Members:** 7 nodes

## Members
- [[Layer 03 resource vs transport kind enums and L2 plan string mapping.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/contracts/transport_kind.py
- [[ResourceKind_2]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/transport_kind.py
- [[TransportKind_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/transport_kind.py
- [[map_resource_kind_to_transport_kind()]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/transport_kind.py
- [[resource_kind_from_plan_string()]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/transport_kind.py
- [[transport_kind.py]] - code - django_apps/asteroid_lab/layers/contracts/transport_kind.py
- [[transport_kind.py_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/transport_kind.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/transport_kindpy
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_StrEnum]]
- 1 edge to [[_COMMUNITY_Enum]]
- 1 edge to [[_COMMUNITY_generate_candidates()]]
- 1 edge to [[_COMMUNITY_build_layer03_transport_profiles()]]

## Top bridge nodes
- [[map_resource_kind_to_transport_kind()]] - degree 5, connects to 2 communities
- [[transport_kind.py_1]] - degree 6, connects to 1 community
- [[ResourceKind_2]] - degree 4, connects to 1 community
- [[TransportKind_1]] - degree 3, connects to 1 community