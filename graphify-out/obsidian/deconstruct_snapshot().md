---
source_file: "src/shapez2_factory/domain/asteroid_lab/cleanup/pipeline.py"
type: "code"
community: "deconstruct_snapshot()"
location: "L20"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/deconstruct_snapshot
---

# deconstruct_snapshot()

## Connections
- [[.run()_1]] - `calls` [INFERRED]
- [[BoundaryTraceSink]] - `references` [EXTRACTED]
- [[CleanupResult]] - `calls` [EXTRACTED]
- [[DecodedBlueprintSnapshotDTO]] - `references` [EXTRACTED]
- [[Remove strippable buildings and compute ``wall_coords`` for reconstruction.]] - `rationale_for` [EXTRACTED]
- [[is_asteroid_evidence()]] - `calls` [INFERRED]
- [[is_strippable_building()]] - `calls` [INFERRED]
- [[is_transport_tile()]] - `calls` [INFERRED]
- [[load_cleanup_result()]] - `calls` [INFERRED]
- [[padded_bbox_bounds()]] - `calls` [INFERRED]
- [[pipeline.py_2]] - `contains` [EXTRACTED]
- [[reconstruct_snapshot()]] - `calls` [INFERRED]
- [[run_golden_solver()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/deconstruct_snapshot