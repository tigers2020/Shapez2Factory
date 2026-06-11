---
source_file: "src/shapez2_factory/domain/asteroid_lab/reconstruction/pipeline.py"
type: "code"
community: "record_existing_layout_inspection_frames"
location: "L685"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/record_existing_layout_inspection_frames
---

# run_topology_reconstruction()

## Connections
- [[.run()_1]] - `calls` [INFERRED]
- [[BoundaryTraceSink]] - `references` [EXTRACTED]
- [[CleanupResult]] - `references` [EXTRACTED]
- [[Fill enclosed holes from ``CleanupResult`` walls and bbox.]] - `rationale_for` [EXTRACTED]
- [[ReconstructionResult]] - `references` [EXTRACTED]
- [[ReconstructionTraceCollector]] - `references` [EXTRACTED]
- [[build_cleanup_and_reconstruction_rows()]] - `calls` [INFERRED]
- [[pipeline.py_3]] - `contains` [EXTRACTED]
- [[reconstruct_after_cleanup()]] - `calls` [EXTRACTED]
- [[run_golden_solver()]] - `calls` [INFERRED]
- [[run_reconstruction_for_map_input()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/record_existing_layout_inspection_frames