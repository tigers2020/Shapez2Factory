---
source_file: "src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_eval.py"
type: "code"
community: "evaluate_against_golden()"
location: "L301"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/evaluate_against_golden
---

# evaluate_against_golden()

## Connections
- [[GoldenEvalResult]] - `calls` [EXTRACTED]
- [[GoldenOracle]] - `references` [EXTRACTED]
- [[GoldenSolverArtifacts]] - `references` [EXTRACTED]
- [[_belt_edges_from_paths()]] - `calls` [EXTRACTED]
- [[_candidate_extractor_anchors_direct()]] - `calls` [EXTRACTED]
- [[_connectivity_roots()]] - `calls` [EXTRACTED]
- [[_f1_score()]] - `calls` [EXTRACTED]
- [[_hard_validity()]] - `calls` [EXTRACTED]
- [[_jaccard()]] - `calls` [EXTRACTED]
- [[_normalize_anchor_set()]] - `calls` [EXTRACTED]
- [[_orphan_count()]] - `calls` [EXTRACTED]
- [[_route_cells_from_plan()]] - `calls` [EXTRACTED]
- [[_route_island_count()]] - `calls` [EXTRACTED]
- [[_routed_throughput_per_min()]] - `calls` [EXTRACTED]
- [[compute_golden_l4_capacity_metrics()]] - `calls` [INFERRED]
- [[format_l4_capacity_diagnostics()]] - `calls` [INFERRED]
- [[format_l5_failure_eval_diagnostics()]] - `calls` [INFERRED]
- [[golden_fixture_eval.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/evaluate_against_golden