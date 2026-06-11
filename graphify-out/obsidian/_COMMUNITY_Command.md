---
type: community
cohesion: 0.18
members: 11
---

# Command

**Cohesion:** 0.18 - loosely connected
**Members:** 11 nodes

## Members
- [[.add_arguments()_4]] - code - django_apps/game_data/management/commands/export_game_data_snapshot.py
- [[.add_arguments()_5]] - code - django_apps/game_data/management/commands/import_game_data.py
- [[.handle()_5]] - code - django_apps/game_data/management/commands/export_game_data_snapshot.py
- [[.handle()_6]] - code - django_apps/game_data/management/commands/import_game_data.py
- [[Command_5]] - code - django_apps/game_data/management/commands/export_game_data_snapshot.py
- [[Command_6]] - code - django_apps/game_data/management/commands/import_game_data.py
- [[CommandParser]] - code - django_apps/game_data/management/commands/import_game_data.py
- [[Import normalized game_data from JSON bundle.]] - rationale - django_apps/game_data/management/commands/import_game_data.py
- [[``manage.py export_game_data_snapshot --out path`` — ORM → frozen snapshot JSO]] - rationale - django_apps/game_data/management/commands/export_game_data_snapshot.py
- [[export_game_data_snapshot.py]] - code - django_apps/game_data/management/commands/export_game_data_snapshot.py
- [[import_game_data.py]] - code - django_apps/game_data/management/commands/import_game_data.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Command
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_BaseCommand]]
- 1 edge to [[_COMMUNITY_Any]]
- 1 edge to [[_COMMUNITY_GameDataImporter]]
- 1 edge to [[_COMMUNITY_build_game_data_snapshot_payload()]]
- 1 edge to [[_COMMUNITY_verify_game_data_source()]]

## Top bridge nodes
- [[.handle()_5]] - degree 3, connects to 2 communities
- [[.handle()_6]] - degree 3, connects to 2 communities
- [[Command_5]] - degree 4, connects to 1 community
- [[Command_6]] - degree 4, connects to 1 community