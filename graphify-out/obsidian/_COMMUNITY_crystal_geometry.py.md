---
type: community
cohesion: 0.17
members: 18
---

# crystal_geometry.py

**Cohesion:** 0.17 - loosely connected
**Members:** 18 nodes

## Members
- [[BFS over crystal cells using func`iter_adjacent_layer_quads`.]] - rationale - django_apps/shapez_core/domain/crystal_geometry.py
- [[Crystal generator fill, adjacency, cluster discovery, and shatter helpers.  Rule]] - rationale - django_apps/shapez_core/domain/crystal_geometry.py
- [[Fill empty quadrants and pins with crystal (``kind='c'``) up to highest used lay]] - rationale - django_apps/shapez_core/domain/crystal_geometry.py
- [[LayerQuad]] - code - django_apps/shapez_core/domain/crystal_geometry.py
- [[Neighbors for cluster BFS same-layer perimeter + same quad abovebelow.]] - rationale - django_apps/shapez_core/domain/crystal_geometry.py
- [[Remove the crystal cluster containing ``(touch_z, touch_q)`` if it is crystal.]] - rationale - django_apps/shapez_core/domain/crystal_geometry.py
- [[Replace every cell in ``cluster`` with empty quadrants.]] - rationale - django_apps/shapez_core/domain/crystal_geometry.py
- [[Return ``(nz, nq)`` if it is an unseen in-bounds crystal cell, else ``None``.]] - rationale - django_apps/shapez_core/domain/crystal_geometry.py
- [[Top layer index that still has any non-empty quadrant.]] - rationale - django_apps/shapez_core/domain/crystal_geometry.py
- [[_crystal_bfs_candidate()]] - code - django_apps/shapez_core/domain/crystal_geometry.py
- [[_validate_paint_color()]] - code - django_apps/shapez_core/domain/crystal_geometry.py
- [[connected_crystal_cluster()]] - code - django_apps/shapez_core/domain/crystal_geometry.py
- [[crystal_fill_gaps_and_pins()]] - code - django_apps/shapez_core/domain/crystal_geometry.py
- [[crystal_geometry.py]] - code - django_apps/shapez_core/domain/crystal_geometry.py
- [[highest_used_layer_index()]] - code - django_apps/shapez_core/domain/crystal_geometry.py
- [[iter_adjacent_layer_quads()]] - code - django_apps/shapez_core/domain/crystal_geometry.py
- [[shatter_at_touch()]] - code - django_apps/shapez_core/domain/crystal_geometry.py
- [[shatter_crystal_cluster()]] - code - django_apps/shapez_core/domain/crystal_geometry.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/crystal_geometrypy
SORT file.name ASC
```

## Connections to other communities
- 8 edges to [[_COMMUNITY_Shape]]

## Top bridge nodes
- [[connected_crystal_cluster()]] - degree 7, connects to 1 community
- [[crystal_fill_gaps_and_pins()]] - degree 6, connects to 1 community
- [[iter_adjacent_layer_quads()]] - degree 5, connects to 1 community
- [[_crystal_bfs_candidate()]] - degree 5, connects to 1 community
- [[shatter_crystal_cluster()]] - degree 5, connects to 1 community