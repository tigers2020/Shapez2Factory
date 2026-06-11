---
type: community
cohesion: 0.35
members: 12
---

# build_layer03_runtime_segment_specs()

**Cohesion:** 0.35 - loosely connected
**Members:** 12 nodes

## Members
- [[Layer 03 rim bundle scan runtime replay segment (transient overlay specs only).]] - rationale - django_apps/asteroid_lab/replay/layer03_segment.py
- [[Layer03Observability]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/candidates.py
- [[PoolProbeWindowPlan_1]] - code - django_apps/asteroid_lab/replay/layer03_segment.py
- [[Transient L3 observation specs; assembler composes persistent exterior overlays.]] - rationale - django_apps/asteroid_lab/replay/layer03_segment.py
- [[_complete_metrics()]] - code - django_apps/asteroid_lab/replay/layer03_segment.py
- [[_overlay_for_plan()]] - code - django_apps/asteroid_lab/replay/layer03_segment.py
- [[_pattern_bundle_highlights_for_plan()]] - code - django_apps/asteroid_lab/replay/layer03_segment.py
- [[_pool_summary_metrics()]] - code - django_apps/asteroid_lab/replay/layer03_segment.py
- [[_probe_window_metrics()]] - code - django_apps/asteroid_lab/replay/layer03_segment.py
- [[_spec()_1]] - code - django_apps/asteroid_lab/replay/layer03_segment.py
- [[build_layer03_runtime_segment_specs()]] - code - django_apps/asteroid_lab/replay/layer03_segment.py
- [[layer03_segment.py]] - code - django_apps/asteroid_lab/replay/layer03_segment.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/build_layer03_runtime_segment_specs
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_ReplayOverlayCell]]
- 3 edges to [[_COMMUNITY_build_solver_runtime_replay_frames()]]
- 2 edges to [[_COMMUNITY_ReplayEventType]]
- 2 edges to [[_COMMUNITY_build_pool_probe_window_plans()]]
- 1 edge to [[_COMMUNITY_StrEnum]]

## Top bridge nodes
- [[_spec()_1]] - degree 6, connects to 3 communities
- [[build_layer03_runtime_segment_specs()]] - degree 11, connects to 2 communities
- [[_overlay_for_plan()]] - degree 5, connects to 2 communities
- [[Layer03Observability]] - degree 5, connects to 1 community
- [[_pattern_bundle_highlights_for_plan()]] - degree 4, connects to 1 community