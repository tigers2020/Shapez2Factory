---
type: community
cohesion: 0.24
members: 10
---

# ImportContext

**Cohesion:** 0.24 - loosely connected
**Members:** 10 nodes

## Members
- [[ImportContext_1]] - code - django_apps/game_data/services/simulation_parameter_registry.py
- [[Record building AssemblyDeclaredMembers as reflection metadata (ignore_audit).]] - rationale - django_apps/game_data/importers/building_assembly_audit.py
- [[Record definition_snapshot ignore_audit coverage for SimulationSystem rows.]] - rationale - django_apps/game_data/importers/simulation_definition_snapshot_audit.py
- [[_norm_path()]] - code - django_apps/game_data/importers/simulation_definition_snapshot_audit.py
- [[_scan_reflection()]] - code - django_apps/game_data/importers/building_assembly_audit.py
- [[_should_record_prefix()]] - code - django_apps/game_data/importers/simulation_definition_snapshot_audit.py
- [[building_assembly_audit.py]] - code - django_apps/game_data/importers/building_assembly_audit.py
- [[record_assembly_reflection_audit()]] - code - django_apps/game_data/importers/building_assembly_audit.py
- [[simulation_definition_snapshot_audit.py]] - code - django_apps/game_data/importers/simulation_definition_snapshot_audit.py
- [[sync_definition_snapshot_coverage_audit()]] - code - django_apps/game_data/importers/simulation_definition_snapshot_audit.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/ImportContext
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_simulation_speed_extract.py]]
- 3 edges to [[_COMMUNITY_import_simulation_systems()]]
- 2 edges to [[_COMMUNITY_Any]]
- 1 edge to [[_COMMUNITY_import_shape_rows()]]
- 1 edge to [[_COMMUNITY__import_connectable_attachment()]]
- 1 edge to [[_COMMUNITY_import_toolbar_tree()]]
- 1 edge to [[_COMMUNITY_GameDataImporter]]

## Top bridge nodes
- [[ImportContext_1]] - degree 11, connects to 5 communities
- [[record_assembly_reflection_audit()]] - degree 5, connects to 2 communities
- [[sync_definition_snapshot_coverage_audit()]] - degree 4, connects to 2 communities