---
source_file: "src/shapez2_factory/domain/asteroid_lab/reconstruction/grid.py"
type: "rationale"
community: "close_diagonal_leaks()"
location: "L40"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/close_diagonal_leaks
---

# All integer coords in the inclusive bbox.      By default skips ``x == 0`` (le

## Connections
- [[iter_bbox_cells()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/close_diagonal_leaks