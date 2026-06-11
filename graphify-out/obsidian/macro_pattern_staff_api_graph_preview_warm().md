---
source_file: "django_apps/web/views/staff_shared.py"
type: "code"
community: "_run_solver_post_traced()"
location: "L50"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/_run_solver_post_traced
---

# macro_pattern_staff_api_graph_preview_warm()

## Connections
- [[HttpRequest]] - `references` [EXTRACTED]
- [[JsonResponse]] - `calls` [EXTRACTED]
- [[PlaywrightPngGraphPreviewRenderer]] - `calls` [INFERRED]
- [[Warm one graph-preview PNG (staff-only; validates cache_key against preview_scen]] - `rationale_for` [EXTRACTED]
- [[_parse_graph_preview_warm_body()]] - `calls` [EXTRACTED]
- [[staff_shared.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/_run_solver_post_traced