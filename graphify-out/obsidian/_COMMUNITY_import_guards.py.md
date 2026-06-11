---
type: community
cohesion: 0.16
members: 14
---

# import_guards.py

**Cohesion:** 0.16 - loosely connected
**Members:** 14 nodes

## Members
- [[GameDataImportBlockedError]] - code - django_apps/game_data/services/import_guards.py
- [[Import refused until migrations or schema contracts are satisfied.]] - rationale - django_apps/game_data/services/import_guards.py
- [[Post-import invariant checks.]] - rationale - django_apps/game_data/services/validators.py
- [[Prepost conditions for game_data import (migrations, schema contracts).]] - rationale - django_apps/game_data/services/import_guards.py
- [[Run after a successful import transaction.]] - rationale - django_apps/game_data/services/import_guards.py
- [[Run before GameDataImporter mutates the database.]] - rationale - django_apps/game_data/services/import_guards.py
- [[RuntimeError]] - code
- [[assert_canonical_ids_unique()]] - code - django_apps/game_data/services/validators.py
- [[assert_game_data_migrations_applied()]] - code - django_apps/game_data/services/import_guards.py
- [[assert_import_preconditions()]] - code - django_apps/game_data/services/import_guards.py
- [[assert_no_domain_json_fields()]] - code - django_apps/game_data/services/validators.py
- [[import_guards.py]] - code - django_apps/game_data/services/import_guards.py
- [[run_post_import_guards()]] - code - django_apps/game_data/services/import_guards.py
- [[validators.py]] - code - django_apps/game_data/services/validators.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/import_guardspy
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_GameDataImporter]]
- 1 edge to [[_COMMUNITY_verify_game_data_source()]]

## Top bridge nodes
- [[assert_import_preconditions()]] - degree 4, connects to 1 community
- [[run_post_import_guards()]] - degree 4, connects to 1 community
- [[RuntimeError]] - degree 2, connects to 1 community