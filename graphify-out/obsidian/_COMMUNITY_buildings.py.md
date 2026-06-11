---
type: community
cohesion: 0.29
members: 10
---

# buildings.py

**Cohesion:** 0.29 - loosely connected
**Members:** 10 nodes

## Members
- [[BuildingConnectorRow]] - code - django_apps/game_data/selectors/buildings.py
- [[BuildingFootprintRow]] - code - django_apps/game_data/selectors/buildings.py
- [[BuildingRowsBundle]] - code - django_apps/game_data/selectors/buildings.py
- [[BuildingVariantRow]] - code - django_apps/game_data/selectors/buildings.py
- [[NamedTuple]] - code
- [[TransportRegistryQueryRow]] - code - django_apps/game_data/selectors/transport_registry.py
- [[buildings.py_1]] - code - django_apps/game_data/selectors/buildings.py
- [[fetch_building_rows_for_batch()]] - code - django_apps/game_data/selectors/buildings.py
- [[fetch_transport_rows_for_batch()]] - code - django_apps/game_data/selectors/transport_registry.py
- [[transport_registry.py]] - code - django_apps/game_data/selectors/transport_registry.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/buildingspy
SORT file.name ASC
```
