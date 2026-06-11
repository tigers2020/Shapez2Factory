---
source_file: "django_apps/asteroid_lab/services/solver_run_lab_summary.py"
type: "code"
community: "Any"
location: "L101"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Any
---

# validation_passed_from_solver_summary()

## Connections
- [[Any]] - `references` [EXTRACTED]
- [[Resolve UI validation flag; CLI summaries may omit the key when stack succeeded.]] - `rationale_for` [EXTRACTED]
- [[_result_from_run()]] - `calls` [INFERRED]
- [[_run_subprocess_runtime_for_project()]] - `calls` [INFERRED]
- [[lab_run_summary_from_solver_summary()]] - `calls` [EXTRACTED]
- [[solver_run_lab_summary.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Any