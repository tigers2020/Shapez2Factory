"""Shared fixtures for ``tests/integration``."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def seed_miner_patterns_db(db: None) -> None:
    from django.core.management import call_command

    call_command("seed_miner_patterns", replace_stale=True)
