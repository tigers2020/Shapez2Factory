---
type: community
cohesion: 0.14
members: 21
---

# stamp_islands_uniform()

**Cohesion:** 0.14 - loosely connected
**Members:** 21 nodes

## Members
- [[Cardinal neighbors for floodcomponents (map coords or grid when seam included).]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/grid.py
- [[CellKey]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/island.py
- [[Decoded ``asteroid__field`` plus implied kinds at stripped minerextension anch]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/island.py
- [[False when both endpoints carry conflicting original ``asteroid_`` evidence.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/island.py
- [[Island member coords plus 4-neighbors of ``topology_fill`` synthetic cells only.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/island.py
- [[Non-transport asteroid islands and uniform ``cell_kind`` stamping (post-reconstr]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/island.py
- [[Stamp targets plus ``unknown`` bridges (walls are not recolored).]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/island.py
- [[Strict fluid vs shape majority on vote coords; tie or no evidence → shape field.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/island.py
- [[Uniform ``asteroid__field`` on stamp targets; ``unknown`` walls stay traversabl]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/island.py
- [[_allow_edge()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/island.py
- [[_is_stamp_target()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/island.py
- [[_is_topology_fill_cell()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/island.py
- [[_is_traversable_for_island()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/island.py
- [[_vote_xy_set()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/island.py
- [[build_original_evidence_by_xy()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/island.py
- [[island.py]] - code - django_apps/asteroid_lab/reconstruction/island.py
- [[island.py_1]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/island.py
- [[iter_four_neighbors()]] - code - src/shapez2_factory/domain/asteroid_lab/transport_components.py
- [[reconstruction_cardinal_neighbors()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/grid.py
- [[resolve_island_kind()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/island.py
- [[stamp_islands_uniform()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/island.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/stamp_islands_uniform
SORT file.name ASC
```

## Connections to other communities
- 10 edges to [[_COMMUNITY_DecodedCellDTO]]
- 5 edges to [[_COMMUNITY_Coord]]
- 3 edges to [[_COMMUNITY_reconstruct_after_cleanup()]]
- 2 edges to [[_COMMUNITY_is_asteroid_evidence()]]
- 1 edge to [[_COMMUNITY_asteroid_map_coords.py]]
- 1 edge to [[_COMMUNITY_deconstruct_snapshot()]]

## Top bridge nodes
- [[build_original_evidence_by_xy()]] - degree 7, connects to 3 communities
- [[reconstruction_cardinal_neighbors()]] - degree 6, connects to 3 communities
- [[stamp_islands_uniform()]] - degree 11, connects to 2 communities
- [[_vote_xy_set()]] - degree 7, connects to 2 communities
- [[resolve_island_kind()]] - degree 7, connects to 2 communities