---
source_file: "src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map_merge.py"
type: "code"
community: "DecodedCellDTO"
location: "L97"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/DecodedCellDTO
---

# merged_display_cells_from_reconstruction()

## Connections
- [[CleanupResult]] - `references` [EXTRACTED]
- [[DecodedCellDTO]] - `references` [EXTRACTED]
- [[Full topology cell set for persist (no replay frame reads).]] - `rationale_for` [EXTRACTED]
- [[ReconstructionResult]] - `references` [EXTRACTED]
- [[build_reconstructed_map_persist_payload()]] - `calls` [INFERRED]
- [[build_reconstruction_complete_map()]] - `calls` [INFERRED]
- [[complete_map_merge.py]] - `contains` [EXTRACTED]
- [[full_map_rows_from_reconstruction()]] - `calls` [INFERRED]
- [[merge_reconstruction_display_cells()]] - `calls` [EXTRACTED]
- [[structural_cells_from_cleanup()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/DecodedCellDTO