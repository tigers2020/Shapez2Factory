---
source_file: "django_apps/shapez_solver/services/recipe_graph_recompute.py"
type: "code"
community: "recipe_graph_recompute.py"
location: "L187"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/recipe_graph_recomputepy
---

# validate_graph_document()

## Connections
- [[Any]] - `references` [EXTRACTED]
- [[_assert_edges_reference_known_nodes()]] - `calls` [EXTRACTED]
- [[_validate_graph_edge_row()]] - `calls` [EXTRACTED]
- [[_validate_graph_node()]] - `calls` [EXTRACTED]
- [[_validated_graph_document_for_pattern_macro()]] - `calls` [EXTRACTED]
- [[assert_delivery_targets_unique()]] - `calls` [INFERRED]
- [[assert_input_output_carriers_for_document()]] - `calls` [INFERRED]
- [[assert_recipe_graph_edge_topology()]] - `calls` [INFERRED]
- [[default_empty_graph_document()]] - `calls` [EXTRACTED]
- [[document_to_solver_graph()]] - `calls` [INFERRED]
- [[graph_document JSON 검증. 통과 시 정규화된 dict 반환.]] - `rationale_for` [EXTRACTED]
- [[recipe_graph_recompute.py]] - `contains` [EXTRACTED]
- [[recompute_graph_document()]] - `calls` [EXTRACTED]
- [[serialize_macro_recipe_visual()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/recipe_graph_recomputepy