---
source_file: "django_apps/shapez_solver/services/recipe_graph_input_carrier.py"
type: "code"
community: "OperationType"
location: "L234"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/OperationType
---

# assert_input_output_carriers_for_document()

## Connections
- [[Any]] - `references` [EXTRACTED]
- [[Raise ``ValueError`` if any inputoutput edge violates materialfluid rules.]] - `rationale_for` [EXTRACTED]
- [[_group_input_and_output_edges()]] - `calls` [EXTRACTED]
- [[_index_nodes_by_id()]] - `calls` [EXTRACTED]
- [[_validate_operation_inputs()]] - `calls` [EXTRACTED]
- [[_validate_output_edge_carriers()]] - `calls` [EXTRACTED]
- [[recipe_graph_input_carrier.py]] - `contains` [EXTRACTED]
- [[validate_graph_document()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/OperationType