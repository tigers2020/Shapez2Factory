---
source_file: "src/shapez2_factory/domain/asteroid_lab/reconstruction/perimeter_closing.py"
type: "code"
community: "close_diagonal_leaks()"
location: "L14"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/close_diagonal_leaks
---

# close_diagonal_leaks()

## Connections
- [[Chebyshev 1-step perimeter close (flood barrier only; not interior holes).]] - `rationale_for` [EXTRACTED]
- [[Coord]] - `references` [EXTRACTED]
- [[_strict_bbox_interior_cells()]] - `calls` [INFERRED]
- [[_touches_bbox_edge()]] - `calls` [EXTRACTED]
- [[iter_bbox_cells()]] - `calls` [INFERRED]
- [[perimeter_closing.py_1]] - `contains` [EXTRACTED]
- [[reconstruct_after_cleanup()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/close_diagonal_leaks