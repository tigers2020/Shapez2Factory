---
type: community
cohesion: 0.12
members: 27
---

# import_toolbar_tree()

**Cohesion:** 0.12 - loosely connected
**Members:** 27 nodes

## Members
- [[Extract toolbar row identity from definition_snapshot envelopes.]] - rationale - django_apps/game_data/importers/toolbar_identity.py
- [[Four-pass toolbar tree import TreeNode hierarchy + ACTION elements + placements]] - rationale - django_apps/game_data/importers/toolbar_tree.py
- [[Last ``Childrenn`` segment in a flattened toolbar ``display_name_key`` path.]] - rationale - django_apps/game_data/importers/base.py
- [[PendingToolbarNode]] - code - django_apps/game_data/importers/toolbar_tree.py
- [[Return (internal_name, localized_title_key, icon_identifier).]] - rationale - django_apps/game_data/importers/toolbar_identity.py
- [[Shared importer utilities.]] - rationale - django_apps/game_data/importers/base.py
- [[Structure-based toolbar tree node classification (no CLR wildcard matching).]] - rationale - django_apps/game_data/services/toolbar_node_kind.py
- [[_element_display_name()]] - code - django_apps/game_data/importers/toolbar_tree.py
- [[_element_stable_key()]] - code - django_apps/game_data/importers/toolbar_tree.py
- [[base.py]] - code - django_apps/game_data/importers/base.py
- [[build_children_by_parent()]] - code - django_apps/game_data/services/toolbar_node_kind.py
- [[classify_toolbar_node_kind()]] - code - django_apps/game_data/services/toolbar_node_kind.py
- [[compute_action_subtree()]] - code - django_apps/game_data/services/toolbar_node_kind.py
- [[depth_from_tree_path()]] - code - django_apps/game_data/services/toolbar_node_kind.py
- [[depth_sorted_paths()]] - code - django_apps/game_data/services/toolbar_node_kind.py
- [[dig()]] - code - django_apps/game_data/importers/base.py
- [[has_placer_id()]] - code - django_apps/game_data/services/toolbar_node_kind.py
- [[import_toolbar_tree()]] - code - django_apps/game_data/importers/toolbar_tree.py
- [[is_separator_row()]] - code - django_apps/game_data/services/toolbar_node_kind.py
- [[parent_path_from_tree_path()]] - code - django_apps/game_data/services/toolbar_node_kind.py
- [[parse_toolbar_child_index()]] - code - django_apps/game_data/importers/base.py
- [[row_is_action()]] - code - django_apps/game_data/services/toolbar_node_kind.py
- [[toolbar_identity.py]] - code - django_apps/game_data/importers/toolbar_identity.py
- [[toolbar_node_kind.py]] - code - django_apps/game_data/services/toolbar_node_kind.py
- [[toolbar_row_identity()]] - code - django_apps/game_data/importers/toolbar_identity.py
- [[toolbar_tree.py]] - code - django_apps/game_data/importers/toolbar_tree.py
- [[topological_paths()]] - code - django_apps/game_data/services/toolbar_node_kind.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/import_toolbar_tree
SORT file.name ASC
```

## Connections to other communities
- 9 edges to [[_COMMUNITY_Any]]
- 6 edges to [[_COMMUNITY_GameDataImporter]]
- 1 edge to [[_COMMUNITY_identifiers.py]]
- 1 edge to [[_COMMUNITY_import_shape_rows()]]
- 1 edge to [[_COMMUNITY_ImportContext]]
- 1 edge to [[_COMMUNITY_parse_lazy_localized_text()]]
- 1 edge to [[_COMMUNITY_recipe_graph_recompute.py]]

## Top bridge nodes
- [[import_toolbar_tree()]] - degree 15, connects to 3 communities
- [[dig()]] - degree 12, connects to 3 communities
- [[toolbar_row_identity()]] - degree 6, connects to 2 communities
- [[row_is_action()]] - degree 5, connects to 1 community
- [[classify_toolbar_node_kind()]] - degree 5, connects to 1 community