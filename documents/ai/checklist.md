# Checklist

**As of**: 2026-05-19

## Removal complete (shapez_asteroid)

- [x] Delete `django_apps/shapez_asteroid/`
- [x] Delete `tests/unit/shapez_asteroid/`, `tests/unit/shapez_asteroid_v2/`, `tests/fixtures/asteroid_mining_layout/`
- [x] Remove references from `INSTALLED_APPS`, `config/urls.py`, `pyproject.toml` mypy overrides, `pytest.ini`, `tests/conftest.py`
- [x] Clean up `documents/Algorithm/mining_solver_cursor_sessions/` and related active plans/checklists
- [x] Remove mining-only env exposure from `config/shapez_runtime_flags.py` (keep copy debug and graph preview only)

## Agent quality gates

- [x] Context trim (2026-05-18): alwaysApply → single [`shapez2-core.mdc`](../../.cursor/rules/shapez2-core.mdc); [`AGENTS.md`](../../AGENTS.md) routing only
- [x] Harness slim (2026-05-19): `AGENTS.md` trimmed to ~90 lines; deleted 3 stub rules; skills 16→5(active)+archive; added `cursor_slim_setup.md`
- [ ] Closing report follows **Caveman 6 sections** ([`shapez2-core.mdc`](../../.cursor/rules/shapez2-core.mdc) · [`AGENTS.md`](../../AGENTS.md))
- [ ] Work classification (contract · implementation · refactor · documentation · regression) — [`AGENTS.md` § Contract-first TDD](../../AGENTS.md#development-mode-contract-first-tdd)
- [ ] [Forbidden shortcuts](manuals/testing.md#forbidden-shortcuts) — none apply
- [ ] On contract/invariant changes, add or update tests (or state skip reason in **Tests**)

## Verification (local)

- [ ] `python manage.py check`
- [x] Repeat: unified replay + selector narrow pytest (2026-05-19)
- [x] PR/merge full gate: `pytest` 813 passed (2026-05-19)
- [ ] Re-run PR/merge full gate: `ruff check .` → `black --check .` → `mypy django_apps config src` → `python -m pytest -n auto --dist loadscope` (or `test_full.ps1`; `-q`/`--quiet`/`--tb=no` forbidden — [`testing.md`](manuals/testing.md))
- [x] Test speed (2026-05-21): session `game_data` import, module exhaustive-gene fixtures, `pytest-xdist`, `slow` marker, duplicate test removal — [`docs/superpowers/plans/2026-05-21-test-suite-speed.md`](../superpowers/plans/2026-05-21-test-suite-speed.md)
