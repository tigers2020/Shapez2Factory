---
type: community
cohesion: 0.19
members: 23
---

# OperationType

**Cohesion:** 0.19 - loosely connected
**Members:** 23 nodes

## Members
- [[Aligns with ``_required_input_count_for_recompute`` in ``recipe_graph_recompute`]] - rationale - django_apps/shapez_solver/services/recipe_graph_input_carrier.py
- [[Carrier]] - code - django_apps/shapez_solver/services/recipe_graph_input_carrier.py
- [[Inputoutput wire carrier (material vs fluid) for recipe graph validation.]] - rationale - django_apps/shapez_solver/services/recipe_graph_input_carrier.py
- [[Map operation node id → incoming input edges (``kind`` == ``input``).]] - rationale - django_apps/shapez_solver/services/recipe_graph_input_carrier.py
- [[OperationType_1]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[Per logical input index after ``sorted_shape_input_edges_to_operation`` order.]] - rationale - django_apps/shapez_solver/services/recipe_graph_input_carrier.py
- [[Raise ``ValueError`` if any inputoutput edge violates materialfluid rules.]] - rationale - django_apps/shapez_solver/services/recipe_graph_input_carrier.py
- [[_apply_operation_output_lane_to_shape_node()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_expected_carrier_for_input_edge()]] - code - django_apps/shapez_solver/services/recipe_graph_input_carrier.py
- [[_fill_linked_shape_from_operation_output()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_group_input_and_output_edges()]] - code - django_apps/shapez_solver/services/recipe_graph_input_carrier.py
- [[_index_nodes_by_id()]] - code - django_apps/shapez_solver/services/recipe_graph_input_carrier.py
- [[_parse_output_lane()]] - code - django_apps/shapez_solver/services/recipe_graph_input_carrier.py
- [[_raise_if_input_carrier_wrong()]] - code - django_apps/shapez_solver/services/recipe_graph_input_carrier.py
- [[_raise_output_carrier_mismatch()]] - code - django_apps/shapez_solver/services/recipe_graph_input_carrier.py
- [[_validate_operation_inputs()]] - code - django_apps/shapez_solver/services/recipe_graph_input_carrier.py
- [[_validate_output_edge_carriers()]] - code - django_apps/shapez_solver/services/recipe_graph_input_carrier.py
- [[assert_input_output_carriers_for_document()]] - code - django_apps/shapez_solver/services/recipe_graph_input_carrier.py
- [[expected_input_carriers()]] - code - django_apps/shapez_solver/services/recipe_graph_input_carrier.py
- [[operation_output_lane_carrier()]] - code - django_apps/shapez_solver/services/recipe_graph_input_carrier.py
- [[recipe_graph_input_carrier.py]] - code - django_apps/shapez_solver/services/recipe_graph_input_carrier.py
- [[required_input_count()]] - code - django_apps/shapez_solver/services/recipe_graph_input_carrier.py
- [[shape_node_is_fluid()]] - code - django_apps/shapez_solver/services/recipe_graph_input_carrier.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/OperationType
SORT file.name ASC
```

## Connections to other communities
- 14 edges to [[_COMMUNITY_recipe_graph_recompute.py]]
- 12 edges to [[_COMMUNITY_Any]]
- 3 edges to [[_COMMUNITY_parse_shape()]]
- 2 edges to [[_COMMUNITY_Shape]]
- 1 edge to [[_COMMUNITY_pure_fluid_color()]]

## Top bridge nodes
- [[OperationType_1]] - degree 21, connects to 3 communities
- [[_validate_operation_inputs()]] - degree 8, connects to 2 communities
- [[assert_input_output_carriers_for_document()]] - degree 8, connects to 2 communities
- [[_apply_operation_output_lane_to_shape_node()]] - degree 6, connects to 2 communities
- [[shape_node_is_fluid()]] - degree 5, connects to 2 communities