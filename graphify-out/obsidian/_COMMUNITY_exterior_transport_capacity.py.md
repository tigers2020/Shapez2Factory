---
type: community
cohesion: 0.13
members: 27
---

# exterior_transport_capacity.py

**Cohesion:** 0.13 - loosely connected
**Members:** 27 nodes

## Members
- [[Alias for inner-belt throughput (legacy name).]] - rationale - django_apps/game_data/services/exterior_transport_capacity.py
- [[ExteriorFluidTransportCapacity_1]] - code - django_apps/game_data/services/exterior_transport_capacity.py
- [[ExteriorShapeTransportCapacity_1]] - code - django_apps/game_data/services/exterior_transport_capacity.py
- [[Full mini miner mini_unit × miner_full_output_multiplier (tier-1 30×16 = 480m]] - rationale - django_apps/game_data/services/exterior_transport_capacity.py
- [[Inner belt mini_unit × buildings_per_regular_belt (tier-1 30×4 = 120min).]] - rationale - django_apps/game_data/services/exterior_transport_capacity.py
- [[One Space Belt building ``line × lines_per_space_belt`` (tier-1 480×12 = 5760]] - rationale - django_apps/game_data/services/exterior_transport_capacity.py
- [[One exterior Space Belt line at full miner export (tier-1 480 shapesmin).]] - rationale - django_apps/game_data/services/exterior_transport_capacity.py
- [[Per-building Space Belt or saturated Space Pipe cap for connector sizing.]] - rationale - django_apps/game_data/services/exterior_transport_capacity.py
- [[Queryable EVTC exterior transport caps. Runtime SoT — no RTTP imports.]] - rationale - django_apps/game_data/services/exterior_transport_capacity.py
- [[Wiki cap inner_belt × space_belt_full_belt_count (tier-1 120×48 = 5760min).]] - rationale - django_apps/game_data/services/exterior_transport_capacity.py
- [[_exterior_transport_capacity_rows()]] - code - django_apps/game_data/services/game_data_snapshot_export.py
- [[``ceil(max_throughput  line_throughput)``; shape only.]] - rationale - django_apps/game_data/services/exterior_transport_capacity.py
- [[``ceil(max_throughput  per_building_connector_capacity)``; 0 when throughput ≤]] - rationale - django_apps/game_data/services/exterior_transport_capacity.py
- [[exterior_connector_capacity_per_min()]] - code - django_apps/game_data/services/exterior_transport_capacity.py
- [[exterior_connector_count_for_throughput()]] - code - django_apps/game_data/services/exterior_transport_capacity.py
- [[exterior_line_count_for_throughput()]] - code - django_apps/game_data/services/exterior_transport_capacity.py
- [[exterior_line_throughput_per_min()]] - code - django_apps/game_data/services/exterior_transport_capacity.py
- [[exterior_transport_capacity.py_1]] - code - django_apps/game_data/services/exterior_transport_capacity.py
- [[full_miner_output_per_min_from_row()]] - code - django_apps/game_data/services/exterior_transport_capacity.py
- [[get_active_exterior_fluid_transport_capacity()]] - code - django_apps/game_data/services/exterior_transport_capacity.py
- [[get_active_exterior_shape_transport_capacity()]] - code - django_apps/game_data/services/exterior_transport_capacity.py
- [[inner_belt_throughput_per_min_from_row()]] - code - django_apps/game_data/services/exterior_transport_capacity.py
- [[line_throughput_per_min_from_row()]] - code - django_apps/game_data/services/exterior_transport_capacity.py
- [[regular_belt_throughput_per_min_from_row()]] - code - django_apps/game_data/services/exterior_transport_capacity.py
- [[space_belt_connector_capacity_per_min_from_row()]] - code - django_apps/game_data/services/exterior_transport_capacity.py
- [[space_belt_max_per_min_from_row()]] - code - django_apps/game_data/services/exterior_transport_capacity.py
- [[space_pipe_max_per_min_from_row()]] - code - django_apps/game_data/services/exterior_transport_capacity.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/exterior_transport_capacitypy
SORT file.name ASC
```

## Connections to other communities
- 12 edges to [[_COMMUNITY_Decimal]]
- 4 edges to [[_COMMUNITY_build_game_data_snapshot_payload()]]
- 3 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY_mining_extraction_rules.py]]

## Top bridge nodes
- [[get_active_exterior_shape_transport_capacity()]] - degree 6, connects to 2 communities
- [[get_active_exterior_fluid_transport_capacity()]] - degree 5, connects to 2 communities
- [[exterior_line_count_for_throughput()]] - degree 5, connects to 2 communities
- [[exterior_connector_count_for_throughput()]] - degree 5, connects to 2 communities
- [[_exterior_transport_capacity_rows()]] - degree 5, connects to 2 communities