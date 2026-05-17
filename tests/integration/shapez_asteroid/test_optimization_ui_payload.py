"""Lab context exposes optimization replay envelope (Sequence 9B, DB-backed shell)."""

from __future__ import annotations

import pytest

from django_apps.shapez_asteroid.optimization.optimization_ui_payload import (
    OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY,
    empty_optimization_replay_track_payload,
)
from django_apps.web.services.asteroid_lab_page_context import lab_page_context


@pytest.mark.django_db
def test_lab_page_context_optimization_replay_matches_empty_payload_helper() -> None:
    ctx = lab_page_context()
    assert ctx[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY] == empty_optimization_replay_track_payload()
