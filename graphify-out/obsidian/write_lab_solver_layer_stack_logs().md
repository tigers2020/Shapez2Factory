---
source_file: "django_apps/asteroid_lab/services/solver_layer_stack_log.py"
type: "code"
community: "write_lab_solver_layer_stack_logs()"
location: "L54"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/write_lab_solver_layer_stack_logs
---

# write_lab_solver_layer_stack_logs()

## Connections
- [[ExteriorConnectionPlan]] - `references` [EXTRACTED]
- [[IntegratedRimGreedyResult]] - `references` [EXTRACTED]
- [[Layer01ReconstructionOutput]] - `references` [EXTRACTED]
- [[Layer04RimPlacementResult]] - `references` [EXTRACTED]
- [[Persist L1–L4 behavior + summary JSONL under var; return run log dir or None.]] - `rationale_for` [EXTRACTED]
- [[RimBundleCandidateSet]] - `references` [EXTRACTED]
- [[StackRunStatus]] - `references` [EXTRACTED]
- [[build_layer01_post_summary_metrics()]] - `calls` [INFERRED]
- [[build_layer02_post_summary_metrics()]] - `calls` [INFERRED]
- [[build_layer03_post_summary_metrics()]] - `calls` [INFERRED]
- [[build_layer03_rim_greedy_post_summary_metrics()]] - `calls` [INFERRED]
- [[build_layer04_post_summary_metrics()]] - `calls` [INFERRED]
- [[create_layer_post_summary_log_session()]] - `calls` [INFERRED]
- [[emit_layer_post_summary()]] - `calls` [INFERRED]
- [[solver_layer_stack_log.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/write_lab_solver_layer_stack_logs