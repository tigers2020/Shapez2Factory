---
source_file: "src/shapez2_factory/domain/asteroid_lab/reconstruction/shell.py"
type: "code"
community: "close_diagonal_leaks()"
location: "L14"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/close_diagonal_leaks
---

# _strict_bbox_interior_cells()

## Connections
- [[Cells strictly inside the axis-aligned bbox of ``walls`` (excl. ``x == 0``).]] - `rationale_for` [EXTRACTED]
- [[Coord]] - `references` [EXTRACTED]
- [[close_diagonal_leaks()]] - `calls` [INFERRED]
- [[infer_shell_barrier_coords()]] - `calls` [EXTRACTED]
- [[shell.py_1]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/close_diagonal_leaks