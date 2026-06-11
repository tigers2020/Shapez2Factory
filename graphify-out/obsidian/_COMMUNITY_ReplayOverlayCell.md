---
type: community
cohesion: 0.20
members: 24
---

# ReplayOverlayCell

**Cohesion:** 0.20 - loosely connected
**Members:** 24 nodes

## Members
- [[Build ``pattern_bundle_highlights`` metrics payload or ``{}`` when empty.]] - rationale - django_apps/asteroid_lab/replay/pattern_bundle_highlight.py
- [[Layer 04 rim provisional placement replay segment (legacy L4 bundle packing obse]] - rationale - django_apps/asteroid_lab/replay/layer04_segment.py
- [[Layer04PackingObservability]] - code - django_apps/asteroid_lab/replay/layer04_segment.py
- [[Map L4 observation role to domain cell_kind for Lab sprite resolution.]] - rationale - django_apps/asteroid_lab/replay/layer04_segment.py
- [[ReplayOverlayCell]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[RimBundlePlacement]] - code - django_apps/asteroid_lab/replay/layer04_segment.py
- [[RimPlacementRejection]] - code - django_apps/asteroid_lab/replay/layer04_segment.py
- [[Transient L4 observation specs; assembler composes persistent exterior overlays.]] - rationale - django_apps/asteroid_lab/replay/layer04_segment.py
- [[_combined_overlay_for_placements()_1]] - code - django_apps/asteroid_lab/replay/layer04_segment.py
- [[_overlay_cells_for_overlap_rejection()]] - code - django_apps/asteroid_lab/replay/layer04_segment.py
- [[_overlay_cells_for_placement()]] - code - django_apps/asteroid_lab/replay/layer04_segment.py
- [[_overlay_cells_for_placement_legacy()]] - code - django_apps/asteroid_lab/replay/layer04_segment.py
- [[_overlay_cells_from_bundle_cell_placements()]] - code - django_apps/asteroid_lab/replay/layer04_segment.py
- [[_overlay_kind_for_cell_role()]] - code - django_apps/asteroid_lab/replay/layer04_segment.py
- [[_overlay_kind_for_role()]] - code - django_apps/asteroid_lab/replay/layer04_segment.py
- [[_overlay_route_probe_path_cells()]] - code - django_apps/asteroid_lab/replay/layer04_segment.py
- [[_packing_observability_metrics()]] - code - django_apps/asteroid_lab/replay/layer04_segment.py
- [[_pattern_bundle_highlights_for_placement()]] - code - django_apps/asteroid_lab/replay/layer04_segment.py
- [[_pattern_bundle_highlights_for_placements()]] - code - django_apps/asteroid_lab/replay/layer04_segment.py
- [[_placement_metadata()]] - code - django_apps/asteroid_lab/replay/layer04_segment.py
- [[_spec()_3]] - code - django_apps/asteroid_lab/replay/layer04_segment.py
- [[build_layer04_runtime_segment_specs()]] - code - django_apps/asteroid_lab/replay/layer04_segment.py
- [[build_pattern_bundle_highlights_wire()]] - code - django_apps/asteroid_lab/replay/pattern_bundle_highlight.py
- [[layer04_segment.py]] - code - django_apps/asteroid_lab/replay/layer04_segment.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/ReplayOverlayCell
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_ReplayEventType]]
- 7 edges to [[_COMMUNITY_build_solver_runtime_replay_frames()]]
- 6 edges to [[_COMMUNITY_layer03_rim_greedy_segment.py]]
- 5 edges to [[_COMMUNITY_lab_timeline_adapter.py]]
- 4 edges to [[_COMMUNITY_pattern_bundle_highlight.py]]
- 3 edges to [[_COMMUNITY_build_layer03_runtime_segment_specs()]]
- 1 edge to [[_COMMUNITY_Coord]]
- 1 edge to [[_COMMUNITY_build_terrain_rim_highlight_from_rendera]]
- 1 edge to [[_COMMUNITY_build_pool_probe_window_plans()]]
- 1 edge to [[_COMMUNITY_timeline_serialization.py]]
- 1 edge to [[_COMMUNITY_ExteriorConnectionPlan]]
- 1 edge to [[_COMMUNITY_enrich_lab_timeline_frames_with_terrain_]]

## Top bridge nodes
- [[ReplayOverlayCell]] - degree 30, connects to 7 communities
- [[build_pattern_bundle_highlights_wire()]] - degree 10, connects to 6 communities
- [[_spec()_3]] - degree 6, connects to 2 communities
- [[build_layer04_runtime_segment_specs()]] - degree 15, connects to 1 community
- [[_pattern_bundle_highlights_for_placement()]] - degree 5, connects to 1 community