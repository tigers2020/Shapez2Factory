---
source_file: "django_apps/web/views/staff_shared.py"
type: "rationale"
community: "_run_solver_post_traced()"
location: "L19"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/_run_solver_post_traced
---

# Require login at ``settings.LOGIN_URL`` and ``is_staff`` (403 if logged-in but n

## Connections
- [[staff_site_required()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/_run_solver_post_traced