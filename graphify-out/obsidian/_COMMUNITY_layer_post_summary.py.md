---
type: community
cohesion: 0.40
members: 5
---

# layer_post_summary.py

**Cohesion:** 0.40 - moderately connected
**Members:** 5 nodes

## Members
- [[LayerPostSummaryOutcome_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/layer_post_summary.py
- [[LayerPostSummaryRecord_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/layer_post_summary.py
- [[Per-layer post-run summary records (observability only; not stack input).]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/contracts/layer_post_summary.py
- [[layer_post_summary.py]] - code - django_apps/asteroid_lab/layers/contracts/layer_post_summary.py
- [[layer_post_summary.py_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/layer_post_summary.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/layer_post_summarypy
SORT file.name ASC
```

## Connections to other communities
- 1 edge to [[_COMMUNITY_StrEnum]]
- 1 edge to [[_COMMUNITY_Enum]]

## Top bridge nodes
- [[layer_post_summary.py_1]] - degree 4, connects to 1 community
- [[LayerPostSummaryOutcome_1]] - degree 2, connects to 1 community