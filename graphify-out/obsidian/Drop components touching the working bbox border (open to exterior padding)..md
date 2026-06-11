---
source_file: "src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py"
type: "rationale"
community: "reconstruct_after_cleanup()"
location: "L20"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/reconstruct_after_cleanup
---

# Drop components touching the working bbox border (open to exterior padding).

## Connections
- [[passes_bbox_interior()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/reconstruct_after_cleanup