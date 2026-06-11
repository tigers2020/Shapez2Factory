---
type: community
cohesion: 0.09
members: 36
---

# Decimal

**Cohesion:** 0.09 - loosely connected
**Members:** 36 nodes

## Members
- [[0026_mining_extraction_rule.py]] - code - django_apps/game_data/migrations/0026_mining_extraction_rule.py
- [[0027_exterior_transport_capacity_tier1.py]] - code - django_apps/game_data/migrations/0027_exterior_transport_capacity_tier1.py
- [[Absolute routed shape throughput from committed rim bundles (CANON mini-unit rat]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/rim_throughput.py
- [[Build ExteriorConnectionPlan from reconstruction-complete map + throughput targe]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/plan.py
- [[Combine per-resource L2 plans so L3 can route belt and pipe goals on mixed maps.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/plan.py
- [[Decimal]] - code - src/shapez2_factory/application/asteroid_lab/layers/shared/ceildiv.py
- [[ExteriorConnectionShortfallReason_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/plan.py
- [[ExteriorConnectorRole_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/plan.py
- [[Integer ceiling division for Decimal throughput rates.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/shared/ceildiv.py
- [[Migration_44]] - code - django_apps/game_data/migrations/0026_mining_extraction_rule.py
- [[Migration_45]] - code - django_apps/game_data/migrations/0027_exterior_transport_capacity_tier1.py
- [[Mining extraction rule row for terrain upper-bound capacity (L1  CLI envelope).]] - rationale - src/shapez2_factory/domain/asteroid_lab/mining_extraction_row.py
- [[MiningExtractionRow_1]] - code - src/shapez2_factory/domain/asteroid_lab/mining_extraction_row.py
- [[Sum ``mini_unit_output × throughput_factor`` for shape-rim commits.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/rim_throughput.py
- [[Terrain upper bound one field cell = one platform at base ×4 mini-units (not ×1]] - rationale - src/shapez2_factory/application/asteroid_lab/reconstruction_capacity.py
- [[Terrain upper-bound capacity from mining extraction (shared Django L1 + CLI run_]] - rationale - src/shapez2_factory/application/asteroid_lab/reconstruction_capacity.py
- [[_empty_plan()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/plan.py
- [[_place_connectors_for_role()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/plan.py
- [[build_exterior_connection_plan()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/plan.py
- [[build_terrain_capacity_summary_row()]] - code - src/shapez2_factory/application/asteroid_lab/reconstruction_capacity.py
- [[ceildiv.py]] - code - django_apps/asteroid_lab/layers/shared/ceildiv.py
- [[ceildiv.py_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/shared/ceildiv.py
- [[ceildiv_decimal()]] - code - src/shapez2_factory/application/asteroid_lab/layers/shared/ceildiv.py
- [[decimal_str()]] - code - src/shapez2_factory/application/asteroid_lab/reconstruction_capacity.py
- [[effective_mini_units()_1]] - code - src/shapez2_factory/application/asteroid_lab/reconstruction_capacity.py
- [[merge_exterior_connection_plans()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/plan.py
- [[mini_unit_output_per_min_for_resource()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/rim_throughput.py
- [[mining_extraction_row.py]] - code - src/shapez2_factory/domain/asteroid_lab/mining_extraction_row.py
- [[output_per_min_from_mini_unit()]] - code - src/shapez2_factory/application/asteroid_lab/reconstruction_capacity.py
- [[plan.py]] - code - django_apps/asteroid_lab/layers/layer_02_exterior_transport/plan.py
- [[plan.py_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/plan.py
- [[reconstruction_capacity.py]] - code - src/shapez2_factory/application/asteroid_lab/reconstruction_capacity.py
- [[rim_throughput.py]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/rim_throughput.py
- [[routed_shape_throughput_per_min()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/rim_throughput.py
- [[seed_exterior_transport_capacity_tier1()]] - code - django_apps/game_data/migrations/0027_exterior_transport_capacity_tier1.py
- [[seed_mining_extraction_rules()]] - code - django_apps/game_data/migrations/0026_mining_extraction_rule.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Decimal
SORT file.name ASC
```

## Connections to other communities
- 12 edges to [[_COMMUNITY_exterior_transport_capacity.py]]
- 6 edges to [[_COMMUNITY_GameDataRulesPort]]
- 5 edges to [[_COMMUNITY_Any]]
- 5 edges to [[_COMMUNITY_ReconstructionCompleteMap]]
- 4 edges to [[_COMMUNITY_json_snapshot_rules.py]]
- 4 edges to [[_COMMUNITY_placement.py]]
- 3 edges to [[_COMMUNITY_execute_layer_02_exterior_transport_plan]]
- 3 edges to [[_COMMUNITY_ExteriorConnectionPlan]]
- 3 edges to [[_COMMUNITY_mining_extraction_rules.py]]
- 1 edge to [[_COMMUNITY_Coord]]
- 1 edge to [[_COMMUNITY_0029_evtc_tier1_shapez2_miner_belt_rates]]
- 1 edge to [[_COMMUNITY_exterior_connection.py]]
- 1 edge to [[_COMMUNITY_exterior_capacity_row.py]]
- 1 edge to [[_COMMUNITY_RouteProbedBundleCandidate]]
- 1 edge to [[_COMMUNITY_evaluate_against_golden()]]
- 1 edge to [[_COMMUNITY_exhaustive_generator.py]]
- 1 edge to [[_COMMUNITY_layout_t.py]]

## Top bridge nodes
- [[Decimal]] - degree 49, connects to 10 communities
- [[build_exterior_connection_plan()]] - degree 12, connects to 4 communities
- [[_place_connectors_for_role()]] - degree 11, connects to 4 communities
- [[build_terrain_capacity_summary_row()]] - degree 9, connects to 3 communities
- [[merge_exterior_connection_plans()]] - degree 5, connects to 2 communities