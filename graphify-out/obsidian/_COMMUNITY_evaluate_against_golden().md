---
type: community
cohesion: 0.09
members: 41
---

# evaluate_against_golden()

**Cohesion:** 0.09 - loosely connected
**Members:** 41 nodes

## Members
- [[Artifact-level golden oracle evaluation (no blueprint assembler required).]] - rationale - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_eval.py
- [[BFS roots from L2 connectors and L5 route group cells only.]] - rationale - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_eval.py
- [[Golden asteroid L4 capacity  inner-fill target metrics (measurement only).  S]] - rationale - src/shapez2_factory/application/asteroid_lab/experiments/golden_l4_capacity_metrics.py
- [[GoldenEvalResult]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_eval.py
- [[GoldenL4CapacityMetrics]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_l4_capacity_metrics.py
- [[GoldenOracle]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_eval.py
- [[GoldenSolverArtifacts]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_l4_capacity_metrics.py
- [[L5-confirmed throughput only placements with committed routes count.]] - rationale - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_eval.py
- [[Map exterior resource kind or route transport kind to ``shape``  ``fluid``.]] - rationale - src/shapez2_factory/application/asteroid_lab/experiments/transport_kind_normalization.py
- [[Merge empty field shell with L3 equipment and L5 transport tiles.]] - rationale - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_assembler.py
- [[Normalize resource and transport layout kinds to a shared transport family.]] - rationale - src/shapez2_factory/application/asteroid_lab/experiments/transport_kind_normalization.py
- [[Optional candidate blueprint export from solver artifacts (PR-6).]] - rationale - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_assembler.py
- [[_belt_edges_from_paths()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_eval.py
- [[_candidate_extractor_anchors_direct()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_eval.py
- [[_connectivity_roots()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_eval.py
- [[_entry()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_assembler.py
- [[_f1_score()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_eval.py
- [[_hard_validity()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_eval.py
- [[_jaccard()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_eval.py
- [[_kind_token()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/transport_kind_normalization.py
- [[_l3_footprints_overlap()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_eval.py
- [[_normalize_anchor_set()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_eval.py
- [[_orphan_count()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_eval.py
- [[_route_cells_from_plan()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_eval.py
- [[_route_island_count()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_eval.py
- [[_routed_throughput_per_min()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_eval.py
- [[_stack_l2_l5_complete()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_eval.py
- [[assemble_candidate_blueprint()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_assembler.py
- [[compute_golden_l4_capacity_metrics()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_l4_capacity_metrics.py
- [[encode_candidate_copy_string()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_assembler.py
- [[evaluate_against_golden()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_eval.py
- [[format_l4_capacity_diagnostics()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_l4_capacity_metrics.py
- [[format_transport_kind_mismatch_diagnostic()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/transport_kind_normalization.py
- [[golden_fixture_assembler.py]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_assembler.py
- [[golden_fixture_eval.py]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_eval.py
- [[golden_l4_capacity_metrics.py]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_l4_capacity_metrics.py
- [[max_group_sets_for_field_count()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_l4_capacity_metrics.py
- [[min_inner_group_sets_target()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_l4_capacity_metrics.py
- [[normalize_transport_family()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/transport_kind_normalization.py
- [[transport_families_compatible()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/transport_kind_normalization.py
- [[transport_kind_normalization.py]] - code - src/shapez2_factory/application/asteroid_lab/experiments/transport_kind_normalization.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/evaluate_against_golden
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_Coord]]
- 2 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY_decode_copy_string()]]
- 1 edge to [[_COMMUNITY_Enum]]
- 1 edge to [[_COMMUNITY_run_layers_02_to_06()]]
- 1 edge to [[_COMMUNITY_Decimal]]
- 1 edge to [[_COMMUNITY_build_failed_source_diagnostic()]]

## Top bridge nodes
- [[assemble_candidate_blueprint()]] - degree 7, connects to 2 communities
- [[evaluate_against_golden()]] - degree 18, connects to 1 community
- [[transport_kind_normalization.py]] - degree 6, connects to 1 community
- [[_connectivity_roots()]] - degree 5, connects to 1 community
- [[_routed_throughput_per_min()]] - degree 5, connects to 1 community