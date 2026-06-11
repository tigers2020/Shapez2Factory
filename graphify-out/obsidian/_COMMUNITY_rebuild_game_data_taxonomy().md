---
type: community
cohesion: 0.19
members: 13
---

# rebuild_game_data_taxonomy()

**Cohesion:** 0.19 - loosely connected
**Members:** 13 nodes

## Members
- [[.handle()_7]] - code - django_apps/game_data/management/commands/seed_game_data_taxonomy.py
- [[Command_7]] - code - django_apps/game_data/management/commands/seed_game_data_taxonomy.py
- [[Create or update namespacesection rows for admin browse navigation.]] - rationale - django_apps/game_data/services/taxonomy_seed.py
- [[Drop browse sections for sub-tables (migrations 0020 + 0023 prune parity).]] - rationale - django_apps/game_data/services/taxonomy_seed.py
- [[Rebuild GameDataNamespace  GameDataSection for admin browse after flush or load]] - rationale - django_apps/game_data/management/commands/seed_game_data_taxonomy.py
- [[Rebuild admin browse taxonomy from model verbose_name_plural metadata.]] - rationale - django_apps/game_data/services/taxonomy_seed.py
- [[Seed namespacessections, then prune sub-table section rows.]] - rationale - django_apps/game_data/services/taxonomy_seed.py
- [[_slugify()]] - code - django_apps/game_data/services/taxonomy_seed.py
- [[prune_subtable_taxonomy_sections()]] - code - django_apps/game_data/services/taxonomy_seed.py
- [[rebuild_game_data_taxonomy()]] - code - django_apps/game_data/services/taxonomy_seed.py
- [[seed_game_data_taxonomy()]] - code - django_apps/game_data/services/taxonomy_seed.py
- [[seed_game_data_taxonomy.py]] - code - django_apps/game_data/management/commands/seed_game_data_taxonomy.py
- [[taxonomy_seed.py]] - code - django_apps/game_data/services/taxonomy_seed.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/rebuild_game_data_taxonomy
SORT file.name ASC
```

## Connections to other communities
- 1 edge to [[_COMMUNITY_BaseCommand]]

## Top bridge nodes
- [[Command_7]] - degree 3, connects to 1 community