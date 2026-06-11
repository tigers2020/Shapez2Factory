---
type: community
cohesion: 0.22
members: 10
---

# verify_game_data_source()

**Cohesion:** 0.22 - loosely connected
**Members:** 10 nodes

## Members
- [[Ensure ``manifest.json`` hash matches the latest ``ImportBatch`` and artifacts a]] - rationale - django_apps/game_data/services/import_verify.py
- [[GameDataVerifyError]] - code - django_apps/game_data/services/import_verify.py
- [[Load JSON artifacts from documentsgame_data.]] - rationale - django_apps/game_data/importers/source_loader.py
- [[Raised when --verify preconditions fail.]] - rationale - django_apps/game_data/services/import_verify.py
- [[Verify on-disk game_data bundle matches the latest imported batch (read-only).]] - rationale - django_apps/game_data/services/import_verify.py
- [[import_verify.py]] - code - django_apps/game_data/services/import_verify.py
- [[sha256_file()]] - code - django_apps/game_data/importers/source_loader.py
- [[sha256_text()]] - code - django_apps/game_data/importers/source_loader.py
- [[source_loader.py]] - code - django_apps/game_data/importers/source_loader.py
- [[verify_game_data_source()]] - code - django_apps/game_data/services/import_verify.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/verify_game_data_source
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_GameDataImporter]]
- 2 edges to [[_COMMUNITY_Path]]
- 1 edge to [[_COMMUNITY_build_asteroid_game_data_snapshot_with_p]]
- 1 edge to [[_COMMUNITY_Command]]
- 1 edge to [[_COMMUNITY_import_guards.py]]

## Top bridge nodes
- [[verify_game_data_source()]] - degree 7, connects to 3 communities
- [[sha256_file()]] - degree 5, connects to 2 communities
- [[source_loader.py]] - degree 4, connects to 1 community
- [[GameDataVerifyError]] - degree 4, connects to 1 community