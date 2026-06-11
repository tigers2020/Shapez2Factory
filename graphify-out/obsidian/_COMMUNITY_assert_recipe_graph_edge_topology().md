---
type: community
cohesion: 0.24
members: 12
---

# assert_recipe_graph_edge_topology()

**Cohesion:** 0.24 - loosely connected
**Members:** 12 nodes

## Members
- [[Recipe graph 엣지 토폴로지 shape ↔ operation 및 intermediate→target(delivery) 규칙.]] - rationale - django_apps/shapez_solver/services/recipe_graph_topology.py
- [[_resolved_edge_nodes()]] - code - django_apps/shapez_solver/services/recipe_graph_topology.py
- [[_validate_delivery_edge()]] - code - django_apps/shapez_solver/services/recipe_graph_topology.py
- [[_validate_input_edge()]] - code - django_apps/shapez_solver/services/recipe_graph_topology.py
- [[_validate_output_edge()]] - code - django_apps/shapez_solver/services/recipe_graph_topology.py
- [[``graph_document`` 의 ``nodes`` 리스트에서 ``str(id) - 노드 dict`` 맵을 만든다.      ``val]] - rationale - django_apps/shapez_solver/services/recipe_graph_topology.py
- [[assert_delivery_targets_unique()]] - code - django_apps/shapez_solver/services/recipe_graph_topology.py
- [[assert_recipe_graph_edge_topology()]] - code - django_apps/shapez_solver/services/recipe_graph_topology.py
- [[index_recipe_graph_nodes_by_id()]] - code - django_apps/shapez_solver/services/recipe_graph_topology.py
- [[recipe_graph_topology.py]] - code - django_apps/shapez_solver/services/recipe_graph_topology.py
- [[각 target shape에는 최대 하나의 ``delivery`` 입력만 허용한다.]] - rationale - django_apps/shapez_solver/services/recipe_graph_topology.py
- [[검증 통과용 graph_document에 대해 연결 규칙을 강제한다.      - ``input`` 엣지 ``shape`` → ``oper]] - rationale - django_apps/shapez_solver/services/recipe_graph_topology.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/assert_recipe_graph_edge_topology
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_Any]]
- 4 edges to [[_COMMUNITY_recipe_graph_recompute.py]]

## Top bridge nodes
- [[assert_recipe_graph_edge_topology()]] - degree 9, connects to 2 communities
- [[index_recipe_graph_nodes_by_id()]] - degree 6, connects to 2 communities
- [[assert_delivery_targets_unique()]] - degree 4, connects to 2 communities
- [[_resolved_edge_nodes()]] - degree 3, connects to 1 community
- [[_validate_input_edge()]] - degree 3, connects to 1 community