---
source_file: "src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/space_lift_routing.py"
type: "code"
community: "ReconstructionCompleteMap"
location: "L128"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/ReconstructionCompleteMap
---

# astar_inner_source_via_space_lift()

## Connections
- [[AstarPathResult_1]] - `calls` [EXTRACTED]
- [[Coord]] - `references` [EXTRACTED]
- [[Layer04SourceView]] - `references` [EXTRACTED]
- [[ReconstructionCompleteMap]] - `references` [EXTRACTED]
- [[Route inner source lift from field stub to z=1 void, then void-only A.]] - `rationale_for` [EXTRACTED]
- [[RouteGoal_1]] - `references` [EXTRACTED]
- [[_prepend_lift_segment()]] - `calls` [EXTRACTED]
- [[astar_to_nearest_goal()]] - `calls` [INFERRED]
- [[build_void_shell_route_domain()]] - `calls` [EXTRACTED]
- [[is_inner_lift_source()]] - `calls` [EXTRACTED]
- [[lift_void_egress_for_stub()]] - `calls` [EXTRACTED]
- [[route_layer04_sequential()]] - `calls` [INFERRED]
- [[space_lift_routing.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/ReconstructionCompleteMap