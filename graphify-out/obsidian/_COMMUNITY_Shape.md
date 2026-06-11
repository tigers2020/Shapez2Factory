---
type: community
cohesion: 0.16
members: 33
---

# Shape

**Cohesion:** 0.16 - loosely connected
**Members:** 33 nodes

## Members
- [[._apply_crystal_generator()]] - code - django_apps/shapez_solver/services/operation_engine.py
- [[._apply_painter()]] - code - django_apps/shapez_solver/services/operation_engine.py
- [[.apply()_1]] - code - django_apps/shapez_solver/services/operation_engine.py
- [[.color_mixer()]] - code - django_apps/shapez_solver/services/operation_engine.py
- [[.cut()]] - code - django_apps/shapez_solver/services/operation_engine.py
- [[.half_destroyer()]] - code - django_apps/shapez_solver/services/operation_engine.py
- [[.painter()]] - code - django_apps/shapez_solver/services/operation_engine.py
- [[.pin_pusher()]] - code - django_apps/shapez_solver/services/operation_engine.py
- [[.rotate_180()]] - code - django_apps/shapez_solver/services/operation_engine.py
- [[.rotate_ccw()]] - code - django_apps/shapez_solver/services/operation_engine.py
- [[.rotate_cw()]] - code - django_apps/shapez_solver/services/operation_engine.py
- [[.splitter()]] - code - django_apps/shapez_solver/services/operation_engine.py
- [[.stacker()]] - code - django_apps/shapez_solver/services/operation_engine.py
- [[.swapper()]] - code - django_apps/shapez_solver/services/operation_engine.py
- [[OperationEngine]] - code - django_apps/shapez_solver/services/operation_engine.py
- [[OperationEngine.apply 에 대응하는 순수 연산 헬퍼(유체는 fluid_semantics).  회전·절단·크리스탈 등은 여기서]] - rationale - django_apps/shapez_solver/services/engine_operation_helpers.py
- [[Shape]] - code - django_apps/shapez_solver/services/shape_layer_physics.py
- [[West half then east half (project quadrant order).]] - rationale - django_apps/shapez_solver/services/engine_operation_helpers.py
- [[color_mixer_fluids()]] - code - django_apps/shapez_solver/services/engine_operation_helpers.py
- [[crystal_generator_output()]] - code - django_apps/shapez_solver/services/engine_operation_helpers.py
- [[cutter_halves()]] - code - django_apps/shapez_solver/services/engine_operation_helpers.py
- [[engine_operation_helpers.py]] - code - django_apps/shapez_solver/services/engine_operation_helpers.py
- [[half_destroyer_shape()]] - code - django_apps/shapez_solver/services/engine_operation_helpers.py
- [[merge_identical_shapes()]] - code - django_apps/shapez_solver/services/engine_operation_helpers.py
- [[operation_engine.py]] - code - django_apps/shapez_solver/services/operation_engine.py
- [[painter_output()]] - code - django_apps/shapez_solver/services/engine_operation_helpers.py
- [[painter_with_fluid_target()]] - code - django_apps/shapez_solver/services/engine_operation_helpers.py
- [[pin_pusher_output()]] - code - django_apps/shapez_solver/services/engine_operation_helpers.py
- [[rotate_shape()]] - code - django_apps/shapez_solver/services/engine_operation_helpers.py
- [[splitter_outputs()]] - code - django_apps/shapez_solver/services/engine_operation_helpers.py
- [[stacker_output()]] - code - django_apps/shapez_solver/services/engine_operation_helpers.py
- [[swapper_outputs()]] - code - django_apps/shapez_solver/services/engine_operation_helpers.py
- [[동일 canonical 도형만 허용; 수량 합산은 그래프 재계산 레이어에서 처리.]] - rationale - django_apps/shapez_solver/services/engine_operation_helpers.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Shape
SORT file.name ASC
```

## Connections to other communities
- 12 edges to [[_COMMUNITY_parse_shape()]]
- 8 edges to [[_COMMUNITY_crystal_geometry.py]]
- 7 edges to [[_COMMUNITY_shape_operations.py]]
- 7 edges to [[_COMMUNITY_pure_fluid_color()]]
- 6 edges to [[_COMMUNITY_post_stack_physics()]]
- 3 edges to [[_COMMUNITY_ShapePart]]
- 3 edges to [[_COMMUNITY_recipe_graph_recompute.py]]
- 2 edges to [[_COMMUNITY_analyze_pattern_lab_shape()]]
- 2 edges to [[_COMMUNITY_build_shape_render_scene()]]
- 2 edges to [[_COMMUNITY_OperationType]]
- 1 edge to [[_COMMUNITY_Protocol]]
- 1 edge to [[_COMMUNITY_shape_codec.py]]
- 1 edge to [[_COMMUNITY_mix_color_pair()]]

## Top bridge nodes
- [[Shape]] - degree 67, connects to 11 communities
- [[color_mixer_fluids()]] - degree 7, connects to 2 communities
- [[swapper_outputs()]] - degree 6, connects to 2 communities
- [[stacker_output()]] - degree 6, connects to 2 communities
- [[engine_operation_helpers.py]] - degree 14, connects to 1 community