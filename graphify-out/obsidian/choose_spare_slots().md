---
source_file: "src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/placement.py"
type: "code"
community: "placement.py"
location: "L101"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/placementpy
---

# choose_spare_slots()

## Connections
- [[Coord]] - `references` [EXTRACTED]
- [[InsufficientConnectorSlotsError]] - `calls` [EXTRACTED]
- [[Pick spare connectors as far from required slots as the edge allows.]] - `rationale_for` [EXTRACTED]
- [[_min_index_distance()]] - `calls` [EXTRACTED]
- [[_place_connectors_for_role()]] - `calls` [INFERRED]
- [[_spare_candidate_rank()]] - `calls` [EXTRACTED]
- [[choose_even_slots()]] - `calls` [EXTRACTED]
- [[placement.py_1]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/placementpy