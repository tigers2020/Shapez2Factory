---
source_file: "src/shapez2_factory/domain/asteroid_lab/reconstruction/pipeline.py"
type: "code"
community: "reconstruct_after_cleanup()"
location: "L710"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/reconstruct_after_cleanup
---

# reconstruct_snapshot()

## Connections
- [[BoundaryTraceSink]] - `references` [EXTRACTED]
- [[Decode snapshot → cleanup → topology reconstruction (convenience wrapper).]] - `rationale_for` [EXTRACTED]
- [[DecodedBlueprintSnapshotDTO]] - `references` [EXTRACTED]
- [[ReconstructionResult]] - `references` [EXTRACTED]
- [[deconstruct_snapshot()]] - `calls` [INFERRED]
- [[pipeline.py_3]] - `contains` [EXTRACTED]
- [[reconstruct_after_cleanup()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/reconstruct_after_cleanup