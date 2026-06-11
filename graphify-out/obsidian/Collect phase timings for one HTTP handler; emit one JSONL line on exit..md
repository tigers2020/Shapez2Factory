---
source_file: "django_apps/asteroid_lab/observability/lab_perf_trace.py"
type: "rationale"
community: "lab_page_context()"
location: "L88"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/lab_page_context
---

# Collect phase timings for one HTTP handler; emit one JSONL line on exit.

## Connections
- [[lab_perf_trace_request()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/lab_page_context