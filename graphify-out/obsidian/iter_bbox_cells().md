---
source_file: "src/shapez2_factory/domain/asteroid_lab/reconstruction/grid.py"
type: "code"
community: "close_diagonal_leaks()"
location: "L32"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/close_diagonal_leaks
---

# iter_bbox_cells()

## Connections
- [[All integer coords in the inclusive bbox.      By default skips ``x == 0`` (le]] - `rationale_for` [EXTRACTED]
- [[Coord]] - `references` [EXTRACTED]
- [[close_diagonal_leaks()]] - `calls` [INFERRED]
- [[grid.py_1]] - `contains` [EXTRACTED]
- [[reconstruct_after_cleanup()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/close_diagonal_leaks