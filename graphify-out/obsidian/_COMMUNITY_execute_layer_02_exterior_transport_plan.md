---
type: community
cohesion: 0.25
members: 11
---

# execute_layer_02_exterior_transport_plan

**Cohesion:** 0.25 - loosely connected
**Members:** 11 nodes

## Members
- [[Layer 2 exterior transport builds ExteriorConnectionPlan from complete map.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/run.py
- [[ORM export → core JSON adapter (single resolution path).]] - rationale - django_apps/asteroid_lab/adapters/orm_game_data_rules.py
- [[ORM-backed game-data rules (transitional, Django side) — PR-CLI-2b.  Single se]] - rationale - django_apps/asteroid_lab/adapters/orm_game_data_rules.py
- [[Run Layer 02 planning (pure; no IO).]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/run.py
- [[Stack runner entry; returns None when planning inputs are not provided (stub hol]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/run.py
- [[build_orm_game_data_rules()]] - code - django_apps/asteroid_lab/adapters/orm_game_data_rules.py
- [[execute_layer_02_exterior_transport_plan()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/run.py
- [[orm_game_data_rules.py]] - code - django_apps/asteroid_lab/adapters/orm_game_data_rules.py
- [[run.py_1]] - code - django_apps/asteroid_lab/layers/layer_02_exterior_transport/run.py
- [[run.py_7]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/run.py
- [[run_layer_02_exterior_transport()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/run.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/execute_layer_02_exterior_transport_plan
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_Decimal]]
- 3 edges to [[_COMMUNITY_ReconstructionCompleteMap]]
- 2 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY_GameDataRulesPort]]
- 2 edges to [[_COMMUNITY_ExteriorConnectionPlan]]
- 1 edge to [[_COMMUNITY_golden_fixture_fixtures.py]]
- 1 edge to [[_COMMUNITY_build_game_data_snapshot_payload()]]
- 1 edge to [[_COMMUNITY_run_full_from_cleanup_recon()]]

## Top bridge nodes
- [[execute_layer_02_exterior_transport_plan()]] - degree 11, connects to 5 communities
- [[run_layer_02_exterior_transport()]] - degree 10, connects to 5 communities
- [[build_orm_game_data_rules()]] - degree 7, connects to 3 communities
- [[run.py_7]] - degree 4, connects to 1 community