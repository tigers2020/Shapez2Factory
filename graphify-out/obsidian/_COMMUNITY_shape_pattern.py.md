---
type: community
cohesion: 0.33
members: 7
---

# shape_pattern.py

**Cohesion:** 0.33 - loosely connected
**Members:** 7 nodes

## Members
- [[Compass labels for each slot in a layer.      Matches ``ShapeLayer.quadrants`` i]] - rationale - django_apps/shapez_core/domain/shape_pattern.py
- [[NormalizedShapeCell]] - code - django_apps/shapez_core/domain/shape_pattern.py
- [[NormalizedShapeLayer]] - code - django_apps/shapez_core/domain/shape_pattern.py
- [[NormalizedShapePattern]] - code - django_apps/shapez_core/domain/shape_pattern.py
- [[QuadrantPosition]] - code - django_apps/shapez_core/domain/shape_pattern.py
- [[quadrant_at_index()]] - code - django_apps/shapez_core/domain/shape_pattern.py
- [[shape_pattern.py]] - code - django_apps/shapez_core/domain/shape_pattern.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/shape_patternpy
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_Enum]]
- 1 edge to [[_COMMUNITY_shape_codec.py]]
- 1 edge to [[_COMMUNITY_ShapeCodeParseError]]
- 1 edge to [[_COMMUNITY_build_shape_render_scene()]]

## Top bridge nodes
- [[quadrant_at_index()]] - degree 5, connects to 3 communities
- [[shape_pattern.py]] - degree 6, connects to 1 community
- [[QuadrantPosition]] - degree 4, connects to 1 community