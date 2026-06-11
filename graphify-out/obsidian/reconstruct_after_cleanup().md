---
source_file: "src/shapez2_factory/domain/asteroid_lab/reconstruction/pipeline.py"
type: "code"
community: "reconstruct_after_cleanup()"
location: "L150"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/reconstruct_after_cleanup
---

# reconstruct_after_cleanup()

## Connections
- [[BoundaryTraceSink]] - `references` [EXTRACTED]
- [[CleanupResult]] - `calls` [EXTRACTED]
- [[Coord]] - `references` [EXTRACTED]
- [[DecodedCellDTO]] - `references` [EXTRACTED]
- [[Flood-fill and fill enclosed holes using precomputed walls and bbox (no snapshot]] - `rationale_for` [EXTRACTED]
- [[ReconstructionResult]] - `references` [EXTRACTED]
- [[ReconstructionTraceCollector]] - `references` [EXTRACTED]
- [[_emit_reconstruction_stamp_boundary()]] - `calls` [EXTRACTED]
- [[_fill_seam_column_gap_coords()]] - `calls` [EXTRACTED]
- [[_finalize_reconstruction_result()]] - `calls` [EXTRACTED]
- [[_sorted_interior_components()]] - `calls` [EXTRACTED]
- [[_wall_neighbor_count()]] - `calls` [INFERRED]
- [[close_diagonal_leaks()]] - `calls` [INFERRED]
- [[dense_gap_column_coords()]] - `calls` [INFERRED]
- [[diagonal_barrier_fill_coords()]] - `calls` [INFERRED]
- [[entries_have_explicit_raw_x_zero()]] - `calls` [INFERRED]
- [[external_pocket_cells_to_fill()]] - `calls` [INFERRED]
- [[external_pocket_components()]] - `calls` [INFERRED]
- [[external_reachable()]] - `calls` [INFERRED]
- [[is_asteroid_evidence()]] - `calls` [INFERRED]
- [[is_transport_tile()]] - `calls` [INFERRED]
- [[iter_bbox_cells()]] - `calls` [INFERRED]
- [[passes_bbox_interior()]] - `calls` [INFERRED]
- [[pipeline.py_3]] - `contains` [EXTRACTED]
- [[reconstruct_snapshot()]] - `calls` [EXTRACTED]
- [[replace_extensions_with_synthetic_fields()]] - `calls` [INFERRED]
- [[replace_miners_with_synthetic_fields()]] - `calls` [INFERRED]
- [[run_topology_reconstruction()]] - `calls` [EXTRACTED]
- [[seam_column_bridge_gap_fill_coords()]] - `calls` [INFERRED]
- [[seam_column_span_gap_fill_coords()]] - `calls` [INFERRED]
- [[stamp_islands_uniform()]] - `calls` [INFERRED]
- [[synthetic_field_cell()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/reconstruct_after_cleanup