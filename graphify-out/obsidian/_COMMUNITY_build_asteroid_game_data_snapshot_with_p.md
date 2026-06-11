---
type: community
cohesion: 0.11
members: 25
---

# build_asteroid_game_data_snapshot_with_p

**Cohesion:** 0.11 - loosely connected
**Members:** 25 nodes

## Members
- [[.hash_short()]] - code - django_apps/game_data/admin.py
- [[Assemble ``AsteroidGameDataSnapshot`` from pinned ``game_data`` import batch.]] - rationale - django_apps/web/services/asteroid_game_data_snapshot.py
- [[AsteroidGameDataSnapshot]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py
- [[BuildingAssemblyRow]] - code - django_apps/web/services/asteroid_game_data_snapshot.py
- [[BuildingConnectorSnapshot]] - code - src/shapez2_factory/domain/asteroid_lab/building_catalog_slice_hash.py
- [[BuildingFootprintCell]] - code - src/shapez2_factory/domain/asteroid_lab/building_catalog_slice_hash.py
- [[BuildingSnapshot]] - code - django_apps/web/services/asteroid_game_data_snapshot.py
- [[ConnectorRow]] - code - django_apps/web/services/asteroid_game_data_snapshot.py
- [[FootprintCellRow]] - code - django_apps/web/services/asteroid_game_data_snapshot.py
- [[GameDataSnapshotBuildResult]] - code - django_apps/web/services/asteroid_game_data_snapshot.py
- [[ImportBatch]] - code - django_apps/web/services/asteroid_game_data_snapshot.py
- [[Pin latest import batch once; return snapshot + provenance (sole construction si]] - rationale - django_apps/web/services/asteroid_game_data_snapshot.py
- [[Return snapshot only; prefer ``build_asteroid_game_data_snapshot_with_provenance]] - rationale - django_apps/web/services/asteroid_game_data_snapshot.py
- [[TransportRegistryEntry]] - code - src/shapez2_factory/domain/asteroid_lab/building_catalog_slice_hash.py
- [[TransportRegistryRow]] - code - django_apps/web/services/asteroid_game_data_snapshot.py
- [[_build_asteroid_game_data_snapshot_for_batch()]] - code - django_apps/web/services/asteroid_game_data_snapshot.py
- [[_building_dto()]] - code - django_apps/web/services/asteroid_game_data_snapshot.py
- [[_connector_dto()]] - code - django_apps/web/services/asteroid_game_data_snapshot.py
- [[_footprint_dto()]] - code - django_apps/web/services/asteroid_game_data_snapshot.py
- [[_transport_dto()]] - code - django_apps/web/services/asteroid_game_data_snapshot.py
- [[asteroid_game_data_snapshot.py]] - code - django_apps/web/services/asteroid_game_data_snapshot.py
- [[build_asteroid_game_data_snapshot()]] - code - django_apps/web/services/asteroid_game_data_snapshot.py
- [[build_asteroid_game_data_snapshot_with_provenance()]] - code - django_apps/web/services/asteroid_game_data_snapshot.py
- [[import_batch.py]] - code - django_apps/game_data/selectors/import_batch.py
- [[pin_latest_import_batch()]] - code - django_apps/game_data/selectors/import_batch.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/build_asteroid_game_data_snapshot_with_p
SORT file.name ASC
```

## Connections to other communities
- 5 edges to [[_COMMUNITY_building_catalog_slice_hash.py]]
- 3 edges to [[_COMMUNITY_game_data_snapshot.py]]
- 2 edges to [[_COMMUNITY_catalog_slice_from_snapshot()]]
- 1 edge to [[_COMMUNITY_admin.py]]
- 1 edge to [[_COMMUNITY_identifiers.py]]
- 1 edge to [[_COMMUNITY_GameDataImporter]]
- 1 edge to [[_COMMUNITY_verify_game_data_source()]]
- 1 edge to [[_COMMUNITY__run_solver_post_traced()]]

## Top bridge nodes
- [[build_asteroid_game_data_snapshot_with_provenance()]] - degree 9, connects to 3 communities
- [[ImportBatch]] - degree 6, connects to 3 communities
- [[AsteroidGameDataSnapshot]] - degree 4, connects to 2 communities
- [[_build_asteroid_game_data_snapshot_for_batch()]] - degree 8, connects to 1 community
- [[_building_dto()]] - degree 7, connects to 1 community