# Checklist

**기준일**: 2026-05-15

## 제거 완료 (shapez_asteroid)

- [x] `django_apps/shapez_asteroid/` 삭제
- [x] `tests/unit/shapez_asteroid/`, `tests/unit/shapez_asteroid_v2/`, `tests/fixtures/asteroid_mining_layout/` 삭제
- [x] `INSTALLED_APPS`·`config/urls.py`·`pyproject.toml` mypy overrides·`pytest.ini`·`tests/conftest.py`에서 참조 제거
- [x] `documents/Algorithm/mining_solver_cursor_sessions/` 및 관련 active 플랜/체크리스트 정리
- [x] `config/shapez_runtime_flags.py`에서 mining 전용 env 노출 제거(복사 디버그·그래프 프리뷰만 유지)

## 에이전트 품질 게이트

- [ ] 마감 보고 **Caveman 6절** 준수 ([`caveman-output.mdc`](../../.cursor/rules/caveman-output.mdc) · [`AGENTS.md`](../../AGENTS.md))

## 검증 (로컬)

- [ ] `python manage.py check`
- [ ] `python -m pytest tests/unit/asteroid_lab/ tests/integration/web/ tests/unit/test_build_locale_ko_strict.py`
- [ ] `ruff check .` → `mypy .` → `black --check .` (변경 범위 또는 전체)
