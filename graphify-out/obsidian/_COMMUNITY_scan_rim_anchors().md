---
type: community
cohesion: 0.32
members: 8
---

# scan_rim_anchors()

**Cohesion:** 0.32 - loosely connected
**Members:** 8 nodes

## Members
- [[A field cell adjacent to external void, with the void-facing directions.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/rim_anchor_scan.py
- [[Enumerate rim anchors field cells with at least one external-void neighbor.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/rim_anchor_scan.py
- [[Layer 03 rim anchor scan deterministic outer-rim enumeration (spec R1  D1).]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/rim_anchor_scan.py
- [[Map a field cell to ``shape``  ``fluid``.      Prefers per-cell evidence]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/rim_anchor_scan.py
- [[RimAnchor_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/rim_anchor_scan.py
- [[_resolve_field_kind()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/rim_anchor_scan.py
- [[rim_anchor_scan.py]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/rim_anchor_scan.py
- [[scan_rim_anchors()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/rim_anchor_scan.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/scan_rim_anchors
SORT file.name ASC
```

## Connections to other communities
- 1 edge to [[_COMMUNITY_Coord]]
- 1 edge to [[_COMMUNITY_ReconstructionCompleteMap]]
- 1 edge to [[_COMMUNITY_generate_candidates()]]
- 1 edge to [[_COMMUNITY_build_reconstruction_complete_map()]]
- 1 edge to [[_COMMUNITY_ExteriorConnectionPlan]]

## Top bridge nodes
- [[scan_rim_anchors()]] - degree 8, connects to 4 communities
- [[_resolve_field_kind()]] - degree 4, connects to 1 community