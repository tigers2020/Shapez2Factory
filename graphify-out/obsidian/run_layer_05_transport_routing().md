---
source_file: "src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/run.py"
type: "code"
community: "route_layer04_sequential()"
location: "L38"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/route_layer04_sequential
---

# run_layer_05_transport_routing()

## Connections
- [[ExteriorConnectionPlan]] - `references` [EXTRACTED]
- [[IntegratedRimGreedyResult]] - `references` [EXTRACTED]
- [[Layer04InnerFillResult]] - `references` [EXTRACTED]
- [[Layer04RoutePlan]] - `calls` [EXTRACTED]
- [[LayerBudgetContext]] - `references` [EXTRACTED]
- [[MVP routing when map + rim + exterior plan are present (canonical L5 slug).]] - `rationale_for` [EXTRACTED]
- [[ReconstructionCompleteMap]] - `references` [EXTRACTED]
- [[ResourceKind_1]] - `references` [EXTRACTED]
- [[SpaceTransportTileCatalog]] - `references` [EXTRACTED]
- [[build_solver_runtime_replay_frames_from_artifact_run()]] - `calls` [INFERRED]
- [[route_layer04_sequential()]] - `calls` [INFERRED]
- [[run.py_10]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/route_layer04_sequential