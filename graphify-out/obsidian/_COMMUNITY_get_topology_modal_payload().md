---
type: community
cohesion: 0.18
members: 11
---

# get_topology_modal_payload()

**Cohesion:** 0.18 - loosely connected
**Members:** 11 nodes

## Members
- [[Catalog row shown beside modal content.]] - rationale - src/shapez2_factory/domain/asteroid_lab/service_dtos.py
- [[Joined rule + modal content for topology help UI.]] - rationale - src/shapez2_factory/domain/asteroid_lab/service_dtos.py
- [[Load ``TopologyRule`` joined with ``TopologyRuleModalContent``.      Returns a]] - rationale - django_apps/asteroid_lab/services/topology_service.py
- [[Rich modal body (UI only).]] - rationale - src/shapez2_factory/domain/asteroid_lab/service_dtos.py
- [[Topology rule catalog + modal payloads (help UI only).]] - rationale - django_apps/asteroid_lab/services/topology_service.py
- [[TopologyModalBodyDTO]] - code - src/shapez2_factory/domain/asteroid_lab/service_dtos.py
- [[TopologyModalPayloadDTO]] - code - src/shapez2_factory/domain/asteroid_lab/service_dtos.py
- [[TopologyModalResultDTO]] - code - django_apps/asteroid_lab/services/topology_service.py
- [[TopologyRuleSummaryDTO]] - code - src/shapez2_factory/domain/asteroid_lab/service_dtos.py
- [[get_topology_modal_payload()]] - code - django_apps/asteroid_lab/services/topology_service.py
- [[topology_service.py]] - code - django_apps/asteroid_lab/services/topology_service.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/get_topology_modal_payload
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_service_dtos.py]]

## Top bridge nodes
- [[TopologyRuleSummaryDTO]] - degree 3, connects to 1 community
- [[TopologyModalBodyDTO]] - degree 3, connects to 1 community
- [[TopologyModalPayloadDTO]] - degree 3, connects to 1 community