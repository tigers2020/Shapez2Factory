# 매뉴얼: Testing · 검증

## pytest (권장 실행 형태)

```bash
python -m pytest
```

PR 직전·CI에서만 전체에 가깝게 두고, 로컬 반복은 아래 **빠른 루틴**을 권장한다.

### 빠른 루틴 · 병렬 · `slow` 마커

- **병렬**: `pip install -e ".[dev]"`에 `pytest-xdist` 포함. 예: `python -m pytest -n auto --dist loadscope` (Django DB 테스트 충돌 시 `--dist loadscope` 유지).
- **`slow`**: 리플레이 빌드·무거운 DB 경로. `pytest.ini`에 등록. 부착 위치: `tests/integration/web/test_asteroid_miner_layout_solver.py`(모듈), `tests/unit/asteroid_lab/test_optimization_replay_persist.py`(모듈), `test_replay_pipeline_service.py`의 DB 리플레이 테스트·`test_replay_snapshot_contract.py`의 대형 리플레이 계약 테스트.
- **로컬 단위 위주**: `python -m pytest -n auto --dist loadscope -m "not slow" tests/unit/shapez_asteroid tests/unit/asteroid_lab tests/unit/web`
- **느린 것만**: `python -m pytest -n auto --dist loadscope -m slow`
- **Makefile**(루트): `make lint` · `make type` · `make test-fast` · `make test-integration` · `make test-slow` · `make test-all` (`PYTHON=python3` 등 오버라이드 가능).

`--reuse-db`는 `pytest.ini`의 `addopts`에 이미 포함되어 있다.

### mypy 캐시

`pyproject.toml`의 `[tool.mypy] cache_dir`를 사용한다. CI에서는 해당 디렉터리를 캐시 아티팩트로 두면 재실행이 빨라진다.

## 구간 실행

| 방식 | 예 |
|------|-----|
| 마커 | `-m unit`, `-m integration`, `-m slow`, `-m "not slow"`, `-m shapez_solver`, `-m shapez_core`, `-m web`, `-m api`, `-m asteroid_lab` |
| 조합 | `-m "unit and shapez_core"` |
| 경로 | `python -m pytest tests/unit/shapez_solver/` · `python -m pytest tests/unit/asteroid_lab/` |

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

템플릿·지정 Python 경로의 gettext msgid를 반영하려면 루트에서 `python scripts/build_locale_ko.py`를 실행한다. PR/CI에서는 `python scripts/build_locale_ko.py --strict`로 `django_apps/web/views/public_pages.py`에 등장하는 리터럴 `_("...")`가 `scripts/build_locale_ko.py`의 `KO`에 모두 있는지 검증한다(`tests/unit/test_build_locale_ko_strict.py`).

## 하네스 순서 (게이트)

`pytest` → `ruff` → `mypy` → `black` 통과를 원칙으로 한다. 로컬 반복 시에만 구간 `pytest`로 단축 가능.

에이전트가 짧은 주기로 전체 스위트를 반복 실행하면 CI·로컬 대기 비용이 커진다. **구간·마커·경로**로 돌리고, 머지 전에만 전체에 가깝게 확장하는 습관을 권장한다(배경: [`cursor_usage.md`](cursor_usage.md) §12).

## 완료 보고

실행 못 한 명령·이유·남은 위험을 적는다 ([`AGENTS.md`](../../../AGENTS.md)).
