---
type: community
cohesion: 0.13
members: 24
---

# build_terrain_rim_highlight_from_rendera

**Cohesion:** 0.13 - loosely connected
**Members:** 24 nodes

## Members
- [[Chain undirected corner segments into closed loop(s).]] - rationale - django_apps/asteroid_lab/reconstruction/cell_hull_outline.py
- [[Closed outline loop(s) around ``occupied`` unit cells.]] - rationale - django_apps/asteroid_lab/reconstruction/cell_hull_outline.py
- [[Corner-lattice hull outlines for occupied unit cells (geometry only).  Used by]] - rationale - django_apps/asteroid_lab/reconstruction/cell_hull_outline.py
- [[JSON-serializable wire for ``metrics.terrain_rim_highlight``.]] - rationale - django_apps/asteroid_lab/reconstruction/rim_highlight.py
- [[ReplayUI enrichment only — not solver input.]] - rationale - django_apps/asteroid_lab/reconstruction/rim_highlight.py
- [[Rim + void edges from reconstruction-complete map SoT.]] - rationale - django_apps/asteroid_lab/reconstruction/rim_highlight.py
- [[Side segments on the hull where a 4-neighbor is outside ``occupied``.]] - rationale - django_apps/asteroid_lab/reconstruction/cell_hull_outline.py
- [[Terrain rim highlight DTO for Lab replay (UI observability only).]] - rationale - django_apps/asteroid_lab/reconstruction/rim_highlight.py
- [[TerrainRimHighlightDTO]] - code - django_apps/asteroid_lab/reconstruction/rim_highlight.py
- [[Validate and return canonical ``n````e````s````w`` edge string.]] - rationale - django_apps/asteroid_lab/reconstruction/rim_highlight.py
- [[VoidEdgeCellDTO]] - code - django_apps/asteroid_lab/reconstruction/rim_highlight.py
- [[_normalize_edge()]] - code - django_apps/asteroid_lab/reconstruction/cell_hull_outline.py
- [[_outer_outline_loops()]] - code - django_apps/asteroid_lab/reconstruction/rim_highlight.py
- [[_void_boundary_segments()]] - code - django_apps/asteroid_lab/reconstruction/rim_highlight.py
- [[_void_edge_cells()]] - code - django_apps/asteroid_lab/reconstruction/rim_highlight.py
- [[build_cell_hull_outline_loops()]] - code - django_apps/asteroid_lab/reconstruction/cell_hull_outline.py
- [[build_terrain_rim_highlight()]] - code - django_apps/asteroid_lab/reconstruction/rim_highlight.py
- [[build_terrain_rim_highlight_from_renderable_cells()]] - code - django_apps/asteroid_lab/reconstruction/rim_highlight.py
- [[canonicalize_void_edges()]] - code - django_apps/asteroid_lab/reconstruction/rim_highlight.py
- [[cell_hull_outline.py]] - code - django_apps/asteroid_lab/reconstruction/cell_hull_outline.py
- [[exterior_segments_for_occupied_cells()]] - code - django_apps/asteroid_lab/reconstruction/cell_hull_outline.py
- [[rim_highlight.py]] - code - django_apps/asteroid_lab/reconstruction/rim_highlight.py
- [[terrain_rim_highlight_to_metrics_dict()]] - code - django_apps/asteroid_lab/reconstruction/rim_highlight.py
- [[trace_outline_loops_from_segments()]] - code - django_apps/asteroid_lab/reconstruction/cell_hull_outline.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/build_terrain_rim_highlight_from_rendera
SORT file.name ASC
```

## Connections to other communities
- 8 edges to [[_COMMUNITY_Coord]]
- 2 edges to [[_COMMUNITY_ReconstructionCompleteMap]]
- 2 edges to [[_COMMUNITY_enrich_lab_timeline_frames_with_terrain_]]
- 1 edge to [[_COMMUNITY_recipe_graph_recompute.py]]
- 1 edge to [[_COMMUNITY_ReplayOverlayCell]]
- 1 edge to [[_COMMUNITY_ReconstructionResult]]

## Top bridge nodes
- [[build_terrain_rim_highlight_from_renderable_cells()]] - degree 10, connects to 4 communities
- [[trace_outline_loops_from_segments()]] - degree 7, connects to 2 communities
- [[build_cell_hull_outline_loops()]] - degree 6, connects to 2 communities
- [[_void_edge_cells()]] - degree 5, connects to 1 community
- [[_outer_outline_loops()]] - degree 5, connects to 1 community