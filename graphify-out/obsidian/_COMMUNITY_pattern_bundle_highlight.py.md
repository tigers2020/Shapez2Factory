---
type: community
cohesion: 0.25
members: 11
---

# pattern_bundle_highlight.py

**Cohesion:** 0.25 - loosely connected
**Members:** 11 nodes

## Members
- [[Adjacent or overlapping footprints cannot share a palette slot.]] - rationale - django_apps/asteroid_lab/replay/pattern_bundle_highlight.py
- [[Equipment footprint for L4 highlights (stubroute excluded).]] - rationale - django_apps/asteroid_lab/replay/pattern_bundle_highlight.py
- [[Greedy graph coloring on bundle footprint conflict (stable input order).]] - rationale - django_apps/asteroid_lab/replay/pattern_bundle_highlight.py
- [[Pattern bundle highlight wire for Lab replay (output-only).  Must not be impor]] - rationale - django_apps/asteroid_lab/replay/pattern_bundle_highlight.py
- [[_RimPlacementMiningSource]] - code - django_apps/asteroid_lab/replay/pattern_bundle_highlight.py
- [[_bundles_adjacent()]] - code - django_apps/asteroid_lab/replay/pattern_bundle_highlight.py
- [[_bundles_conflict()]] - code - django_apps/asteroid_lab/replay/pattern_bundle_highlight.py
- [[_bundles_share_cells()]] - code - django_apps/asteroid_lab/replay/pattern_bundle_highlight.py
- [[assign_bundle_color_indices()]] - code - django_apps/asteroid_lab/replay/pattern_bundle_highlight.py
- [[mining_occupied_from_rim_placement()]] - code - django_apps/asteroid_lab/replay/pattern_bundle_highlight.py
- [[pattern_bundle_highlight.py]] - code - django_apps/asteroid_lab/replay/pattern_bundle_highlight.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/pattern_bundle_highlightpy
SORT file.name ASC
```

## Connections to other communities
- 5 edges to [[_COMMUNITY_Coord]]
- 4 edges to [[_COMMUNITY_ReplayOverlayCell]]
- 1 edge to [[_COMMUNITY_Protocol]]

## Top bridge nodes
- [[mining_occupied_from_rim_placement()]] - degree 6, connects to 2 communities
- [[assign_bundle_color_indices()]] - degree 5, connects to 2 communities
- [[pattern_bundle_highlight.py]] - degree 8, connects to 1 community
- [[_bundles_conflict()]] - degree 6, connects to 1 community
- [[_RimPlacementMiningSource]] - degree 3, connects to 1 community