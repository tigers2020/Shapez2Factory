"""Pytest configuration: path-based markers for selective test runs.

Markers are applied automatically from file location (no per-test decorators):
- unit / integration — top-level under tests/
- shapez_core / shapez_solver / shapez_asteroid / web / api — second segment when present

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

_TESTS_ROOT = Path(__file__).resolve().parent

_LAYER_MARKERS = frozenset(
    {"shapez_core", "shapez_solver", "shapez_asteroid", "web", "api", "asteroid_lab"}
)


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
