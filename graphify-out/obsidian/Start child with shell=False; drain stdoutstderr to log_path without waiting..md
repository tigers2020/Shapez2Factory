---
source_file: "django_apps/asteroid_lab/services/subprocess_stream_tee.py"
type: "rationale"
community: "run_solver_subprocess()"
location: "L115"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/run_solver_subprocess
---

# Start child with shell=False; drain stdout/stderr to log_path without waiting.

## Connections
- [[spawn_subprocess_with_log_tee()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/run_solver_subprocess