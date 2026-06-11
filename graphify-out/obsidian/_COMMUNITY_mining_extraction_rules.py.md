---
type: community
cohesion: 0.36
members: 9
---

# mining_extraction_rules.py

**Cohesion:** 0.36 - loosely connected
**Members:** 9 nodes

## Members
- [[LookupError]] - code - django_apps/game_data/services/game_data_snapshot_export.py
- [[MiningExtractionRule_1]] - code - django_apps/game_data/services/mining_extraction_rules.py
- [[Queryable CANON extraction rates (L1b). No RTTP imports.]] - rationale - django_apps/game_data/services/mining_extraction_rules.py
- [[assert_throughput_factor_matches_extensions()]] - code - django_apps/game_data/services/mining_extraction_rules.py
- [[effective_mini_units()]] - code - django_apps/game_data/services/mining_extraction_rules.py
- [[get_active_rule()]] - code - django_apps/game_data/services/mining_extraction_rules.py
- [[max_output_per_miner()]] - code - django_apps/game_data/services/mining_extraction_rules.py
- [[mining_extraction_rules.py]] - code - django_apps/game_data/services/mining_extraction_rules.py
- [[output_per_min()]] - code - django_apps/game_data/services/mining_extraction_rules.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/mining_extraction_rulespy
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_Decimal]]
- 2 edges to [[_COMMUNITY_exterior_transport_capacity.py]]
- 2 edges to [[_COMMUNITY_build_game_data_snapshot_payload()]]
- 2 edges to [[_COMMUNITY_json_snapshot_rules.py]]
- 1 edge to [[_COMMUNITY_ReconstructionCompleteMap]]

## Top bridge nodes
- [[LookupError]] - degree 6, connects to 3 communities
- [[get_active_rule()]] - degree 5, connects to 2 communities
- [[mining_extraction_rules.py]] - degree 7, connects to 1 community
- [[max_output_per_miner()]] - degree 5, connects to 1 community
- [[output_per_min()]] - degree 4, connects to 1 community