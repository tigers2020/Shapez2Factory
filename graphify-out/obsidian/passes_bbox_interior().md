---
source_file: "src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py"
type: "code"
community: "reconstruct_after_cleanup()"
location: "L19"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/reconstruct_after_cleanup
---

# passes_bbox_interior()

## Connections
- [[Coord]] - `references` [EXTRACTED]
- [[Drop components touching the working bbox border (open to exterior padding).]] - `rationale_for` [EXTRACTED]
- [[diagonal_barrier_fill_coords()]] - `calls` [EXTRACTED]
- [[external_pocket_components()]] - `calls` [EXTRACTED]
- [[fill.py_1]] - `contains` [EXTRACTED]
- [[reconstruct_after_cleanup()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/reconstruct_after_cleanup