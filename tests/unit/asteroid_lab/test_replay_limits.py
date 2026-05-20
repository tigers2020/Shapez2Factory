"""Phase 9 pre-9B — replay limit constants align with product canon."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.replay_limits import (
    MAX_UNIFIED_LAB_REPLAY_CELLS_PER_FRAME,
    MAX_UNIFIED_LAB_REPLAY_FRAMES,
)


def test_replay_limits_constants_match_canon_doc() -> None:
    assert MAX_UNIFIED_LAB_REPLAY_FRAMES == 500
    assert MAX_UNIFIED_LAB_REPLAY_CELLS_PER_FRAME == 2000
