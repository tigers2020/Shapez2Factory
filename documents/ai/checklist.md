# Checklist

**기준일**: 2026-05-15

## 제거 완료 (shapez_asteroid)

- [x] `django_apps/shapez_asteroid/` 삭제
- [x] `tests/unit/shapez_asteroid/`, `tests/unit/shapez_asteroid_v2/`, `tests/fixtures/asteroid_mining_layout/` 삭제
- [x] `INSTALLED_APPS`·`config/urls.py`·`pyproject.toml` mypy overrides·`pytest.ini`·`tests/conftest.py`에서 참조 제거
- [x] `documents/Algorithm/mining_solver_cursor_sessions/` 및 관련 active 플랜/체크리스트 정리
- [x] `config/shapez_runtime_flags.py`에서 mining 전용 env 노출 제거(복사 디버그·그래프 프리뷰만 유지)

## 에이전트 품질 게이트

- [x] Context trim (2026-05-18): alwaysApply → [`shapez2-core.mdc`](../../.cursor/rules/shapez2-core.mdc) 단일; [`AGENTS.md`](../../AGENTS.md) 라우팅만
- [ ] 마감 보고 **Caveman 6절** 준수 ([`shapez2-core.mdc`](../../.cursor/rules/shapez2-core.mdc) · [`AGENTS.md`](../../AGENTS.md))
- [ ] 작업 분류(계약·구현·리팩터·문서·회귀) — [`AGENTS.md` § Contract-first TDD](../../AGENTS.md#development-mode-contract-first-tdd)
- [ ] [Forbidden shortcuts](manuals/testing.md#forbidden-shortcuts) 해당 없음
- [ ] 계약·불변식 변경 시 테스트 추가·갱신(또는 생략 이유 in **Tests**)

## 검증 (로컬)

- [ ] `python manage.py check`
- [ ] 반복: narrow `python -m pytest <path>` ([testing.md](manuals/testing.md))
- [ ] PR/병합 full gate: `ruff check .` → `black --check .` → `mypy .` → `python -m pytest`
