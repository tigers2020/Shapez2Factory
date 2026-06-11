---
source_file: "django_apps/asteroid_lab/services/experiment_service.py"
type: "code"
community: "create_solver_run()"
location: "L22"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/create_solver_run
---

# create_solver_run()

## Connections
- [[Any]] - `references` [EXTRACTED]
- [[Insert one ``SolverRun`` plus default ``ReplayTrack`` scaffolding.      Does]] - `rationale_for` [EXTRACTED]
- [[SolverRunDTO]] - `references` [EXTRACTED]
- [[_solver_run_dto()]] - `calls` [EXTRACTED]
- [[create_or_replace_solver_run()]] - `calls` [EXTRACTED]
- [[empty_solver_run_fast_cache_kwargs()]] - `calls` [INFERRED]
- [[ensure_default_replay_track()]] - `calls` [EXTRACTED]
- [[experiment_service.py]] - `contains` [EXTRACTED]
- [[resolve_inspection_solver_run()]] - `calls` [EXTRACTED]
- [[sync_solver_run_fast_cache_from_config_json()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/create_solver_run