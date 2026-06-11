---
source_file: "django_apps/shapez_solver/services/recipe_graph_recompute.py"
type: "code"
community: "recipe_graph_recompute.py"
location: "L479"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/recipe_graph_recomputepy
---

# _apply_recomputed_operation()

## Connections
- [[(성공 여부, 출력 shape_code 튜플, 경고 메시지). 실패 시 튜플은 빈 값.]] - `rationale_for` [EXTRACTED]
- [[Any]] - `references` [EXTRACTED]
- [[OperationType_1]] - `references` [EXTRACTED]
- [[Shape]] - `references` [EXTRACTED]
- [[_recompute_one_operation_in_topo()]] - `calls` [EXTRACTED]
- [[_required_input_count_for_recompute()]] - `calls` [EXTRACTED]
- [[apply_operation()]] - `calls` [INFERRED]
- [[recipe_graph_recompute.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/recipe_graph_recomputepy