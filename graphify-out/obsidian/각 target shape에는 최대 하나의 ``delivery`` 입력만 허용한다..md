---
source_file: "django_apps/shapez_solver/services/recipe_graph_topology.py"
type: "rationale"
community: "assert_recipe_graph_edge_topology()"
location: "L102"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/assert_recipe_graph_edge_topology
---

# 각 target shape에는 최대 하나의 ``delivery`` 입력만 허용한다.

## Connections
- [[assert_delivery_targets_unique()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/assert_recipe_graph_edge_topology