---
source_file: "django_apps/web/views/public_pages.py"
type: "code"
community: "_run_solver_post_traced()"
location: "L349"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/_run_solver_post_traced
---

# asteroid_miner_layout_project_run_solver()

## Connections
- [[HttpRequest]] - `references` [EXTRACTED]
- [[JsonResponse]] - `calls` [EXTRACTED]
- [[POST run solver runtime pipeline for one project; JSON response (PR8 entry).]] - `rationale_for` [EXTRACTED]
- [[_run_solver_post_traced()]] - `calls` [EXTRACTED]
- [[_run_solver_request_config()]] - `calls` [EXTRACTED]
- [[lab_perf_trace_request()]] - `calls` [INFERRED]
- [[public_pages.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/_run_solver_post_traced