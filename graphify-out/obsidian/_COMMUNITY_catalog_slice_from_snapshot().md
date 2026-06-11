---
type: community
cohesion: 0.43
members: 7
---

# catalog_slice_from_snapshot()

**Cohesion:** 0.43 - moderately connected
**Members:** 7 nodes

## Members
- [[Allowlist catalog slice extracted from ``AsteroidGameDataSnapshot`` (Track B2]] - rationale - src/shapez2_factory/domain/asteroid_lab/building_catalog_slice.py
- [[BuildingCatalogSlice]] - code - src/shapez2_factory/domain/asteroid_lab/building_catalog_slice.py
- [[Extract identity, transport registry, and per-variant geometry for the allowlist]] - rationale - src/shapez2_factory/domain/asteroid_lab/building_catalog_slice.py
- [[VariantGeometryCatalog]] - code - src/shapez2_factory/domain/asteroid_lab/building_catalog_slice.py
- [[VariantIdentity]] - code - src/shapez2_factory/domain/asteroid_lab/building_catalog_slice.py
- [[building_catalog_slice.py_1]] - code - src/shapez2_factory/domain/asteroid_lab/building_catalog_slice.py
- [[catalog_slice_from_snapshot()]] - code - src/shapez2_factory/domain/asteroid_lab/building_catalog_slice.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/catalog_slice_from_snapshot
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_build_asteroid_game_data_snapshot_with_p]]
- 1 edge to [[_COMMUNITY_game_data_snapshot.py]]

## Top bridge nodes
- [[catalog_slice_from_snapshot()]] - degree 8, connects to 2 communities