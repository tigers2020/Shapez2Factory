"""Pytest configuration: path-based markers for selective test runs.

Markers are applied automatically from file location (no per-test decorators):
- unit / integration — top-level under tests/
- shapez_core / shapez_solver / web / api — second segment when present
- slow — ``_SLOW_TEST_RELS`` 에 해당하는 모듈에 자동 부착

Examples:
  pytest -m unit
  pytest -m integration
  pytest -m shapez_solver
  pytest -m "unit and shapez_core"
  pytest tests/integration/web/
  pytest -m "not slow"
  pytest -m slow
"""

from __future__ import annotations

from pathlib import Path

import pytest

_TESTS_ROOT = Path(__file__).resolve().parent

_LAYER_MARKERS = frozenset({"shapez_core", "shapez_solver", "web", "api", "asteroid_lab"})

# 느린 모듈(리플레이 빌드·Django 통합 등): 로컬 기본 루틴에서는 ``-m "not slow"`` 로 제외 가능.
_SLOW_TEST_RELS = frozenset(
    {
        "integration/web/test_asteroid_miner_layout_solver.py",
        "unit/asteroid_lab/test_optimization_replay_persist.py",
        "unit/asteroid_lab/test_replay_pipeline_service.py",
    }
)


def pytest_configure(config: pytest.Config) -> None:
    """pytest-django: 테스트 DB 재사용.

    pytest.ini ``--reuse-db``와 동일, addopts 미적용 환경 보조.
    """
    opt = config.option
    if getattr(opt, "create_db", False):
        return
    if hasattr(opt, "reuse_db"):
        opt.reuse_db = True


@pytest.fixture
def without_canonical_catalog_macros() -> None:
    """Remove migration-seeded macro recipes so tests can define their own catalog rows."""

    from django_apps.shapez_solver.models import MacroRecipe

    MacroRecipe.objects.filter(
        code__in=("abcc-batch", "swap-rotate-swap-checker"),
    ).delete()


def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
) -> None:
    for item in items:
        try:
            path = Path(item.path).resolve()
            rel = path.relative_to(_TESTS_ROOT)
        except ValueError:
            continue

        parts = rel.parts
        if not parts:
            continue

        scope = parts[0]
        if scope == "unit":
            item.add_marker(pytest.mark.unit)
        elif scope == "integration":
            item.add_marker(pytest.mark.integration)

        if len(parts) >= 2 and parts[1] in _LAYER_MARKERS:
            item.add_marker(getattr(pytest.mark, parts[1]))

        rel_posix = rel.as_posix()
        if rel_posix in _SLOW_TEST_RELS:
            item.add_marker(pytest.mark.slow)
