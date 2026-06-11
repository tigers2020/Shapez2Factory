---
source_file: "src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/run.py"
type: "code"
community: "execute_layer_02_exterior_transport_plan"
location: "L27"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/execute_layer_02_exterior_transport_plan
---

# execute_layer_02_exterior_transport_plan()

## Connections
- [[Any]] - `references` [EXTRACTED]
- [[ExteriorConnectionPlan]] - `references` [EXTRACTED]
- [[GameDataRulesPort]] - `references` [EXTRACTED]
- [[ReconstructionCompleteMap]] - `references` [EXTRACTED]
- [[Run Layer 02 planning (pure; no IO).]] - `rationale_for` [EXTRACTED]
- [[build_orm_game_data_rules()]] - `calls` [INFERRED]
- [[detect_present_resource_kinds()]] - `calls` [INFERRED]
- [[merge_exterior_connection_plans()]] - `calls` [INFERRED]
- [[run.py_1]] - `contains` [EXTRACTED]
- [[run.py_7]] - `contains` [EXTRACTED]
- [[run_layer_02_exterior_transport()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/execute_layer_02_exterior_transport_plan