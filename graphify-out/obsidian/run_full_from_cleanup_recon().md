---
source_file: "django_apps/asteroid_lab/layers/stack_runner.py"
type: "code"
community: "run_full_from_cleanup_recon()"
location: "L108"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/run_full_from_cleanup_recon
---

# run_full_from_cleanup_recon()

## Connections
- [[CleanupResult]] - `references` [EXTRACTED]
- [[Layer01ReconstructionOutput]] - `references` [EXTRACTED]
- [[LayerBudgetContext]] - `references` [EXTRACTED]
- [[LayerPostSummaryLogSession]] - `references` [EXTRACTED]
- [[ReconstructionResult]] - `references` [EXTRACTED]
- [[StackRunResult]] - `references` [EXTRACTED]
- [[_LayerStackRunner]] - `references` [EXTRACTED]
- [[build_layer01_post_summary_metrics()]] - `calls` [INFERRED]
- [[create_layer_post_summary_log_session()]] - `calls` [INFERRED]
- [[emit_layer_post_summary()]] - `calls` [INFERRED]
- [[run_layer_01()]] - `calls` [INFERRED]
- [[run_layers_02_to_06()]] - `calls` [EXTRACTED]
- [[stack_runner.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/run_full_from_cleanup_recon