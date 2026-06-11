---
type: community
cohesion: 0.12
members: 34
---

# macro_recipe_graph_visual.py

**Cohesion:** 0.12 - loosely connected
**Members:** 34 nodes

## Members
- [[GraphPreviewRenderer]] - code - django_apps/web/services/graph_preview.py
- [[React Flow 스냅샷에 macro visual 미리보기(PNG URL, preview_scene, alt)를 합친다.]] - rationale - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[SolverGraph]] - code - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[SolverGraphEdge]] - code - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[SolverGraphNode]] - code - django_apps/shapez_solver/view_graph_serialization.py
- [[SolverOperationNode]] - code - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[SolverShapeNode]] - code - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[Wire 노드(kind=shape)의 PNG URL·scene·alt를 React 노드 id 기준으로 묶는다.]] - rationale - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[_build_shape_overlay_entry_fields()]] - code - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[_collect_node_xy()]] - code - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[_edge_doc_to_solver_edge()]] - code - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[_graph_node_doc_to_solver()]] - code - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[_load_macro_visual_payload()]] - code - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[_macro_payload_for_node()]] - code - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[_merge_preview_into_react_node()]] - code - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[_normalize_shape_role()]] - code - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[_serialize_solver_operation_node()]] - code - django_apps/shapez_solver/view_graph_serialization.py
- [[_serialize_solver_shape_node()]] - code - django_apps/shapez_solver/view_graph_serialization.py
- [[_shape_overlay_pair_from_visual_item()]] - code - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[_shape_visual_overlay_by_node_id()]] - code - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[_solver_graph_from_validated_document()]] - code - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[``validate_graph_document`` 결과 dict만 받는다(추가 검증·deepcopy 없음).]] - rationale - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[build_preview_scene()]] - code - django_apps/shapez_solver/view_graph_serialization.py
- [[document_to_solver_graph()]] - code - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[enrich_react_flow_with_macro_visual_previews()]] - code - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[graph_document JSON을 검증한 뒤 SolverGraph DTO로 변환한다.]] - rationale - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[graph_document(JSON) → 솔버 그래프 UI용 wire payload.]] - rationale - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[graph_document를 ``renderSolverGraph``  ``mountGraph``가 기대하는 JSON으로 직렬화한다.]] - rationale - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[macro_recipe_graph_visual.py]] - code - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[serialize_graph_edge()]] - code - django_apps/shapez_solver/view_graph_serialization.py
- [[serialize_graph_node()]] - code - django_apps/shapez_solver/view_graph_serialization.py
- [[serialize_macro_recipe_visual()]] - code - django_apps/shapez_solver/services/macro_recipe_graph_visual.py
- [[serialize_solver_graph()]] - code - django_apps/shapez_solver/view_graph_serialization.py
- [[view_graph_serialization.py]] - code - django_apps/shapez_solver/view_graph_serialization.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/macro_recipe_graph_visualpy
SORT file.name ASC
```

## Connections to other communities
- 19 edges to [[_COMMUNITY_Any]]
- 3 edges to [[_COMMUNITY_build_shape_render_scene()]]
- 2 edges to [[_COMMUNITY_recipe_graph_recompute.py]]
- 1 edge to [[_COMMUNITY_ShapeCodeParseError]]
- 1 edge to [[_COMMUNITY_graph_preview.py]]

## Top bridge nodes
- [[build_preview_scene()]] - degree 7, connects to 3 communities
- [[serialize_macro_recipe_visual()]] - degree 10, connects to 2 communities
- [[document_to_solver_graph()]] - degree 6, connects to 2 communities
- [[GraphPreviewRenderer]] - degree 8, connects to 1 community
- [[serialize_graph_node()]] - degree 8, connects to 1 community