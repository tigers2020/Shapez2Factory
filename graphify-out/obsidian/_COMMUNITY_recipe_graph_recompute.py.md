---
type: community
cohesion: 0.07
members: 57
---

# recipe_graph_recompute.py

**Cohesion:** 0.07 - loosely connected
**Members:** 57 nodes

## Members
- [[(성공 여부, 출력 shape_code 튜플, 경고 메시지). 실패 시 튜플은 빈 값.]] - rationale - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[MERGESTACKERCUTTER 등 출력 레인별 수량이 필요할 때만 튜플을 반환한다.]] - rationale - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[Pattern Lab·스태프 카탈로그용 ``graph_document``에서 operation 위상순 스텝 요약을 만든다.      - 검]] - rationale - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[Recipe graph document validate, topo order, and engine-backed recompute.]] - rationale - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[Return (role, shape_id, op_id) with role ``produce`` or ``consume``, else None.]] - rationale - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[Return list of (producer_op_id, consumer_op_id) where consumer runs after produc]] - rationale - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[Same ordering as ``_sorted_input_codes_for_operation`` (slot edges before unsort]] - rationale - django_apps/shapez_solver/services/recipe_graph_input_carrier.py
- [[_RecomputeGraphMutation]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_append_auto_created_operation_output_shape()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_apply_delivery_edges()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_apply_recomputed_operation()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_as_str()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_assert_edges_reference_known_nodes()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_assign_operation_outputs()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_cutter_output_quantities()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_edge_adjacency()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_merge_input_quantity_sum()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_new_shape_id()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_normalize_crystal_generator_crystal_color()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_normalize_operation_node()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_normalize_painter_paint_color()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_normalize_shape_node()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_normalize_shape_node_shape_code()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_normalize_shape_node_source_carrier()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_operation_dep_pairs_from_shape_links()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_operation_dependency_edges()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_output_edge_sort_key()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_output_quantities_for_recomputed_op()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_output_slots_strings_for_edges()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_recompute_one_operation_in_topo()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_required_input_count_for_recompute()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_shape_op_edge_action()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_shape_quantity_int()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_sorted_input_codes_for_operation()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_sorted_output_edges_for_operation()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_sorted_pattern_macro_input_slots()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_topological_operation_order()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_validate_graph_edge_row()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_validate_graph_node()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[_validated_graph_document_for_pattern_macro()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[``try_pattern_macro_step_rows_from_graph_document`` 선행 검증. 실패 시 ``None``.]] - rationale - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[``validate_graph_document`` 를 통과한 문서에 대해 재계산만 수행한다(추가 deepcopy 없음).      ``wor]] - rationale - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[default_empty_graph_document()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[defaultdict]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[graph_document JSON 검증. 통과 시 정규화된 dict 반환.]] - rationale - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[input to → edges, output from → edges (참조는 원본 edge dict와 동일).]] - rationale - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[output 엣리스트를 Pattern Macro 스텝의 ``output_slots`` 문자열 목록으로 바꾼다.]] - rationale - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[recipe_graph_recompute.py]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[recompute_graph_document()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[recompute_validated_graph_document()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[sorted_shape_input_edges_to_operation()]] - code - django_apps/shapez_solver/services/recipe_graph_input_carrier.py
- [[try_pattern_macro_step_rows_from_graph_document()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[validate_graph_document()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[검증을 통과한 빈 레시피 그래프(JSON).]] - rationale - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[세로 컷 조각 수를 반으로 나눈다(풀 4 → 2+2). ``quantity``2 는 레거시로 (1,1).]] - rationale - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[연결이 갖춰진 operation에 대해 apply_operation으로 하류 shape_code를 갱신한다.      Returns (upd]] - rationale - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[연산 재계산 후 intermediate의 ``shape_code``를 delivery 링크로 target에 복사한다.]] - rationale - django_apps/shapez_solver/services/recipe_graph_recompute.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/recipe_graph_recomputepy
SORT file.name ASC
```

## Connections to other communities
- 31 edges to [[_COMMUNITY_Any]]
- 14 edges to [[_COMMUNITY_OperationType]]
- 4 edges to [[_COMMUNITY_assert_recipe_graph_edge_topology()]]
- 3 edges to [[_COMMUNITY_Shape]]
- 3 edges to [[_COMMUNITY_pure_fluid_color()]]
- 2 edges to [[_COMMUNITY_macro_recipe_graph_visual.py]]
- 1 edge to [[_COMMUNITY_build_terrain_rim_highlight_from_rendera]]
- 1 edge to [[_COMMUNITY_import_toolbar_tree()]]
- 1 edge to [[_COMMUNITY_parse_shape()]]
- 1 edge to [[_COMMUNITY_RouteProbedBundleCandidate]]

## Top bridge nodes
- [[validate_graph_document()]] - degree 14, connects to 4 communities
- [[_apply_recomputed_operation()]] - degree 8, connects to 4 communities
- [[_recompute_one_operation_in_topo()]] - degree 11, connects to 3 communities
- [[defaultdict]] - degree 9, connects to 3 communities
- [[_sorted_pattern_macro_input_slots()]] - degree 6, connects to 3 communities