---
source_file: "django_apps/shapez_solver/services/recipe_graph_recompute.py"
type: "code"
community: "recipe_graph_recompute.py"
location: "L291"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/recipe_graph_recomputepy
---

# defaultdict

## Connections
- [[_assign_operation_outputs()]] - `references` [EXTRACTED]
- [[_edge_adjacency()]] - `calls` [EXTRACTED]
- [[_group_by_anchor()]] - `calls` [INFERRED]
- [[_operation_dependency_edges()]] - `calls` [EXTRACTED]
- [[_recompute_one_operation_in_topo()]] - `references` [EXTRACTED]
- [[_sorted_output_edges_for_operation()]] - `references` [EXTRACTED]
- [[_topological_operation_order()]] - `calls` [EXTRACTED]
- [[build_children_by_parent()]] - `calls` [INFERRED]
- [[trace_outline_loops_from_segments()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/recipe_graph_recomputepy