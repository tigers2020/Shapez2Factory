---
type: community
cohesion: 0.12
members: 29
---

# registry.py

**Cohesion:** 0.12 - loosely connected
**Members:** 29 nodes

## Members
- [[.related_subtable_links()]] - code - django_apps/game_data/admin.py
- [[AdminSite]] - code - django_apps/game_data/browse/registry.py
- [[AggregateRootSpec_1]] - code - django_apps/game_data/browse/registry.py
- [[Bounded-context browse registry taxonomy → admin targets and aggregate roots.]] - rationale - django_apps/game_data/browse/registry.py
- [[Browse-first game_data admin dashboard grouped by taxonomy.]] - rationale - django_apps/game_data/browse/views.py
- [[BrowseNamespaceGroup]] - code - django_apps/game_data/browse/registry.py
- [[BrowseSectionEntry]] - code - django_apps/game_data/browse/registry.py
- [[Build a filtered admin changelist URL for a sub-table without a direct parent FK]] - rationale - django_apps/game_data/browse/registry.py
- [[Canonical import-metadata names mapped to existing Django models (no parallel ta]] - rationale - django_apps/game_data/import_layer.py
- [[Expected parent-centered admin navigation for an aggregate root model.]] - rationale - django_apps/game_data/browse/registry.py
- [[GameDataSection]] - code - django_apps/game_data/browse/registry.py
- [[Model]] - code - django_apps/game_data/browse/registry.py
- [[RelatedChangelistSpec_1]] - code - django_apps/game_data/browse/registry.py
- [[Return human-readable errors when taxonomy sections lack admin browse targets.]] - rationale - django_apps/game_data/browse/registry.py
- [[Sub-table reached via filtered changelist (no direct FK inline).]] - rationale - django_apps/game_data/browse/registry.py
- [[aggregate_root_model_labels()]] - code - django_apps/game_data/browse/registry.py
- [[build_browse_groups()]] - code - django_apps/game_data/browse/registry.py
- [[changelist_url_for_model()]] - code - django_apps/game_data/browse/registry.py
- [[game_data_browse()]] - code - django_apps/game_data/browse/views.py
- [[import_layer.py]] - code - django_apps/game_data/import_layer.py
- [[model_for_canonical()]] - code - django_apps/game_data/import_layer.py
- [[registry.py]] - code - django_apps/game_data/browse/registry.py
- [[related_changelist_url()]] - code - django_apps/game_data/browse/registry.py
- [[resolve_model()]] - code - django_apps/game_data/browse/registry.py
- [[row_count_for_model()]] - code - django_apps/game_data/browse/registry.py
- [[section_qs_sorted()]] - code - django_apps/game_data/browse/registry.py
- [[validate_aggregate_root_inlines()]] - code - django_apps/game_data/browse/registry.py
- [[validate_section_admin_targets()]] - code - django_apps/game_data/browse/registry.py
- [[views.py]] - code - django_apps/game_data/browse/views.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/registrypy
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY_HttpRequest]]
- 1 edge to [[_COMMUNITY_admin.py]]

## Top bridge nodes
- [[.related_subtable_links()]] - degree 3, connects to 2 communities
- [[registry.py]] - degree 15, connects to 1 community
- [[section_qs_sorted()]] - degree 4, connects to 1 community
- [[validate_aggregate_root_inlines()]] - degree 4, connects to 1 community