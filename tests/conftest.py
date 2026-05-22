"""Pytest configuration: path-based markers for selective test runs.

Markers are applied automatically from file location (no per-test decorators):
- unit / integration — top-level under tests/
- shapez_core / shapez_solver / web / api — second segment when present

Examples:
  pytest -m unit
  pytest -m integration
  pytest -m shapez_solver
  pytest -m "unit and shapez_core"
  pytest tests/integration/web/
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest_plugins = ["tests.unit.game_data.fixtures"]

_TESTS_ROOT = Path(__file__).resolve().parent

_LAYER_MARKERS = frozenset({"shapez_core", "shapez_solver", "web", "api", "asteroid_lab"})

# Fixtures that dominate wall time; auto-tagged slow so `-m "unit and not slow"` stays useful.
_SLOW_FIXTURE_NAMES = frozenset(
    {
        "imported_game_data_batch",
        "imported_batch",
        "imported_game_data_batch_module",
        "imported_batch_module",
        "exhaustive_genes_ext3",
        "exhaustive_genes_ext0_belt",
        "exhaustive_genes_ext1_belt",
        "connected_branch_gene_ext3",
    }
)

# Whole modules that are intentionally heavy even without the shared fixtures above.
_SLOW_MODULE_SUFFIXES = (
    "test_sample_gene_exhaustive.py",
    "test_macro_recipe_staff_catalog.py",
    "test_solver_runtime_replay_recorder.py",
    "test_simulation_systems_import.py",
    "test_simulation_speed_import.py",
)


def pytest_configure(config: pytest.Config) -> None:
    """pytest-django: 테스트 DB 재사용 (`--reuse-db`; addopts 미적용 시 보조)."""
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


def _apply_path_markers(item: pytest.Item, path: Path, rel: Path) -> None:
    parts = rel.parts
    if not parts:
        return
    scope = parts[0]
    if scope == "unit":
        item.add_marker(pytest.mark.unit)
    elif scope == "integration":
        item.add_marker(pytest.mark.integration)
    if len(parts) >= 2 and parts[1] in _LAYER_MARKERS:
        item.add_marker(getattr(pytest.mark, parts[1]))
    if item.get_closest_marker("slow"):
        return
    fixturenames = set(getattr(item, "fixturenames", ()) or ())
    if fixturenames & _SLOW_FIXTURE_NAMES or path.name in _SLOW_MODULE_SUFFIXES:
        item.add_marker(pytest.mark.slow)


def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
) -> None:
    for item in items:
        try:
            path = Path(item.path).resolve()
            rel = path.relative_to(_TESTS_ROOT)
        except ValueError:
            continue
        _apply_path_markers(item, path, rel)
