"""Shared fixtures for web integration tests."""

from __future__ import annotations

import pytest
from django.test import override_settings


@pytest.fixture(autouse=True)
def asteroid_lab_sync_run_solver(request: pytest.FixtureRequest):
    """Keep legacy integration tests on synchronous run-solver unless marked async."""

    if request.node.get_closest_marker("async_solver"):
        yield
        return
    with override_settings(ASTEROID_LAB_SOLVER_ASYNC_DEFAULT=False):
        yield


@pytest.fixture(autouse=True)
def _lab_replay_compose_cache_enabled_for_integration_tests(settings) -> None:
    """Keep compose-cache integration tests green when local ``.env`` disables cache."""

    settings.ASTEROID_LAB_REPLAY_COMPOSE_CACHE_ENABLED = True
