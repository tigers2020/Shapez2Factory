---
source_file: "django_apps/asteroid_lab/services/solver_run_reconcile.py"
type: "code"
community: "SolverRun"
location: "L125"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/SolverRun
---

# _result_from_run()

## Connections
- [[SolverRun_1]] - `references` [EXTRACTED]
- [[SolverRunReconcileResult]] - `calls` [EXTRACTED]
- [[_spawn_config()]] - `calls` [EXTRACTED]
- [[is_terminal_solver_run()]] - `calls` [INFERRED]
- [[lab_run_summary_from_orm()]] - `calls` [INFERRED]
- [[reconcile_solver_run()]] - `calls` [EXTRACTED]
- [[solver_run_reconcile.py]] - `contains` [EXTRACTED]
- [[validation_passed_from_solver_summary()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/SolverRun