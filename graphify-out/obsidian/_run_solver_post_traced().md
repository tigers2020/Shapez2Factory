---
source_file: "django_apps/web/views/public_pages.py"
type: "code"
community: "_run_solver_post_traced()"
location: "L410"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/_run_solver_post_traced
---

# _run_solver_post_traced()

## Connections
- [[Any]] - `references` [EXTRACTED]
- [[AsteroidProject_1]] - `references` [EXTRACTED]
- [[HttpRequest]] - `references` [EXTRACTED]
- [[JsonResponse]] - `calls` [EXTRACTED]
- [[_solver_async_enabled()]] - `calls` [EXTRACTED]
- [[asteroid_miner_layout_project_run_solver()]] - `calls` [EXTRACTED]
- [[build_asteroid_game_data_snapshot_with_provenance()]] - `calls` [INFERRED]
- [[build_game_data_snapshot_payload()]] - `calls` [INFERRED]
- [[cli_invoke_trace()]] - `calls` [INFERRED]
- [[enqueue_solver_run_for_project()]] - `calls` [INFERRED]
- [[entry_result_to_json_dict()]] - `calls` [INFERRED]
- [[perf_span()]] - `calls` [INFERRED]
- [[provenance_stub_diagnostic_dict()]] - `calls` [INFERRED]
- [[public_pages.py]] - `contains` [EXTRACTED]
- [[record_perf_meta()]] - `calls` [INFERRED]
- [[run_solver_runtime_for_project()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/_run_solver_post_traced