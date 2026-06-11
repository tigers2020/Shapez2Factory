---
type: community
cohesion: 0.14
members: 17
---

# close_diagonal_leaks()

**Cohesion:** 0.14 - loosely connected
**Members:** 17 nodes

## Members
- [[All integer coords in the inclusive bbox.      By default skips ``x == 0`` (le]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/grid.py
- [[Cells strictly inside the axis-aligned bbox of ``walls`` (excl. ``x == 0``).]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/shell.py
- [[Chebyshev 1-step perimeter close (flood barrier only; not interior holes).]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/perimeter_closing.py
- [[Inferred shell closure from evidence walls (reconstruction-only flood barrier).]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/shell.py
- [[Perimeter morphology before external flood (diagonal closing + orthogonal slit s]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/perimeter_closing.py
- [[Rowcolumn min–max span closure; returns inferred cells only (not in ``wall_coor]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/shell.py
- [[Seal width-1 orthogonal voids opposed by ``slit_solid`` (fixed-point; bbox edge]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/perimeter_closing.py
- [[_strict_bbox_interior_cells()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/shell.py
- [[_touches_bbox_edge()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/perimeter_closing.py
- [[close_diagonal_leaks()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/perimeter_closing.py
- [[close_orthogonal_one_cell_slits()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/perimeter_closing.py
- [[infer_shell_barrier_coords()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/shell.py
- [[iter_bbox_cells()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/grid.py
- [[perimeter_closing.py]] - code - django_apps/asteroid_lab/reconstruction/perimeter_closing.py
- [[perimeter_closing.py_1]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/perimeter_closing.py
- [[shell.py]] - code - django_apps/asteroid_lab/reconstruction/shell.py
- [[shell.py_1]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/shell.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/close_diagonal_leaks
SORT file.name ASC
```

## Connections to other communities
- 6 edges to [[_COMMUNITY_Coord]]
- 3 edges to [[_COMMUNITY_reconstruct_after_cleanup()]]
- 1 edge to [[_COMMUNITY_deconstruct_snapshot()]]

## Top bridge nodes
- [[iter_bbox_cells()]] - degree 5, connects to 3 communities
- [[close_diagonal_leaks()]] - degree 7, connects to 2 communities
- [[infer_shell_barrier_coords()]] - degree 5, connects to 2 communities
- [[_strict_bbox_interior_cells()]] - degree 5, connects to 1 community
- [[_touches_bbox_edge()]] - degree 4, connects to 1 community