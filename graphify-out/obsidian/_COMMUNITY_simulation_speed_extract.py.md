---
type: community
cohesion: 0.16
members: 23
---

# simulation_speed_extract.py

**Cohesion:** 0.16 - loosely connected
**Members:** 23 nodes

## Members
- [[Extract typed fields from simulation_parameters speed blobs (dump-verified shape]] - rationale - django_apps/game_data/services/simulation_speed_extract.py
- [[Import simulation_parameters speed keys into typed per-system tables.]] - rationale - django_apps/game_data/importers/simulation_speeds.py
- [[ResearchUpgrade]] - code - django_apps/game_data/importers/simulation_speeds.py
- [[Route by ``$type`` first, then parameter_name (dump has no cross-type rows).]] - rationale - django_apps/game_data/services/simulation_speed_extract.py
- [[SimulationBuffableSpeed]] - code - django_apps/game_data/importers/simulation_speeds.py
- [[SimulationSystem]] - code - django_apps/game_data/services/simulation_parameter_registry.py
- [[SpeedRoute]] - code - django_apps/game_data/services/simulation_speed_extract.py
- [[SpeedShapeError]] - code - django_apps/game_data/services/simulation_speed_extract.py
- [[_import_global_belt_policy_from_buffable()]] - code - django_apps/game_data/importers/simulation_speeds.py
- [[_record_speed_import_issue()]] - code - django_apps/game_data/importers/simulation_speeds.py
- [[_resolve_research_upgrade()]] - code - django_apps/game_data/importers/simulation_speeds.py
- [[classify_speed_entry()]] - code - django_apps/game_data/services/simulation_speed_extract.py
- [[dump_type_name()]] - code - django_apps/game_data/services/simulation_speed_extract.py
- [[import_simulation_speeds()]] - code - django_apps/game_data/importers/simulation_speeds.py
- [[parameter_matches_route()]] - code - django_apps/game_data/services/simulation_speed_extract.py
- [[parse_buffable_speed_blob()]] - code - django_apps/game_data/services/simulation_speed_extract.py
- [[parse_multiple_speed_blob()]] - code - django_apps/game_data/services/simulation_speed_extract.py
- [[research_upgrade_key()]] - code - django_apps/game_data/services/simulation_speed_extract.py
- [[simulation_speed_extract.py]] - code - django_apps/game_data/services/simulation_speed_extract.py
- [[simulation_speeds.py]] - code - django_apps/game_data/importers/simulation_speeds.py
- [[steps_per_tick_value()]] - code - django_apps/game_data/services/simulation_speed_extract.py
- [[validate_buffable_shape()]] - code - django_apps/game_data/services/simulation_speed_extract.py
- [[validate_multiple_shape()]] - code - django_apps/game_data/services/simulation_speed_extract.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/simulation_speed_extractpy
SORT file.name ASC
```

## Connections to other communities
- 9 edges to [[_COMMUNITY_Any]]
- 3 edges to [[_COMMUNITY_ImportContext]]
- 2 edges to [[_COMMUNITY_import_simulation_systems()]]
- 1 edge to [[_COMMUNITY_ValueError]]
- 1 edge to [[_COMMUNITY_StrEnum]]
- 1 edge to [[_COMMUNITY__import_connectable_attachment()]]
- 1 edge to [[_COMMUNITY_Enum]]

## Top bridge nodes
- [[import_simulation_speeds()]] - degree 12, connects to 3 communities
- [[SimulationSystem]] - degree 4, connects to 2 communities
- [[_record_speed_import_issue()]] - degree 4, connects to 2 communities
- [[simulation_speed_extract.py]] - degree 13, connects to 1 community
- [[parse_buffable_speed_blob()]] - degree 8, connects to 1 community