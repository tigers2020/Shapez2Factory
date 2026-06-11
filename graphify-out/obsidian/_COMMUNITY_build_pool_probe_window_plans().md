---
type: community
cohesion: 0.31
members: 9
---

# build_pool_probe_window_plans()

**Cohesion:** 0.31 - loosely connected
**Members:** 9 nodes

## Members
- [[L3 replay candidate observation overlay projection (output-only).]] - rationale - django_apps/asteroid_lab/replay/layer03_overlay_cells.py
- [[L3 replay pool logical windows and cell-budget physical sub-split (projection on]] - rationale - django_apps/asteroid_lab/replay/layer03_pool_windowing.py
- [[PoolProbeWindowPlan]] - code - django_apps/asteroid_lab/replay/layer03_pool_windowing.py
- [[_split_chunk_for_cell_budget()]] - code - django_apps/asteroid_lab/replay/layer03_pool_windowing.py
- [[build_pool_probe_window_plans()]] - code - django_apps/asteroid_lab/replay/layer03_pool_windowing.py
- [[layer03_overlay_cells.py]] - code - django_apps/asteroid_lab/replay/layer03_overlay_cells.py
- [[layer03_pool_windowing.py]] - code - django_apps/asteroid_lab/replay/layer03_pool_windowing.py
- [[overlay_cell_count_for_candidate()]] - code - django_apps/asteroid_lab/replay/layer03_overlay_cells.py
- [[overlay_for_probed()]] - code - django_apps/asteroid_lab/replay/layer03_overlay_cells.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/build_pool_probe_window_plans
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_RouteProbedBundleCandidate]]
- 2 edges to [[_COMMUNITY_build_layer03_runtime_segment_specs()]]
- 1 edge to [[_COMMUNITY_ReplayOverlayCell]]

## Top bridge nodes
- [[overlay_for_probed()]] - degree 5, connects to 3 communities
- [[build_pool_probe_window_plans()]] - degree 5, connects to 2 communities
- [[overlay_cell_count_for_candidate()]] - degree 4, connects to 1 community
- [[_split_chunk_for_cell_budget()]] - degree 4, connects to 1 community