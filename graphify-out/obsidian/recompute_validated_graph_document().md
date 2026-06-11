---
source_file: "django_apps/shapez_solver/services/recipe_graph_recompute.py"
type: "code"
community: "recipe_graph_recompute.py"
location: "L750"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/recipe_graph_recomputepy
---

# recompute_validated_graph_document()

## Connections
- [[Any]] - `references` [EXTRACTED]
- [[_apply_delivery_edges()]] - `calls` [EXTRACTED]
- [[_edge_adjacency()]] - `calls` [EXTRACTED]
- [[_operation_dependency_edges()]] - `calls` [EXTRACTED]
- [[_recompute_one_operation_in_topo()]] - `calls` [EXTRACTED]
- [[_topological_operation_order()]] - `calls` [EXTRACTED]
- [[``validate_graph_document`` 를 통과한 문서에 대해 재계산만 수행한다(추가 deepcopy 없음).      ``wor]] - `rationale_for` [EXTRACTED]
- [[index_recipe_graph_nodes_by_id()]] - `calls` [INFERRED]
- [[recipe_graph_recompute.py]] - `contains` [EXTRACTED]
- [[recompute_graph_document()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/recipe_graph_recomputepy