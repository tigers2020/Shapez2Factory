---
type: community
cohesion: 0.20
members: 17
---

# _import_connectable_attachment()

**Cohesion:** 0.20 - loosely connected
**Members:** 17 nodes

## Members
- [[Deterministic signatures for ConnectableSimulation connectable_key.]] - rationale - django_apps/game_data/services/connectable_signatures.py
- [[Import simulation_systems.json into C-lite normalized models.]] - rationale - django_apps/game_data/importers/simulation_systems.py
- [[SimulationConnector]] - code - django_apps/game_data/importers/simulation_systems.py
- [[SimulationProfile]] - code - django_apps/game_data/importers/simulation_systems.py
- [[_bounds_coords()]] - code - django_apps/game_data/importers/simulation_systems.py
- [[_building_internal_name()]] - code - django_apps/game_data/importers/simulation_systems.py
- [[_ensure_profile()]] - code - django_apps/game_data/importers/simulation_systems.py
- [[_import_connectable_attachment()]] - code - django_apps/game_data/importers/simulation_systems.py
- [[_set_connector_property()]] - code - django_apps/game_data/importers/simulation_systems.py
- [[build_connectable_key()]] - code - django_apps/game_data/services/connectable_signatures.py
- [[build_connector_signature()]] - code - django_apps/game_data/services/connectable_signatures.py
- [[build_lane_signature()]] - code - django_apps/game_data/services/connectable_signatures.py
- [[connectable_signatures.py]] - code - django_apps/game_data/services/connectable_signatures.py
- [[connector_type_name()]] - code - django_apps/game_data/services/connectable_signatures.py
- [[pivot_direction()]] - code - django_apps/game_data/services/connectable_signatures.py
- [[simulation_systems.py]] - code - django_apps/game_data/importers/simulation_systems.py
- [[simulation_transport_slug()]] - code - django_apps/game_data/services/connectable_signatures.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/_import_connectable_attachment
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_Any]]
- 3 edges to [[_COMMUNITY_import_simulation_systems()]]
- 1 edge to [[_COMMUNITY_ImportContext]]
- 1 edge to [[_COMMUNITY_simulation_speed_extract.py]]

## Top bridge nodes
- [[_import_connectable_attachment()]] - degree 14, connects to 4 communities
- [[simulation_systems.py]] - degree 7, connects to 1 community
- [[build_connector_signature()]] - degree 5, connects to 1 community
- [[connector_type_name()]] - degree 4, connects to 1 community
- [[simulation_transport_slug()]] - degree 4, connects to 1 community