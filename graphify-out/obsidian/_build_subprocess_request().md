---
source_file: "django_apps/asteroid_lab/services/solver_runtime_entry.py"
type: "code"
community: "entry_result_to_json_dict()"
location: "L134"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/entry_result_to_json_dict
---

# _build_subprocess_request()

## Connections
- [[Any]] - `references` [EXTRACTED]
- [[AsteroidMapInput]] - `references` [EXTRACTED]
- [[Path]] - `references` [EXTRACTED]
- [[SolverSubprocessRequest]] - `calls` [EXTRACTED]
- [[_run_subprocess_runtime_for_project()]] - `calls` [EXTRACTED]
- [[build_genetic_sample_seed_snapshot()]] - `calls` [INFERRED]
- [[enqueue_solver_run_for_project()]] - `calls` [EXTRACTED]
- [[solver_runtime_entry.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/entry_result_to_json_dict