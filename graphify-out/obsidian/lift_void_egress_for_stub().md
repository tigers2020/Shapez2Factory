---
source_file: "src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/space_lift_routing.py"
type: "code"
community: "ReconstructionCompleteMap"
location: "L57"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/ReconstructionCompleteMap
---

# lift_void_egress_for_stub()

## Connections
- [[Coord]] - `references` [EXTRACTED]
- [[Pick void cell on z=1 network for lift egress nearest to ``stub``.]] - `rationale_for` [EXTRACTED]
- [[ReconstructionCompleteMap]] - `references` [EXTRACTED]
- [[_stub_has_lift_egress()]] - `calls` [INFERRED]
- [[astar_inner_source_via_space_lift()]] - `calls` [EXTRACTED]
- [[connector_reachable_void_cells()]] - `calls` [EXTRACTED]
- [[space_lift_routing.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/ReconstructionCompleteMap