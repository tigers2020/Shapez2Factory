---
type: community
cohesion: 0.27
members: 12
---

# build_game_data_snapshot_payload()

**Cohesion:** 0.27 - loosely connected
**Members:** 12 nodes

## Members
- [[.__init__()_4]] - code - django_apps/game_data/services/game_data_snapshot_export.py
- [[Fail closed when BA-8 minimum active ORM rows are absent.]] - rationale - django_apps/game_data/services/game_data_snapshot_export.py
- [[GameDataSnapshotExportError]] - code - django_apps/game_data/services/game_data_snapshot_export.py
- [[GameDataSnapshotExportErrorCode]] - code - django_apps/game_data/services/game_data_snapshot_export.py
- [[ORM → game_data snapshot payload (EVTC capacity) for the Asteroid Lab CLI core (]] - rationale - django_apps/game_data/services/game_data_snapshot_export.py
- [[ORM → snapshot payload (resolver output only; capacity formula stays in game_dat]] - rationale - django_apps/game_data/services/game_data_snapshot_export.py
- [[_assert_required_snapshot_rows()]] - code - django_apps/game_data/services/game_data_snapshot_export.py
- [[_dump_hash()]] - code - django_apps/game_data/services/game_data_snapshot_export.py
- [[_mining_extraction_rule_rows()]] - code - django_apps/game_data/services/game_data_snapshot_export.py
- [[_raise_export_error()]] - code - django_apps/game_data/services/game_data_snapshot_export.py
- [[build_game_data_snapshot_payload()]] - code - django_apps/game_data/services/game_data_snapshot_export.py
- [[game_data_snapshot_export.py]] - code - django_apps/game_data/services/game_data_snapshot_export.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/build_game_data_snapshot_payload
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_exterior_transport_capacity.py]]
- 3 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY_mining_extraction_rules.py]]
- 1 edge to [[_COMMUNITY_execute_layer_02_exterior_transport_plan]]
- 1 edge to [[_COMMUNITY_entry_result_to_json_dict()]]
- 1 edge to [[_COMMUNITY_StrEnum]]
- 1 edge to [[_COMMUNITY_Exception]]
- 1 edge to [[_COMMUNITY_Command]]
- 1 edge to [[_COMMUNITY_Enum]]
- 1 edge to [[_COMMUNITY__run_solver_post_traced()]]

## Top bridge nodes
- [[build_game_data_snapshot_payload()]] - degree 11, connects to 6 communities
- [[game_data_snapshot_export.py]] - degree 10, connects to 2 communities
- [[_assert_required_snapshot_rows()]] - degree 7, connects to 2 communities
- [[_raise_export_error()]] - degree 5, connects to 1 community
- [[GameDataSnapshotExportErrorCode]] - degree 4, connects to 1 community