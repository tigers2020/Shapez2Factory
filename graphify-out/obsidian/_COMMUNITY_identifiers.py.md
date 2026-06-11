---
type: community
cohesion: 0.08
members: 52
---

# identifiers.py

**Cohesion:** 0.08 - loosely connected
**Members:** 52 nodes

## Members
- [[.__init__()_2]] - code - django_apps/game_data/importers/base.py
- [[.bump()]] - code - django_apps/game_data/importers/base.py
- [[.record_source_row()]] - code - django_apps/game_data/importers/base.py
- [[.record_unknown()]] - code - django_apps/game_data/importers/base.py
- [[.record_unresolved_reference()]] - code - django_apps/game_data/importers/base.py
- [[Canonical ID policy domain keys only, never runtime CLR names.]] - rationale - django_apps/game_data/services/identifiers.py
- [[GameDataReference]] - code - django_apps/game_data/importers/base.py
- [[Hash (type_name, assembly_name) — CLR names may contain UnityEngine. segments.]] - rationale - django_apps/game_data/services/identifiers.py
- [[ImportContext]] - code - django_apps/game_data/importers/base.py
- [[InvalidCanonicalIdError]] - code - django_apps/game_data/services/identifiers.py
- [[Legacy Phase A row id — prefer canonical_simulation_group_id for grouping.]] - rationale - django_apps/game_data/services/identifiers.py
- [[SourceObject]] - code - django_apps/game_data/importers/importer.py
- [[Stable id for ``SimulationClrProvenance`` (CLR ``source_type_name`` capture).]] - rationale - django_apps/game_data/services/identifiers.py
- [[Upsert row-level provenance; UK remains (batch, file, row_index).]] - rationale - django_apps/game_data/importers/base.py
- [[_slug()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_building_group()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_building_variant()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_clr_type()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_component_kind()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_connectable_simulation()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_connector()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_content_asset()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_fluid_color()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_footprint_tile()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_group_member()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_import_batch()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_lazy_localized_replacement()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_lazy_localized_text()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_meta_reference()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_placement_rule()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_quadrant_slot()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_research_cost()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_research_mechanic()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_research_node()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_research_prerequisite()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_research_upgrade()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_shape_layer()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_shape_recipe()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_simulation_buffable_speed()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_simulation_clr_provenance()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_simulation_connector()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_simulation_entry()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_simulation_group_id()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_simulation_group_key()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_simulation_lane_definition()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_simulation_multiple_belt_speed()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_toolbar_element()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_toolbar_node()]] - code - django_apps/game_data/services/identifiers.py
- [[canonical_transport_kind()]] - code - django_apps/game_data/services/identifiers.py
- [[hash_preview()]] - code - django_apps/game_data/services/identifiers.py
- [[identifiers.py]] - code - django_apps/game_data/services/identifiers.py
- [[reject_runtime_canonical()]] - code - django_apps/game_data/services/identifiers.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/identifierspy
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_Any]]
- 1 edge to [[_COMMUNITY_ValueError]]
- 1 edge to [[_COMMUNITY_build_asteroid_game_data_snapshot_with_p]]
- 1 edge to [[_COMMUNITY_import_toolbar_tree()]]
- 1 edge to [[_COMMUNITY_import_shape_rows()]]
- 1 edge to [[_COMMUNITY_GameDataImporter]]

## Top bridge nodes
- [[.record_source_row()]] - degree 5, connects to 2 communities
- [[ImportContext]] - degree 6, connects to 1 community
- [[InvalidCanonicalIdError]] - degree 4, connects to 1 community
- [[.record_unknown()]] - degree 3, connects to 1 community
- [[SourceObject]] - degree 3, connects to 1 community