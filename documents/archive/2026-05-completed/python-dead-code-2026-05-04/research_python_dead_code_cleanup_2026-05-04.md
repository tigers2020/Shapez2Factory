# Python 죽은·중복·레거시 코드 정리 — 조사 요약 (2026-05-04)

## 범위

- `django_apps/shapez_core/`, `django_apps/shapez_solver/`, `django_apps/web/`, `tests/`, `config/` 등 런타임·테스트 Python.
- 비범위: `frontend/recipe_graph_editor/`, `django_apps/web/static/web/js/recipe_graph_editor/` (플랜 비범위).

## 정적 분석: Ruff

실행: `python -m ruff check .` (프로젝트 루트).

### 선택 규칙 `F401`, `F821`, `F841`

- **통과** — 미사용 import·정의되지 않은 이름·미사용 지역 변수 후보 없음.

### 전체 규칙에서 발견했던 항목 (1차 구현에서 처리됨)

| 규칙 | 파일 | 조치 |
|------|------|------|
| I001 | `django_apps/shapez_solver/migrations/0004_patternfamily_graph_draft.py` | `ruff check --fix` |
| I001 | `tests/integration/web/test_macro_pattern_staff.py` | `ruff check --fix` |
| E501 | `tests/integration/web/test_macro_pattern_staff.py` | import 괄호 줄바꿈(Ruff 자동) |
| E501 | `tests/unit/shapez_solver/test_recipe_graph_react_flow_adapter.py` | dict 리터럴 다줄 |
| E501 | `tests/unit/shapez_solver/test_recipe_graph_topology.py` | dict 리터럴 다줄 |

구현 후: `python -m ruff check .` 전체 통과.

### Mypy (검증 보강)

- 초기 조사 시 `django_apps/web`의 allauth 연동·`context_processors`·일부 단위 테스트에서 오류가 있었음.
- 후속: `context_processors.django_debug`에 요청·반환 타입 추가, `test_macro_recipe_staff_catalog`의 `empty_doc`에 `dict[str, object]`, `pyproject.toml`의 mypy override에 `django_apps.web.social_adapter`·`django_apps.web.socialaccount_forms` 추가 → `python -m mypy .` 통과.

## Vulture

- 실행: `python -m vulture django_apps tests config --min-confidence 80`
- **결과**: 로컬 환경에 `vulture` 패키지 미설치로 실행 불가. 고신뢰도 미사용 심볼 목록은 이번 조사에 포함하지 않음.

## 참조 추적(샘플)

- `shapez_solver/services/` 내 `recipe_graph_*`, `graph_document_primitive_chain`, `macro_recipe_staff_catalog` 등은 `django_apps/web/views.py`, URL, 통합·단위 테스트에서 import·호출 확인.
- `shapez_core` 모듈 트리(예: `shape_pattern.py`)는 서비스·테스트에서 참조됨.
- **전체 `services/*.py` 파일을 orphan으로 단정하지 않음** — Django 문자열 참조·동적 로딩 오탐 가능성은 플랜의 리스크 절과 동일.

## 레거시 명칭 (플랜 인용)

- `tests/unit/shapez_solver/test_legacy_planner_characterization.py`는 **회귀·스펙 고정** 목적로 유지. 삭제 대상 아님.

## 메모

- 루트 `.gitignore`에 `documents/`가 있어 Git 추적 여부는 별도 정책에 따름. 워크스페이스에는 본 문서 경로로 기록함.
