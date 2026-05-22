# 매뉴얼: Graph UI (레시피 그래프 화면)

시각화·편집기 작업 시 읽는다. 로직 규칙은 [`solver.md`](solver.md)와 겹치면 **solver 정본**을 따른다.

## 위치 (예)

- Django 정적·템플릿: `django_apps/web/`
- 레시피 그래프 에디터 번들: `django_apps/web/static/web/js/recipe_graph_editor/`
- 소스 에디터(필요 시 빌드): `frontend/recipe_graph_editor/`

## 원칙

- **표시 데이터**와 **솔버 내부 물리 그래프**를 혼동하지 않는다.
- 라벨·좌표·React Flow 어댑터는 UI/어댑터 경계에 두고, 도메인 규칙은 core/solver에 둔다.

## 혼동 방지 (반복)

요약(demand summary 등)만으로 **연결 그래프 정합**이 증명되지 않는다. 연산 간 직접 연결 금지·중간 도형 노드 경유는 [`solver.md`](solver.md)와 동일.

### 레시피 그래프: material / fluid 와이어

검증 메시지의 **material** 은 “크리스털 파트만 허용”이 아니라 **도형 캐리어**(일반 `shape` 노드에서 오는 연결)를 뜻한다. **fluid** 는 `source_carrier=fluid` 인 순색 유체 소스에서 오는 연결이다.

**Crystal Generator** (`crystal_generator`): 노드에 `crystal_color`가 있으면 **도형 입력 1개**만 연결하면 된다. `crystal_color`가 없으면 **Painter와 동일**하게 상단 `in-1`에 유체(fluid), 하단 `in`에 가공 대상 도형(material)을 연결한다. 규칙 요약은 [`documents/game_rules/crystal_mechanics.md`](../../game_rules/crystal_mechanics.md) “레시피 그래프(와이어 타입)” 절을 본다.

### 연산·와이어 규칙 변경 시 (체크리스트)

연산 종류·입력 슬롯·material/fluid carrier 규칙을 바꿀 때는 **`django_apps/shapez_solver/services/recipe_graph_input_carrier.py`**(정본)와 **`frontend/recipe_graph_editor/src/recipeConnection.ts`**, **`operationArity.ts`**를 함께 수정한다. 공통 시나리오는 **`tests/fixtures/recipe_connection_rule_scenarios.json`**에 추가·갱신한 뒤 `python -m pytest tests/unit/shapez_solver/test_recipe_connection_rule_fixture_alignment.py` 및 `npm --prefix frontend/recipe_graph_editor test`로 양쪽을 검증한다 (`-q` / `--quiet` / `--tb=no` 금지 — [`testing.md`](testing.md)).

## 브라우저 확인

필요 시 로컬 서버 실행 후 수동 또는 MCP 브라우저 도구로 확인 (`.cursor/rules/mcp.mdc`).

## 관련 매뉴얼

- 프론트 빌드·Tailwind: [`frontend.md`](frontend.md)
