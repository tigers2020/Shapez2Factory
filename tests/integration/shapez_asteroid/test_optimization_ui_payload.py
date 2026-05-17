"""Lab page context no longer exposes a parallel optimization replay payload."""

from __future__ import annotations

import pytest

from django_apps.web.services.asteroid_lab_page_context import lab_page_context


@pytest.mark.django_db
def test_lab_page_context_has_no_parallel_optimization_replay_key() -> None:
    ctx = lab_page_context()
    assert "optimization_replay" not in ctx
