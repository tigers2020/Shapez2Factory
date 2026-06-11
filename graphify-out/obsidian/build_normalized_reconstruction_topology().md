---
source_file: "src/shapez2_factory/domain/asteroid_lab/reconstruction/topology_contract.py"
type: "code"
community: "build_normalized_reconstruction_topology"
location: "L76"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/build_normalized_reconstruction_topology
---

# build_normalized_reconstruction_topology()

## Connections
- [[Build compare topology from decoded or reconstruction-merged cells.]] - `rationale_for` [EXTRACTED]
- [[CoordFrame]] - `references` [EXTRACTED]
- [[DecodedCellDTO]] - `references` [EXTRACTED]
- [[NormalizedReconstructionTopology]] - `calls` [EXTRACTED]
- [[RawCoord]] - `references` [EXTRACTED]
- [[_finalize_reconstruction_result()]] - `calls` [INFERRED]
- [[_is_mineable_occupied()]] - `calls` [EXTRACTED]
- [[_shell_topology_coords()]] - `calls` [EXTRACTED]
- [[bbox_from_coords()]] - `calls` [INFERRED]
- [[infer_topology_coord_frame()]] - `calls` [INFERRED]
- [[is_asteroid_evidence()]] - `calls` [INFERRED]
- [[topology_contract.py_1]] - `contains` [EXTRACTED]
- [[topology_coord_for_cell()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/build_normalized_reconstruction_topology