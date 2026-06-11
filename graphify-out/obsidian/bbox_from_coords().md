---
source_file: "src/shapez2_factory/domain/asteroid_lab/grid_contract.py"
type: "code"
community: "bbox_from_coords()"
location: "L26"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/bbox_from_coords
---

# bbox_from_coords()

## Connections
- [[BBox_1]] - `calls` [EXTRACTED]
- [[Coord]] - `references` [EXTRACTED]
- [[Inclusive bbox over ``coords``; empty becomes ``BBox(0, 0, 0, 0)``.]] - `rationale_for` [EXTRACTED]
- [[acceptance_topology_from_decoded_cells()]] - `calls` [INFERRED]
- [[build_commit_reprobe_context()]] - `calls` [INFERRED]
- [[build_l4_route_search_domain()]] - `calls` [INFERRED]
- [[build_normalized_reconstruction_topology()]] - `calls` [INFERRED]
- [[build_void_shell_route_domain()]] - `calls` [INFERRED]
- [[generate_candidates()]] - `calls` [INFERRED]
- [[grid_contract.py]] - `contains` [EXTRACTED]
- [[immediate_route_probe()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/bbox_from_coords