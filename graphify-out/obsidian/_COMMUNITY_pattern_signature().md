---
type: community
cohesion: 0.18
members: 14
---

# pattern_signature()

**Cohesion:** 0.18 - loosely connected
**Members:** 14 nodes

## Members
- [[Recipe graph_document vs pattern family signature — validation helpers.]] - rationale - django_apps/shapez_solver/services/recipe_graph_recipe_validation.py
- [[_issue()]] - code - django_apps/shapez_solver/services/recipe_graph_recipe_validation.py
- [[_shape_code_structural_error()]] - code - django_apps/shapez_solver/services/recipe_graph_recipe_validation.py
- [[``visual_graph.nodes`` 항목에 ``validation_severity``를 붙인다 (graph_markup 소비).]] - rationale - django_apps/shapez_solver/services/recipe_graph_recipe_validation.py
- [[annotate_visual_graph_with_issues()]] - code - django_apps/shapez_solver/services/recipe_graph_recipe_validation.py
- [[graph_document(재계산 후 등)을 레시피 패밀리 맥락에서 검사한다.      severity ``error``  ``warni]] - rationale - django_apps/shapez_solver/services/recipe_graph_recipe_validation.py
- [[is_full_source_signature()]] - code - django_apps/shapez_solver/services/pattern_classifier.py
- [[pattern_classifier.py]] - code - django_apps/shapez_solver/services/pattern_classifier.py
- [[pattern_signature()]] - code - django_apps/shapez_solver/services/pattern_classifier.py
- [[recipe_graph_recipe_validation.py]] - code - django_apps/shapez_solver/services/recipe_graph_recipe_validation.py
- [[validate_recipe_graph_context()]] - code - django_apps/shapez_solver/services/recipe_graph_recipe_validation.py
- [[단일 레이어 4사분면의 kind 등장 순서를 ABC… 시그니처로 표현한다.]] - rationale - django_apps/shapez_solver/services/pattern_classifier.py
- [[레시피 그래프 shape_code 구조 검사. 문제가 있으면 메시지, 없으면 ``None``.]] - rationale - django_apps/shapez_solver/services/recipe_graph_recipe_validation.py
- [[풀 소스(AAAA) 여부 — 인벤토리 매크로 후보 판별에 사용한다.]] - rationale - django_apps/shapez_solver/services/pattern_classifier.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/pattern_signature
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_analyze_pattern_lab_shape()]]
- 3 edges to [[_COMMUNITY_Any]]
- 1 edge to [[_COMMUNITY_ShapeCodeParseError]]

## Top bridge nodes
- [[validate_recipe_graph_context()]] - degree 6, connects to 2 communities
- [[pattern_signature()]] - degree 7, connects to 1 community
- [[_shape_code_structural_error()]] - degree 5, connects to 1 community
- [[_issue()]] - degree 3, connects to 1 community
- [[annotate_visual_graph_with_issues()]] - degree 3, connects to 1 community