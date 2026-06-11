---
source_file: "src/shapez2_factory/domain/asteroid_lab/reconstruction/pipeline.py"
type: "code"
community: "reconstruct_after_cleanup()"
location: "L62"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/reconstruct_after_cleanup
---

# _finalize_reconstruction_result()

## Connections
- [[CleanupResult]] - `references` [EXTRACTED]
- [[Coord]] - `references` [EXTRACTED]
- [[DecodedCellDTO]] - `references` [EXTRACTED]
- [[ReconstructionResult]] - `calls` [EXTRACTED]
- [[apply_confidence_to_result()]] - `calls` [INFERRED]
- [[build_normalized_reconstruction_topology()]] - `calls` [INFERRED]
- [[pipeline.py_3]] - `contains` [EXTRACTED]
- [[reconstruct_after_cleanup()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/reconstruct_after_cleanup