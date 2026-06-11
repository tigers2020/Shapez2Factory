---
type: community
cohesion: 0.19
members: 15
---

# entry_island_raw_coord()

**Cohesion:** 0.19 - loosely connected
**Members:** 15 nodes

## Members
- [[Coerce a blueprint entry numeric field; missing  null → ``0``.]] - rationale - src/shapez2_factory/domain/asteroid_lab/copy_json_coords.py
- [[Island-local ``X`` (omitted key → ``0``).]] - rationale - src/shapez2_factory/domain/asteroid_lab/copy_json_coords.py
- [[Island-local ``Y`` (omitted key → ``0``).]] - rationale - src/shapez2_factory/domain/asteroid_lab/copy_json_coords.py
- [[Island-local paste coord as class`~coord_frames.IslandRawCoord`.]] - rationale - src/shapez2_factory/domain/asteroid_lab/copy_json_coords.py
- [[IslandRawCoord_1]] - code - src/shapez2_factory/domain/asteroid_lab/copy_json_coords.py
- [[Shapez2 copy JSON island-local coordinates (``BP.Entries``).  Decoded paste]] - rationale - src/shapez2_factory/domain/asteroid_lab/copy_json_coords.py
- [[Whether any entry uses raw column ``X == 0``.      Includes entries with omi]] - rationale - src/shapez2_factory/domain/asteroid_lab/copy_json_coords.py
- [[``(x, y)`` after defaulting omitted keys.]] - rationale - src/shapez2_factory/domain/asteroid_lab/copy_json_coords.py
- [[as_entry_int()]] - code - src/shapez2_factory/domain/asteroid_lab/copy_json_coords.py
- [[copy_json_coords.py]] - code - src/shapez2_factory/domain/asteroid_lab/copy_json_coords.py
- [[entries_have_explicit_raw_x_zero()]] - code - src/shapez2_factory/domain/asteroid_lab/copy_json_coords.py
- [[entry_island_local_xy()]] - code - src/shapez2_factory/domain/asteroid_lab/copy_json_coords.py
- [[entry_island_raw_coord()]] - code - src/shapez2_factory/domain/asteroid_lab/copy_json_coords.py
- [[entry_raw_x()]] - code - src/shapez2_factory/domain/asteroid_lab/copy_json_coords.py
- [[entry_raw_y()]] - code - src/shapez2_factory/domain/asteroid_lab/copy_json_coords.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/entry_island_raw_coord
SORT file.name ASC
```

## Connections to other communities
- 6 edges to [[_COMMUNITY_Any]]
- 6 edges to [[_COMMUNITY_ValueError]]
- 5 edges to [[_COMMUNITY_build_golden_oracle()]]
- 2 edges to [[_COMMUNITY_build_decoded_blueprint_snapshot()]]
- 2 edges to [[_COMMUNITY_topology_signature_from_decoded_root()]]
- 1 edge to [[_COMMUNITY_normalize_decoded_blueprint()]]
- 1 edge to [[_COMMUNITY_reconstruct_after_cleanup()]]

## Top bridge nodes
- [[entry_island_raw_coord()]] - degree 12, connects to 5 communities
- [[entry_raw_x()]] - degree 8, connects to 3 communities
- [[entry_raw_y()]] - degree 7, connects to 3 communities
- [[entries_have_explicit_raw_x_zero()]] - degree 6, connects to 3 communities
- [[copy_json_coords.py]] - degree 10, connects to 2 communities