---
type: community
cohesion: 0.33
members: 6
---

# build_layer05_transport_post_summary_met

**Cohesion:** 0.33 - loosely connected
**Members:** 6 nodes

## Members
- [[Layer 04 transport routing post-summary metrics (pure core).]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/observability/layer04_post_summary_metrics.py
- [[Layer 05 transport routing post-summary metrics (canonical L5 slug).]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/observability/layer05_post_summary_metrics.py
- [[build_layer04_transport_post_summary_metrics()]] - code - src/shapez2_factory/application/asteroid_lab/layers/observability/layer04_post_summary_metrics.py
- [[build_layer05_transport_post_summary_metrics()]] - code - src/shapez2_factory/application/asteroid_lab/layers/observability/layer05_post_summary_metrics.py
- [[layer04_post_summary_metrics.py]] - code - src/shapez2_factory/application/asteroid_lab/layers/observability/layer04_post_summary_metrics.py
- [[layer05_post_summary_metrics.py]] - code - src/shapez2_factory/application/asteroid_lab/layers/observability/layer05_post_summary_metrics.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/build_layer05_transport_post_summary_met
SORT file.name ASC
```

## Connections to other communities
- 1 edge to [[_COMMUNITY_route_layer04_sequential()]]
- 1 edge to [[_COMMUNITY_ReplayEventType]]
- 1 edge to [[_COMMUNITY_run_layers_02_to_06()]]

## Top bridge nodes
- [[build_layer05_transport_post_summary_metrics()]] - degree 4, connects to 2 communities
- [[build_layer04_transport_post_summary_metrics()]] - degree 3, connects to 1 community