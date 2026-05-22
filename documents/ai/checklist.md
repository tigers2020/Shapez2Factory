# Checklist

**기준일**: 2026-05-19

## 제거 완료 (shapez_asteroid)

- [x] `django_apps/shapez_asteroid/` 삭제
- [x] `tests/unit/shapez_asteroid/`, `tests/unit/shapez_asteroid_v2/`, `tests/fixtures/asteroid_mining_layout/` 삭제
- [x] `INSTALLED_APPS`·`config/urls.py`·`pyproject.toml` mypy overrides·`pytest.ini`·`tests/conftest.py`에서 참조 제거
- [x] `documents/Algorithm/mining_solver_cursor_sessions/` 및 관련 active 플랜/체크리스트 정리
- [x] `config/shapez_runtime_flags.py`에서 mining 전용 env 노출 제거(복사 디버그·그래프 프리뷰만 유지)

## 에이전트 품질 게이트

- [x] Context trim (2026-05-18): alwaysApply → [`shapez2-core.mdc`](../../.cursor/rules/shapez2-core.mdc) 단일; [`AGENTS.md`](../../AGENTS.md) 라우팅만
- [x] Harness slim (2026-05-19): `AGENTS.md` ~90줄 축소; stub rules 3개 삭제; 스킬 16→5(active)+archive; `cursor_slim_setup.md` 신설
- [ ] 마감 보고 **Caveman 6절** 준수 ([`shapez2-core.mdc`](../../.cursor/rules/shapez2-core.mdc) · [`AGENTS.md`](../../AGENTS.md))
- [ ] 작업 분류(계약·구현·리팩터·문서·회귀) — [`AGENTS.md` § Contract-first TDD](../../AGENTS.md#development-mode-contract-first-tdd)
- [ ] [Forbidden shortcuts](manuals/testing.md#forbidden-shortcuts) 해당 없음
- [ ] 계약·불변식 변경 시 테스트 추가·갱신(또는 생략 이유 in **Tests**)

## 검증 (로컬)

- [ ] `python manage.py check`
- [x] 반복: unified replay + selector narrow pytest (2026-05-19)
- [x] PR/병합 full gate: `pytest` 813 passed (2026-05-19)
- [ ] PR/병합 full gate 재실행: `ruff check .` → `black --check .` → `mypy django_apps config src` → `python -m pytest -n auto --dist loadscope` (또는 `test_full.ps1`; `-q`/`--quiet`/`--tb=no` 금지 — [`testing.md`](manuals/testing.md))
- [x] 테스트 속도 (2026-05-21): session `game_data` import, module exhaustive-gene fixtures, `pytest-xdist`, `slow` 마커, 중복 테스트 제거 — [`docs/superpowers/plans/2026-05-21-test-suite-speed.md`](../superpowers/plans/2026-05-21-test-suite-speed.md)
