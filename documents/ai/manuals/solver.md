# 매뉴얼: Solver · 레시피 그래프 로직

작업 전 [`AGENTS.md`](../../../AGENTS.md)와 solver/graph 혼동 방지 규칙을 확인한다.

## 위치

- 도형 도메인·파싱: `django_apps/shapez_core/`
- 솔버·플래너·레시피 그래프 재계산 등: `django_apps/shapez_solver/services/` 등

## 의존

`shapez_solver`는 `shapez_core`만 import. **Django web 앱을 solver에서 import하지 않는다.**

## 개념 분리 (필수)

아래를 **서로 다른 것**으로 취급한다.

- demand summary
- source quantity / target output count
- materialized graph nodes (물리 노드)
- visual labels
- operation / intermediate node structure

**요약 수치가 맞아도 그래프 연결·노드 구조가 자동으로 맞는 것은 아니다.**

**연산 출력 → 다른 연산 입력**으로 직접 붙이지 않는다. **중간 도형(shape) 노드**를 경유한다.

## 테스트

```bash
python -m pytest tests/unit/shapez_solver/
```

`recipe_graph_input_carrier`와 프론트 `recipeConnection`/`operationArity`의 정합은 **`tests/fixtures/recipe_connection_rule_scenarios.json`**과 `tests/unit/shapez_solver/test_recipe_connection_rule_fixture_alignment.py`로 고정한다. 프론트 측 동일 픽스처 검증은 `npm --prefix frontend/recipe_graph_editor test`를 실행한다.

상세: [`testing.md`](testing.md).

## 참고 연구

[`documents/research/research_shapez2_game_systems_2026-05-01.md`](../../../research/research_shapez2_game_systems_2026-05-01.md) — 핀·레이어 상한·열 단위 중력 등 **도형 물리**는 해당 문서의 「도형 레이어·핀(Pin) 메커닉」 절을 정본으로 삼는다.

## 관련 매뉴얼

- UI·에디터: [`graph_ui.md`](graph_ui.md)
