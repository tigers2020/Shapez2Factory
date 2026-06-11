---
source_file: "django_apps/asteroid_lab/services/solver_subprocess_runner.py"
type: "rationale"
community: "run_solver_subprocess()"
location: "L73"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/run_solver_subprocess
---

# Validate ``run_key`` and ensure final artifact path stays under allowed root.

## Connections
- [[resolve_subprocess_artifact_dir()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/run_solver_subprocess