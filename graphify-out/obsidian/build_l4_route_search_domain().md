---
source_file: "src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/route_domain.py"
type: "code"
community: "bbox_from_coords()"
location: "L55"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/bbox_from_coords
---

# build_l4_route_search_domain()

## Connections
- [[Coord]] - `references` [EXTRACTED]
- [[L4RouteSearchDomain_1]] - `calls` [EXTRACTED]
- [[ReconstructionCompleteMap]] - `references` [EXTRACTED]
- [[bbox_from_coords()]] - `calls` [INFERRED]
- [[route_domain.py]] - `contains` [EXTRACTED]
- [[route_layer04_sequential()]] - `calls` [INFERRED]
- [[terrain_kind_at()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/bbox_from_coords