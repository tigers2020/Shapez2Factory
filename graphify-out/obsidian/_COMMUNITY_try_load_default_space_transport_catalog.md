---
type: community
cohesion: 0.50
members: 4
---

# try_load_default_space_transport_catalog

**Cohesion:** 0.50 - moderately connected
**Members:** 4 nodes

## Members
- [[Load ``SpaceTransportTileCatalog`` from repo game_data (Django boundary only).]] - rationale - django_apps/asteroid_lab/services/space_transport_catalog_loader.py
- [[Return catalog from default game_data paths, or None if import fails.]] - rationale - django_apps/asteroid_lab/services/space_transport_catalog_loader.py
- [[space_transport_catalog_loader.py]] - code - django_apps/asteroid_lab/services/space_transport_catalog_loader.py
- [[try_load_default_space_transport_catalog()]] - code - django_apps/asteroid_lab/services/space_transport_catalog_loader.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/try_load_default_space_transport_catalog
SORT file.name ASC
```

## Connections to other communities
- 1 edge to [[_COMMUNITY_run_full_from_cleanup_recon()]]
- 1 edge to [[_COMMUNITY_build_solver_runtime_replay_frames_from_]]
- 1 edge to [[_COMMUNITY_Path]]
- 1 edge to [[_COMMUNITY_run_layers_02_to_06()]]

## Top bridge nodes
- [[try_load_default_space_transport_catalog()]] - degree 6, connects to 4 communities