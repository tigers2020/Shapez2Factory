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
