---
type: community
cohesion: 0.19
members: 20
---

# game_data_snapshot.py

**Cohesion:** 0.19 - loosely connected
**Members:** 20 nodes

## Members
- [[.__post_init__()_10]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot.py
- [[AsteroidGameDataSnapshot_1]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot.py
- [[BuildingConnectorSnapshot_1]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot.py
- [[BuildingFootprintCell_1]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot.py
- [[BuildingSnapshot_1]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot.py
- [[Frozen consumer DTOs and validation for game_data → Asteroid Lab snapshot.]] - rationale - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot.py
- [[SHA-256 hex of canonical JSON over snapshot subset (meta excluded).]] - rationale - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot.py
- [[SnapshotMeta]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot.py
- [[TransportRegistryEntry_1]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot.py
- [[_building_dict()]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot.py
- [[_canonical_payload()_1]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot.py
- [[_connector_dict()_1]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot.py
- [[_footprint_cell_dict()]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot.py
- [[_sort_connectors()]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot.py
- [[_sort_footprint()]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot.py
- [[_transport_dict()_1]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot.py
- [[build_snapshot_meta()]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot.py
- [[game_data_snapshot.py_1]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot.py
- [[snapshot_content_hash()]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot.py
- [[validate_building_snapshot()]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/game_data_snapshotpy
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_build_asteroid_game_data_snapshot_with_p]]
- 1 edge to [[_COMMUNITY_catalog_slice_from_snapshot()]]

## Top bridge nodes
- [[validate_building_snapshot()]] - degree 6, connects to 2 communities
- [[snapshot_content_hash()]] - degree 5, connects to 1 community
- [[build_snapshot_meta()]] - degree 3, connects to 1 community