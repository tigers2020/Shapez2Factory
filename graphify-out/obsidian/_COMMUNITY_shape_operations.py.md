---
type: community
cohesion: 0.24
members: 12
---

# shape_operations.py

**Cohesion:** 0.24 - loosely connected
**Members:** 12 nodes

## Members
- [[Exchange east halves (NE+SE) between two single layers.]] - rationale - django_apps/shapez_core/domain/shape_operations.py
- [[If no quadrant has both inputs non-empty, merge into one layer; else ``None``.]] - rationale - django_apps/shapez_core/domain/shape_operations.py
- [[Pure shape transforms (rotate  cut  merge  swap halves).  These functions o]] - rationale - django_apps/shapez_core/domain/shape_operations.py
- [[ShapeLayer_1]] - code - django_apps/shapez_core/domain/shape_operations.py
- [[Split each layer into west (``quadrants02``) and east (``24``) halves.]] - rationale - django_apps/shapez_core/domain/shape_operations.py
- [[cut_vertical_halves()]] - code - django_apps/shapez_core/domain/shape_operations.py
- [[merge_disjoint_shape_layers()]] - code - django_apps/shapez_core/domain/shape_operations.py
- [[rotate_180()]] - code - django_apps/shapez_core/domain/shape_operations.py
- [[rotate_ccw()]] - code - django_apps/shapez_core/domain/shape_operations.py
- [[rotate_cw()]] - code - django_apps/shapez_core/domain/shape_operations.py
- [[shape_operations.py]] - code - django_apps/shapez_core/domain/shape_operations.py
- [[swap_half_planes_single_layer()]] - code - django_apps/shapez_core/domain/shape_operations.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/shape_operationspy
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_Shape]]

## Top bridge nodes
- [[cut_vertical_halves()]] - degree 5, connects to 1 community
- [[merge_disjoint_shape_layers()]] - degree 4, connects to 1 community
- [[swap_half_planes_single_layer()]] - degree 4, connects to 1 community
- [[rotate_cw()]] - degree 3, connects to 1 community
- [[rotate_ccw()]] - degree 3, connects to 1 community