---
type: community
cohesion: 0.14
members: 22
---

# json_snapshot_rules.py

**Cohesion:** 0.14 - loosely connected
**Members:** 22 nodes

## Members
- [[.__init__()_13]] - code - src/shapez2_factory/adapters/asteroid_lab/json_snapshot_rules.py
- [[.__init__()_14]] - code - src/shapez2_factory/adapters/asteroid_lab/json_snapshot_rules.py
- [[.exterior_connector_capacity()]] - code - src/shapez2_factory/adapters/asteroid_lab/json_snapshot_rules.py
- [[.exterior_connector_capacity()_1]] - code - src/shapez2_factory/application/asteroid_lab/ports/game_data_rules.py
- [[.from_file()_1]] - code - src/shapez2_factory/adapters/asteroid_lab/json_snapshot_rules.py
- [[.from_payload()_1]] - code - src/shapez2_factory/adapters/asteroid_lab/json_snapshot_rules.py
- [[.mining_extraction_rule()]] - code - src/shapez2_factory/adapters/asteroid_lab/json_snapshot_rules.py
- [[.mining_extraction_rule()_1]] - code - src/shapez2_factory/application/asteroid_lab/ports/game_data_rules.py
- [[ExteriorCapacityRow]] - code - src/shapez2_factory/application/asteroid_lab/ports/game_data_rules.py
- [[GameDataRulesPort_1]] - code - src/shapez2_factory/application/asteroid_lab/ports/game_data_rules.py
- [[GameDataSnapshotInvalid]] - code - src/shapez2_factory/adapters/asteroid_lab/json_snapshot_rules.py
- [[GameDataSnapshotIssue]] - code - src/shapez2_factory/adapters/asteroid_lab/json_snapshot_rules.py
- [[JsonSnapshotGameDataRulesAdapter_1]] - code - src/shapez2_factory/adapters/asteroid_lab/json_snapshot_rules.py
- [[MiningExtractionRow]] - code - src/shapez2_factory/application/asteroid_lab/ports/game_data_rules.py
- [[Return the active mining extraction row; raise ``LookupError`` when no row exist]] - rationale - src/shapez2_factory/application/asteroid_lab/ports/game_data_rules.py
- [[Return the per-connector capacity row; raise ``LookupError`` when no row exists.]] - rationale - src/shapez2_factory/application/asteroid_lab/ports/game_data_rules.py
- [[_parse_capacity_rows()]] - code - src/shapez2_factory/adapters/asteroid_lab/json_snapshot_rules.py
- [[_parse_mining_rows()]] - code - src/shapez2_factory/adapters/asteroid_lab/json_snapshot_rules.py
- [[``GameDataRulesPort`` solver-facing game-data rules (L2 decouple, PR-CLI-2b).]] - rationale - src/shapez2_factory/application/asteroid_lab/ports/game_data_rules.py
- [[``JsonSnapshotGameDataRulesAdapter`` — core game-data rules from a frozen snapsh]] - rationale - src/shapez2_factory/adapters/asteroid_lab/json_snapshot_rules.py
- [[game_data_rules.py]] - code - src/shapez2_factory/application/asteroid_lab/ports/game_data_rules.py
- [[json_snapshot_rules.py]] - code - src/shapez2_factory/adapters/asteroid_lab/json_snapshot_rules.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/json_snapshot_rulespy
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_Decimal]]
- 2 edges to [[_COMMUNITY_mining_extraction_rules.py]]
- 1 edge to [[_COMMUNITY_Path]]
- 1 edge to [[_COMMUNITY_Protocol]]
- 1 edge to [[_COMMUNITY_StrEnum]]
- 1 edge to [[_COMMUNITY_Exception]]
- 1 edge to [[_COMMUNITY_Enum]]

## Top bridge nodes
- [[json_snapshot_rules.py]] - degree 8, connects to 2 communities
- [[GameDataSnapshotInvalid]] - degree 7, connects to 1 community
- [[_parse_mining_rows()]] - degree 5, connects to 1 community
- [[.__init__()_14]] - degree 4, connects to 1 community
- [[.from_file()_1]] - degree 4, connects to 1 community