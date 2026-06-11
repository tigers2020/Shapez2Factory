---
type: community
cohesion: 0.15
members: 17
---

# pure_fluid_color()

**Cohesion:** 0.15 - loosely connected
**Members:** 17 nodes

## Members
- [[Non-empty, non-pin quadrants must share one color; else ``None``.]] - rationale - django_apps/shapez_solver/services/fluid_semantics.py
- [[Pattern macro UI fluid wire는 균일 잉크 한 글자만; 재료(shape)는 기존 shape_code.]] - rationale - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[Pure color fluid encoded as a Shape (uniform ink on paintable parts).  Used by C]] - rationale - django_apps/shapez_solver/services/fluid_semantics.py
- [[Recipe graph ``source_carrier=fluid`` and primary-only ink rules.]] - rationale - django_apps/shapez_solver/services/recipe_graph_source_carrier.py
- [[Recolor every paintable (non-empty, non-pin) quadrant; pins and empties unchange]] - rationale - django_apps/shapez_solver/services/fluid_semantics.py
- [[Return the single fluid color letter for a pure-fluid carrier shape.]] - rationale - django_apps/shapez_solver/services/fluid_semantics.py
- [[_pattern_macro_input_slot_label()]] - code - django_apps/shapez_solver/services/recipe_graph_recompute.py
- [[``source_carrier`` 유체 소스의 ``shape_code``는 순수 유체이며 색은 rgb만.]] - rationale - django_apps/shapez_solver/services/recipe_graph_source_carrier.py
- [[assert_fluid_carrier_shape_for_role()]] - code - django_apps/shapez_solver/services/recipe_graph_source_carrier.py
- [[assert_intermediate_fluid_shape_valid()]] - code - django_apps/shapez_solver/services/recipe_graph_source_carrier.py
- [[assert_source_fluid_shape_valid()]] - code - django_apps/shapez_solver/services/recipe_graph_source_carrier.py
- [[fluid_semantics.py]] - code - django_apps/shapez_solver/services/fluid_semantics.py
- [[infer_uniform_paint_color()]] - code - django_apps/shapez_solver/services/fluid_semantics.py
- [[pure_fluid_color()]] - code - django_apps/shapez_solver/services/fluid_semantics.py
- [[recipe_graph_source_carrier.py]] - code - django_apps/shapez_solver/services/recipe_graph_source_carrier.py
- [[uniform_fluid_output_from_template()]] - code - django_apps/shapez_solver/services/fluid_semantics.py
- [[유체 intermediate 순수 유체(보조색 허용).]] - rationale - django_apps/shapez_solver/services/recipe_graph_source_carrier.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/pure_fluid_color
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_Shape]]
- 5 edges to [[_COMMUNITY_parse_shape()]]
- 3 edges to [[_COMMUNITY_recipe_graph_recompute.py]]
- 1 edge to [[_COMMUNITY_Any]]
- 1 edge to [[_COMMUNITY_build_shape_render_scene()]]
- 1 edge to [[_COMMUNITY_OperationType]]

## Top bridge nodes
- [[_pattern_macro_input_slot_label()]] - degree 8, connects to 5 communities
- [[pure_fluid_color()]] - degree 12, connects to 3 communities
- [[assert_source_fluid_shape_valid()]] - degree 5, connects to 1 community
- [[assert_intermediate_fluid_shape_valid()]] - degree 5, connects to 1 community
- [[infer_uniform_paint_color()]] - degree 4, connects to 1 community