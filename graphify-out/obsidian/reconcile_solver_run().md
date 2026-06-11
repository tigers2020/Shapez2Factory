---
source_file: "django_apps/asteroid_lab/services/solver_run_reconcile.py"
type: "code"
community: "SolverRun"
location: "L173"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/SolverRun
---

# reconcile_solver_run()

## Connections
- [[Single reconcile entry for status GET and ``run_solver_reap`` (artifact-first).]] - `rationale_for` [EXTRACTED]
- [[SolverRunReconcileResult]] - `references` [EXTRACTED]
- [[_artifact_dir_for_run()]] - `calls` [EXTRACTED]
- [[_attempt_artifact_ingest()]] - `calls` [EXTRACTED]
- [[_log_has_fatal_marker()]] - `calls` [EXTRACTED]
- [[_mark_run_failed_locked()]] - `calls` [EXTRACTED]
- [[_max_runtime_seconds()]] - `calls` [EXTRACTED]
- [[_result_from_run()]] - `calls` [EXTRACTED]
- [[_sidecar_path_for_run()]] - `calls` [EXTRACTED]
- [[asteroid_miner_layout_project_solver_run_status()]] - `calls` [INFERRED]
- [[is_terminal_solver_run()]] - `calls` [INFERRED]
- [[read_verified_artifact_manifest()]] - `calls` [INFERRED]
- [[reconcile_running_solver_runs()]] - `calls` [EXTRACTED]
- [[solver_run_reconcile.py]] - `contains` [EXTRACTED]
- [[tail_log_text()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/SolverRun