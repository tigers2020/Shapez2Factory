---
type: community
cohesion: 0.20
members: 20
---

# parse_shape()

**Cohesion:** 0.20 - loosely connected
**Members:** 20 nodes

## Members
- [[Cutter primitive의 leftright output code를 반환한다.]] - rationale - django_apps/shapez_solver/services/operation_semantics.py
- [[Search action generator가 사용할 operation dispatch.]] - rationale - django_apps/shapez_solver/services/operation_semantics.py
- [[Shape code 문자열을 canonical Shape로 변환한다.]] - rationale - django_apps/shapez_solver/services/operation_semantics.py
- [[Stacker primitive의 output code를 반환한다.]] - rationale - django_apps/shapez_solver/services/operation_semantics.py
- [[Swapper primitive의 2-output code를 engine semantics 기준으로 반환한다.]] - rationale - django_apps/shapez_solver/services/operation_semantics.py
- [[_apply_color_mixer()]] - code - django_apps/shapez_solver/services/operation_semantics.py
- [[_apply_crystal_generator()]] - code - django_apps/shapez_solver/services/operation_semantics.py
- [[_apply_painter()]] - code - django_apps/shapez_solver/services/operation_semantics.py
- [[_engine_outputs_single_input()]] - code - django_apps/shapez_solver/services/operation_semantics.py
- [[apply_operation()]] - code - django_apps/shapez_solver/services/operation_semantics.py
- [[cut()]] - code - django_apps/shapez_solver/services/operation_semantics.py
- [[infer_uniform_shape_color()]] - code - django_apps/shapez_solver/services/operation_semantics.py
- [[merge_flow()]] - code - django_apps/shapez_solver/services/operation_semantics.py
- [[operation_semantics.py]] - code - django_apps/shapez_solver/services/operation_semantics.py
- [[parse_shape()]] - code - django_apps/shapez_solver/services/operation_semantics.py
- [[rotate()]] - code - django_apps/shapez_solver/services/operation_semantics.py
- [[stack()]] - code - django_apps/shapez_solver/services/operation_semantics.py
- [[swap()]] - code - django_apps/shapez_solver/services/operation_semantics.py
- [[모든 비어있지 않은·비-pin 칸의 색이 동일할 때 그 한 글자 색 코드. 유체 색 추론용.]] - rationale - django_apps/shapez_solver/services/operation_semantics.py
- [[회전 primitive의 canonical output code를 반환한다.]] - rationale - django_apps/shapez_solver/services/operation_semantics.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/parse_shape
SORT file.name ASC
```

## Connections to other communities
- 12 edges to [[_COMMUNITY_Shape]]
- 5 edges to [[_COMMUNITY_pure_fluid_color()]]
- 3 edges to [[_COMMUNITY_OperationType]]
- 1 edge to [[_COMMUNITY_analyze_pattern_lab_shape()]]
- 1 edge to [[_COMMUNITY_ShapeCodeParseError]]
- 1 edge to [[_COMMUNITY_recipe_graph_recompute.py]]

## Top bridge nodes
- [[parse_shape()]] - degree 18, connects to 4 communities
- [[apply_operation()]] - degree 14, connects to 3 communities
- [[rotate()]] - degree 6, connects to 2 communities
- [[_engine_outputs_single_input()]] - degree 5, connects to 2 communities
- [[_apply_color_mixer()]] - degree 5, connects to 2 communities