# 매뉴얼: Frontend · 템플릿 · 정적 자산

## Django 쪽

- 템플릿·페이지 조립: `django_apps/web/templates/`
- 정적 JS/CSS: `django_apps/web/static/`

뷰는 얇게 유지 ([`django.md`](django.md)).

## Recipe Graph 에디터 (Vite 등)

- 소스: `frontend/recipe_graph_editor/` (Tailwind 4 등 — 패키지는 해당 디렉터리 `package.json` 확인)
- 픽스처 기반 와이어 규칙 검증: `npm --prefix frontend/recipe_graph_editor test` (Vitest, `tests/fixtures/recipe_connection_rule_scenarios.json`과 동기)
- 빌드 산출물이 정적 번들로 웹 앱에 들어가는 구조이면, **수정 후 빌드·복사 절차**를 이번 작업 범위에 포함했는지 확인한다.

## 그래프 레이아웃 엔진 (`frontend/graph_layout/`)

- 소스는 TypeScript 모듈(`graphLayoutEngine.ts` 진입 + `graphLayout*.ts` 단계별 구현). 타임라인·에디터 공통 로직이다.
- Django 정적 번들 **`django_apps/web/static/web/js/solver_graph_layout.js`**, **`editor_graph_layout.js`** 는 **esbuild 출력물**이다. 저장소에 두되 **직접 수정하지 않는다.** 레이아웃 로직을 바꾼 뒤에는 반드시 재생성한다.
- 재생성: 레포 루트에서 `npm run build:graph-layout` (루트 `package.json`의 `build` 스크립트에 포함됨).
- Python 단위 테스트 `tests/unit/web/test_editor_graph_layout.py`는 Node가 `editor_graph_layout.js`를 import 하므로, 엔진 변경 후 위 명령으로 정적 파일을 갱신한 뒤 pytest를 돌린다.

## 원칙

- UI에 비즈니스 정책을 넣지 않는다. API·서비스 경계는 [`architecture.mdc`](../../../.cursor/rules/architecture.mdc) 참고.

## 관련 매뉴얼

- 그래프 UI 동작: [`graph_ui.md`](graph_ui.md)
- 테스트: [`testing.md`](testing.md)
