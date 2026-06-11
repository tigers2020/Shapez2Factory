---
type: community
cohesion: 0.32
members: 8
---

# import_shape_rows()

**Cohesion:** 0.32 - loosely connected
**Members:** 8 nodes

## Members
- [[.catalog_appearances_summary()]] - code - django_apps/game_data/admin.py
- [[First FULL appearance wins; else first ITEMS.]] - rationale - django_apps/game_data/importers/shape_recipes.py
- [[Provenance-preserving shape_recipe import (shapes.json + items.json).]] - rationale - django_apps/game_data/importers/shape_recipes.py
- [[ShapeRecipe]] - code - django_apps/game_data/importers/shape_recipes.py
- [[_shape_definition()]] - code - django_apps/game_data/importers/shape_recipes.py
- [[import_shape_rows()]] - code - django_apps/game_data/importers/shape_recipes.py
- [[refresh_primary_source_object()]] - code - django_apps/game_data/importers/shape_recipes.py
- [[shape_recipes.py]] - code - django_apps/game_data/importers/shape_recipes.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/import_shape_rows
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_Any]]
- 1 edge to [[_COMMUNITY_admin.py]]
- 1 edge to [[_COMMUNITY_identifiers.py]]
- 1 edge to [[_COMMUNITY_import_toolbar_tree()]]
- 1 edge to [[_COMMUNITY_ImportContext]]
- 1 edge to [[_COMMUNITY_GameDataImporter]]

## Top bridge nodes
- [[import_shape_rows()]] - degree 8, connects to 5 communities
- [[_shape_definition()]] - degree 3, connects to 1 community
- [[.catalog_appearances_summary()]] - degree 2, connects to 1 community