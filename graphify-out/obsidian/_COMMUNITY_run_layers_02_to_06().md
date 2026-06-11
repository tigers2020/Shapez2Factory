---
type: community
cohesion: 0.20
members: 17
---

# run_layers_02_to_06()

**Cohesion:** 0.20 - loosely connected
**Members:** 17 nodes

## Members
- [[CoreStackRunResult]] - code - src/shapez2_factory/application/asteroid_lab/stack_runner.py
- [[Deprecated alias for ``run_layers_02_to_06`` (PR-3c layer renumber)._1]] - rationale - src/shapez2_factory/application/asteroid_lab/stack_runner.py
- [[DiagnosticLayerSnapshot]] - code - src/shapez2_factory/application/asteroid_lab/stack_runner.py
- [[GeneticSampleSeedSnapshot]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/run.py
- [[Map persisted misnumbered slug literals to canonical slugs.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/contracts/layer_slugs.py
- [[Pure core orchestration for layers 2–6 (Django-free).  The Django wrapper in `]] - rationale - src/shapez2_factory/application/asteroid_lab/stack_runner.py
- [[Pure stack outcome plus the ordered post-summary records the caller may persist.]] - rationale - src/shapez2_factory/application/asteroid_lab/stack_runner.py
- [[SpaceTransportTileCatalog]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sprite_projector.py
- [[_LayerStackRunner_1]] - code - src/shapez2_factory/application/asteroid_lab/stack_runner.py
- [[_diagnostic_for_slug()]] - code - src/shapez2_factory/application/asteroid_lab/stack_runner.py
- [[_layer_index_for_slug()]] - code - src/shapez2_factory/application/asteroid_lab/stack_runner.py
- [[_layer_outcome()]] - code - django_apps/asteroid_lab/services/solver_run_lab_summary.py
- [[load_genetic_sample_seeds()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_fixtures.py
- [[resolve_canonical_layer_slug()]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/layer_slugs.py
- [[run_layers_02_to_05()_1]] - code - src/shapez2_factory/application/asteroid_lab/stack_runner.py
- [[run_layers_02_to_06()_1]] - code - src/shapez2_factory/application/asteroid_lab/stack_runner.py
- [[stack_runner.py_1]] - code - src/shapez2_factory/application/asteroid_lab/stack_runner.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/run_layers_02_to_06
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_write_lab_solver_layer_stack_logs()]]
- 3 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY_ReconstructionCompleteMap]]
- 2 edges to [[_COMMUNITY_run_full_from_cleanup_recon()]]
- 2 edges to [[_COMMUNITY_deconstruct_snapshot()]]
- 2 edges to [[_COMMUNITY_route_layer04_sequential()]]
- 2 edges to [[_COMMUNITY_.write_layer_post_summary()]]
- 1 edge to [[_COMMUNITY_build_solver_runtime_replay_frames_from_]]
- 1 edge to [[_COMMUNITY_generate_candidates()]]
- 1 edge to [[_COMMUNITY_ExteriorConnectionPlan]]
- 1 edge to [[_COMMUNITY_try_load_default_space_transport_catalog]]
- 1 edge to [[_COMMUNITY_space_transport_catalog_snapshot.py]]
- 1 edge to [[_COMMUNITY_build_layer05_transport_post_summary_met]]
- 1 edge to [[_COMMUNITY_evaluate_against_golden()]]
- 1 edge to [[_COMMUNITY_golden_fixture_fixtures.py]]
- 1 edge to [[_COMMUNITY_layer_slugs.py]]

## Top bridge nodes
- [[run_layers_02_to_06()_1]] - degree 17, connects to 5 communities
- [[GeneticSampleSeedSnapshot]] - degree 8, connects to 4 communities
- [[run_layers_02_to_05()_1]] - degree 10, connects to 3 communities
- [[resolve_canonical_layer_slug()]] - degree 9, connects to 3 communities
- [[SpaceTransportTileCatalog]] - degree 6, connects to 3 communities