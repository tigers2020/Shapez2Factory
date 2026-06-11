---
source_file: "django_apps/asteroid_lab/services/solver_subprocess_runner.py"
type: "rationale"
community: "run_solver_subprocess()"
location: "L119"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/run_solver_subprocess
---

# Build the exact ``sys.executable -m ...`` invocation.

## Connections
- [[build_solver_cli_args()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/run_solver_subprocess