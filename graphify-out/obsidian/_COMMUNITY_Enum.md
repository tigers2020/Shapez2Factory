---
type: community
cohesion: 0.09
members: 24
---

# Enum

**Cohesion:** 0.09 - loosely connected
**Members:** 24 nodes

## Members
- [[Beam-selector soft-penalty weight profiles (not solver feedback from replay).]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/contracts/penalty_mode.py
- [[BeamPenaltyWeights]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/penalty_mode.py
- [[Enum]] - code
- [[ExteriorConnectorRole]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/exterior_connector_role.py
- [[Lab replay timeline enums (Phase 9A product contract).]] - rationale - django_apps/asteroid_lab/replay/replay_enums.py
- [[Layer 02 exterior connector role (required vs spare).]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/contracts/exterior_connector_role.py
- [[Lifecycle phase marker on a replay timeline frame (not a separate track).]] - rationale - django_apps/asteroid_lab/replay/replay_enums.py
- [[OperationDefinition]] - code - django_apps/shapez_solver/domain/operations.py
- [[OperationType]] - code - django_apps/shapez_solver/domain/operations.py
- [[PenaltyMode]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/penalty_mode.py
- [[Predictive fitness penalty profiles for Layer 03 beam selection (10B v0.1).]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/contracts/penalty_mode.py
- [[ReplayEventType_1]] - code - django_apps/asteroid_lab/replay/replay_enums.py
- [[ReplayPhase_1]] - code - django_apps/asteroid_lab/replay/replay_enums.py
- [[Stack run status codes for layer 2-5 orchestration.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/contracts/stack_status.py
- [[StackRunStatus_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/stack_status.py
- [[Wire ``event_type`` for replay timeline frames (free strings forbidden).]] - rationale - django_apps/asteroid_lab/replay/replay_enums.py
- [[beam_penalty_weights()]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/penalty_mode.py
- [[exterior_connector_role.py]] - code - django_apps/asteroid_lab/layers/contracts/exterior_connector_role.py
- [[exterior_connector_role.py_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/exterior_connector_role.py
- [[operations.py]] - code - django_apps/shapez_solver/domain/operations.py
- [[penalty_mode.py]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/penalty_mode.py
- [[replay_enums.py]] - code - django_apps/asteroid_lab/replay/replay_enums.py
- [[stack_status.py]] - code - django_apps/asteroid_lab/layers/contracts/stack_status.py
- [[stack_status.py_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/stack_status.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Enum
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_StrEnum]]
- 2 edges to [[_COMMUNITY_shape_pattern.py]]
- 1 edge to [[_COMMUNITY_layer_post_summary_log.py]]
- 1 edge to [[_COMMUNITY_GeneTemplate]]
- 1 edge to [[_COMMUNITY_build_initial_replay_for_map_input()]]
- 1 edge to [[_COMMUNITY_gene_template_from_miner_gene_seed()]]
- 1 edge to [[_COMMUNITY_runtime_gene_template_source.py]]
- 1 edge to [[_COMMUNITY_solver_runtime_types.py]]
- 1 edge to [[_COMMUNITY_AsteroidLabTraceLogger]]
- 1 edge to [[_COMMUNITY_build_game_data_snapshot_payload()]]
- 1 edge to [[_COMMUNITY_simulation_speed_extract.py]]
- 1 edge to [[_COMMUNITY_genetic_sample_seed_snapshot.py]]
- 1 edge to [[_COMMUNITY_json_snapshot_rules.py]]
- 1 edge to [[_COMMUNITY_Exception]]
- 1 edge to [[_COMMUNITY_space_transport_catalog_snapshot.py]]
- 1 edge to [[_COMMUNITY_evaluate_against_golden()]]
- 1 edge to [[_COMMUNITY_cardinal_edge.py]]
- 1 edge to [[_COMMUNITY_exterior_connection.py]]
- 1 edge to [[_COMMUNITY_layer04_inner_fill.py]]
- 1 edge to [[_COMMUNITY_build_failed_source_diagnostic()]]
- 1 edge to [[_COMMUNITY_layer05_route.py]]
- 1 edge to [[_COMMUNITY_layer_post_summary.py]]
- 1 edge to [[_COMMUNITY_placement_state.py]]
- 1 edge to [[_COMMUNITY_rim_greedy.py]]
- 1 edge to [[_COMMUNITY_rim_greedy_append.py]]
- 1 edge to [[_COMMUNITY_rim_placement.py]]
- 1 edge to [[_COMMUNITY_exhaustive_generator.py]]
- 1 edge to [[_COMMUNITY_transport_kind.py]]
- 1 edge to [[_COMMUNITY_coord_frames.py]]
- 1 edge to [[_COMMUNITY_game_data_snapshot_provenance.py]]
- 1 edge to [[_COMMUNITY_enums.py]]
- 1 edge to [[_COMMUNITY__run_artifact()]]
- 1 edge to [[_COMMUNITY_RouteProbedBundleCandidate]]

## Top bridge nodes
- [[Enum]] - degree 38, connects to 32 communities
- [[PenaltyMode]] - degree 4, connects to 1 community
- [[beam_penalty_weights()]] - degree 4, connects to 1 community
- [[ReplayPhase_1]] - degree 3, connects to 1 community
- [[ReplayEventType_1]] - degree 3, connects to 1 community