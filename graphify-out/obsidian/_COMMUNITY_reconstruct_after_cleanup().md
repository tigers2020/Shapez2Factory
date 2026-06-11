---
type: community
cohesion: 0.07
members: 45
---

# reconstruct_after_cleanup()

**Cohesion:** 0.07 - loosely connected
**Members:** 45 nodes

## Members
- [[1-cell-wide external run (vertical seam  hole-island slit) → preserve as void.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[4-connected components.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[BoundaryTraceSink]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/pipeline.py
- [[Cells in ``walkable`` reachable from the bbox border via 4-neighbor moves within]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/flood_fill.py
- [[Decode snapshot → cleanup → topology reconstruction (convenience wrapper).]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/pipeline.py
- [[Drop components touching the working bbox border (open to exterior padding).]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[External void flood fill from padded bbox border (walkable cells only).]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/flood_fill.py
- [[Fill pinhole closes when both dense neighbors are evidence walls (not recursive]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[Fill raw ``x == 0`` gaps between extension-shell rows on the explicit seam colum]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[Fill raw ``x == 0`` holes between two occupied seam cells (e.g. ``y=5`` and ``y=]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[Fill raw ``x == 0`` only when evidence walls seal both dense neighbors (not fill]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[Flood-fill and fill enclosed holes using precomputed walls and bbox (no snapshot]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/pipeline.py
- [[Interior component detection, enclosure guards, and topology placeholder fill.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[Pockets in ``external`` fillable without reusing morphology as barriers.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[ReconstructionTraceCollector]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/shell.py
- [[Replay-only filled hole cell (placeholder ``cell_kind`` until island stamp).]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[Require evidence-wall touch on both x- and y-offset directions (4-neighbor).]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[Subset of a pocket component safe to synthetic-fill (limits exterior seam overcl]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[Topology fill after cleanup (pure; not solver input).]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/pipeline.py
- [[_component_touches_walls()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[_emit_reconstruction_stamp_boundary()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/pipeline.py
- [[_fill_seam_column_gap_coords()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/pipeline.py
- [[_finalize_reconstruction_result()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/pipeline.py
- [[_is_narrow_external_channel()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[_sorted_interior_components()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/pipeline.py
- [[_wall_neighbor_count()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[connected_components()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[dense_gap_column_coords()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[diagonal_barrier_fill_coords()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[external_pocket_cells_to_fill()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[external_pocket_components()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[external_reachable()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/flood_fill.py
- [[fill.py]] - code - django_apps/asteroid_lab/reconstruction/fill.py
- [[fill.py_1]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[flood_fill.py]] - code - django_apps/asteroid_lab/reconstruction/flood_fill.py
- [[flood_fill.py_1]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/flood_fill.py
- [[passes_bbox_interior()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[passes_two_axis_evidence_guard()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[pipeline.py_1]] - code - django_apps/asteroid_lab/reconstruction/pipeline.py
- [[pipeline.py_3]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/pipeline.py
- [[reconstruct_after_cleanup()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/pipeline.py
- [[reconstruct_snapshot()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/pipeline.py
- [[seam_column_bridge_gap_fill_coords()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[seam_column_span_gap_fill_coords()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py
- [[synthetic_field_cell()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/fill.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/reconstruct_after_cleanup
SORT file.name ASC
```

## Connections to other communities
- 17 edges to [[_COMMUNITY_Coord]]
- 8 edges to [[_COMMUNITY_DecodedCellDTO]]
- 8 edges to [[_COMMUNITY_record_existing_layout_inspection_frames]]
- 4 edges to [[_COMMUNITY_ReconstructionResult]]
- 3 edges to [[_COMMUNITY_close_diagonal_leaks()]]
- 3 edges to [[_COMMUNITY_stamp_islands_uniform()]]
- 2 edges to [[_COMMUNITY_deconstruct_snapshot()]]
- 1 edge to [[_COMMUNITY_entry_island_raw_coord()]]
- 1 edge to [[_COMMUNITY_build_decoded_blueprint_snapshot()]]
- 1 edge to [[_COMMUNITY_Protocol]]
- 1 edge to [[_COMMUNITY_is_asteroid_evidence()]]
- 1 edge to [[_COMMUNITY_build_normalized_reconstruction_topology]]

## Top bridge nodes
- [[reconstruct_after_cleanup()]] - degree 32, connects to 8 communities
- [[_finalize_reconstruction_result()]] - degree 8, connects to 5 communities
- [[reconstruct_snapshot()]] - degree 7, connects to 3 communities
- [[BoundaryTraceSink]] - degree 6, connects to 3 communities
- [[connected_components()]] - degree 7, connects to 2 communities