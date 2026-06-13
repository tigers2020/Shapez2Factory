"""Pytest configuration: path-based markers for selective test runs.

Markers are applied automatically from file location (no per-test decorators):
- unit / integration - top-level under tests/
- shapez_core / shapez_solver / web / api - second segment when present

Examples:
  pytest -m unit
  pytest -m integration
  pytest -m shapez_solver
  pytest -m "unit and shapez_core"
  pytest tests/integration/web/
"""

from __future__ import annotations

import os
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
    "test_solver_runtime_replay_recorder.py",
    "test_simulation_systems_import.py",
    "test_simulation_speed_import.py",
    "test_runtime_wire_serde.py",
    "test_runtime_wire_projection_compose.py",
)


@pytest.fixture(autouse=True)
def _ensure_space_transport_layout_registry(
    request: pytest.FixtureRequest,
    django_db_blocker,
    db: None,
) -> None:
    """Re-seed layouts after module fixtures flush game_data (macro-smoke / xdist safe)."""

    if request.node.get_closest_marker("django_db") is None:
        return

    from django_apps.game_data.models import SpaceTransportLayoutRegistry
    from django_apps.game_data.services.space_transport_layout_catalog import (
        EXPECTED_SPACE_TRANSPORT_LAYOUT_COUNT,
    )
    from tests.support.game_data_layout_seed import ensure_space_transport_layout_registry

    if SpaceTransportLayoutRegistry.objects.count() >= EXPECTED_SPACE_TRANSPORT_LAYOUT_COUNT:
        return
    with django_db_blocker.unblock():
        ensure_space_transport_layout_registry(strict=bool(os.environ.get("CI")))


def pytest_configure(config: pytest.Config) -> None:
    """pytest-django: reuse test DB when ``--reuse-db`` is available."""
    opt = config.option
    if getattr(opt, "create_db", False):
        return
    if hasattr(opt, "reuse_db"):
        opt.reuse_db = True


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
