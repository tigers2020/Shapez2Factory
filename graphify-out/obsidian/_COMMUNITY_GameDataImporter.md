---
type: community
cohesion: 0.22
members: 27
---

# GameDataImporter

**Cohesion:** 0.22 - loosely connected
**Members:** 27 nodes

## Members
- [[._import_asset_meta()]] - code - django_apps/game_data/importers/importer.py
- [[._import_building_groups()]] - code - django_apps/game_data/importers/importer.py
- [[._import_building_variants()]] - code - django_apps/game_data/importers/importer.py
- [[._import_buildings_plain()]] - code - django_apps/game_data/importers/importer.py
- [[._import_clr_types()]] - code - django_apps/game_data/importers/importer.py
- [[._import_content_assets()]] - code - django_apps/game_data/importers/importer.py
- [[._import_fluids()]] - code - django_apps/game_data/importers/importer.py
- [[._import_research()]] - code - django_apps/game_data/importers/importer.py
- [[._import_research_costs()]] - code - django_apps/game_data/importers/importer.py
- [[._import_research_prerequisites()]] - code - django_apps/game_data/importers/importer.py
- [[._import_shapes()]] - code - django_apps/game_data/importers/importer.py
- [[._import_simulation_systems()]] - code - django_apps/game_data/importers/importer.py
- [[._import_toolbar()]] - code - django_apps/game_data/importers/importer.py
- [[._import_translations_status()]] - code - django_apps/game_data/importers/importer.py
- [[._import_transport_registry()]] - code - django_apps/game_data/importers/importer.py
- [[._load_manifest()]] - code - django_apps/game_data/importers/importer.py
- [[._path()]] - code - django_apps/game_data/importers/importer.py
- [[._source_object()]] - code - django_apps/game_data/importers/importer.py
- [[._upsert_building_group()]] - code - django_apps/game_data/importers/importer.py
- [[._upsert_lazy_localized_text()]] - code - django_apps/game_data/importers/importer.py
- [[.run()]] - code - django_apps/game_data/importers/importer.py
- [[BuildingGroup]] - code - django_apps/game_data/importers/importer.py
- [[Deterministic game_data JSON importer.]] - rationale - django_apps/game_data/importers/importer.py
- [[GameDataImporter]] - code - django_apps/game_data/importers/importer.py
- [[LazyLocalizedTextRef]] - code - django_apps/game_data/importers/importer.py
- [[importer.py]] - code - django_apps/game_data/importers/importer.py
- [[load_json()]] - code - django_apps/game_data/importers/source_loader.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/GameDataImporter
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_Any]]
- 6 edges to [[_COMMUNITY_import_toolbar_tree()]]
- 3 edges to [[_COMMUNITY_Path]]
- 3 edges to [[_COMMUNITY_verify_game_data_source()]]
- 2 edges to [[_COMMUNITY_import_guards.py]]
- 1 edge to [[_COMMUNITY_build_asteroid_game_data_snapshot_with_p]]
- 1 edge to [[_COMMUNITY_ResearchSideQuestAdmin]]
- 1 edge to [[_COMMUNITY_identifiers.py]]
- 1 edge to [[_COMMUNITY_ImportContext]]
- 1 edge to [[_COMMUNITY_Command]]
- 1 edge to [[_COMMUNITY_import_shape_rows()]]
- 1 edge to [[_COMMUNITY_parse_lazy_localized_text()]]
- 1 edge to [[_COMMUNITY_import_simulation_systems()]]

## Top bridge nodes
- [[load_json()]] - degree 17, connects to 3 communities
- [[._upsert_building_group()]] - degree 8, connects to 3 communities
- [[GameDataImporter]] - degree 24, connects to 2 communities
- [[.run()]] - degree 18, connects to 2 communities
- [[._source_object()]] - degree 7, connects to 2 communities