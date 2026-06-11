---
type: community
cohesion: 0.23
members: 14
---

# building_catalog_slice_hash.py

**Cohesion:** 0.23 - loosely connected
**Members:** 14 nodes

## Members
- [[BuildingCatalogSlice_1]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py
- [[Deterministic hash for ``BuildingCatalogSlice`` (Track B2  D).]] - rationale - src/shapez2_factory/domain/asteroid_lab/building_catalog_slice_hash.py
- [[SHA-256 hex; ``slice_version`` is included in the payload.]] - rationale - src/shapez2_factory/domain/asteroid_lab/building_catalog_slice_hash.py
- [[VariantGeometryCatalog_1]] - code - src/shapez2_factory/domain/asteroid_lab/building_catalog_slice_hash.py
- [[VariantIdentity_1]] - code - src/shapez2_factory/domain/asteroid_lab/building_catalog_slice_hash.py
- [[_canonical_payload()]] - code - src/shapez2_factory/domain/asteroid_lab/building_catalog_slice_hash.py
- [[_connector_dict()]] - code - src/shapez2_factory/domain/asteroid_lab/building_catalog_slice_hash.py
- [[_footprint_dict()]] - code - src/shapez2_factory/domain/asteroid_lab/building_catalog_slice_hash.py
- [[_geometry_dict()]] - code - src/shapez2_factory/domain/asteroid_lab/building_catalog_slice_hash.py
- [[_transport_dict()]] - code - src/shapez2_factory/domain/asteroid_lab/building_catalog_slice_hash.py
- [[_variant_dict()]] - code - src/shapez2_factory/domain/asteroid_lab/building_catalog_slice_hash.py
- [[building_catalog_slice_hash.py_1]] - code - src/shapez2_factory/domain/asteroid_lab/building_catalog_slice_hash.py
- [[catalog_slice_hash()]] - code - src/shapez2_factory/domain/asteroid_lab/building_catalog_slice_hash.py
- [[provenance_from_snapshot()]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/building_catalog_slice_hashpy
SORT file.name ASC
```

## Connections to other communities
- 5 edges to [[_COMMUNITY_build_asteroid_game_data_snapshot_with_p]]
- 2 edges to [[_COMMUNITY_game_data_snapshot_provenance.py]]
- 1 edge to [[_COMMUNITY_ValueError]]

## Top bridge nodes
- [[provenance_from_snapshot()]] - degree 7, connects to 3 communities
- [[_footprint_dict()]] - degree 3, connects to 1 community
- [[_connector_dict()]] - degree 3, connects to 1 community
- [[_transport_dict()]] - degree 3, connects to 1 community