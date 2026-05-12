# 매뉴얼: Testing · 검증

## pytest (권장 실행 형태)

```bash
python -m pytest
```

## 구간 실행

| 방식 | 예 |
|------|-----|
| 마커 | `-m unit`, `-m integration`, `-m shapez_solver`, `-m shapez_core`, `-m shapez_asteroid`, `-m web`, `-m api` |
| 조합 | `-m "unit and shapez_core"` |
| 경로 | `python -m pytest tests/unit/shapez_solver/` · `python -m pytest tests/unit/shapez_asteroid/` |

마커 정의: `pytest.ini`. 경로 기반 자동 마커: `tests/conftest.py`.

## Recipe Graph 에디터 (Vitest)

와이어·입력 arity·carrier 정렬은 Python과 공유 픽스처로 검증한다.

```bash
npm --prefix frontend/recipe_graph_editor test
```

픽스처: `tests/fixtures/recipe_connection_rule_scenarios.json` · Python: `tests/unit/shapez_solver/test_recipe_connection_rule_fixture_alignment.py`

## 린트 · 타입 · 포맷

```bash
ruff check .
mypy .
black .
```

CI에서는 `black --check .`로 포맷만 검사하는 경우가 있다.

## 로케일(`ko`)

템플릿·지정 Python 경로의 gettext msgid를 반영하려면 루트에서 `python scripts/build_locale_ko.py`를 실행한다. PR/CI에서는 `python scripts/build_locale_ko.py --strict`로 `django_apps/shapez_asteroid/views.py`와 `django_apps/web/views/public_pages.py`에 등장하는 리터럴 `_("...")`가 `scripts/build_locale_ko.py`의 `KO`에 모두 있는지 검증한다(`tests/unit/test_build_locale_ko_strict.py`).

## 하네스 순서 (게이트)

`pytest` → `ruff` → `mypy` → `black` 통과를 원칙으로 한다. 로컬 반복 시에만 구간 `pytest`로 단축 가능.

에이전트가 짧은 주기로 전체 스위트를 반복 실행하면 CI·로컬 대기 비용이 커진다. **구간·마커·경로**로 돌리고, 머지 전에만 전체에 가깝게 확장하는 습관을 권장한다(배경: [`cursor_usage.md`](cursor_usage.md) §12).

## 완료 보고

실행 못 한 명령·이유·남은 위험을 적는다 ([`AGENTS.md`](../../../AGENTS.md)).
