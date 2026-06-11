---
source_file: "django_apps/shapez_solver/ports/graph_preview.py"
type: "rationale"
community: "GraphPreviewRenderer"
location: "L36"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/GraphPreviewRenderer
---

# No server-side PNG; for tests and hosts without Playwright. Not settings-coupled

## Connections
- [[NoopGraphPreviewRenderer]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/GraphPreviewRenderer