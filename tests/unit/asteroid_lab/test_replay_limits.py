"""Phase 9 pre-9B — replay limit constants align with product canon."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.replay_frame import (
    MAX_REPLAY_CELLS_PER_FRAME,
    MAX_REPLAY_FRAMES,
)
from django_apps.asteroid_lab.replay.replay_limits import (
    MAX_OPTIMIZATION_REPLAY_CELLS_PER_FRAME,
    MAX_OPTIMIZATION_REPLAY_FRAMES,
    MAX_UNIFIED_LAB_REPLAY_CELLS_PER_FRAME,
    MAX_UNIFIED_LAB_REPLAY_FRAMES,
)


def test_replay_limits_constants_match_canon_doc() -> None:
    assert MAX_OPTIMIZATION_REPLAY_FRAMES == 500
    assert MAX_OPTIMIZATION_REPLAY_CELLS_PER_FRAME == 2000
    assert MAX_UNIFIED_LAB_REPLAY_FRAMES == 500
    assert MAX_UNIFIED_LAB_REPLAY_CELLS_PER_FRAME == 2000
    assert MAX_REPLAY_FRAMES == MAX_OPTIMIZATION_REPLAY_FRAMES
    assert MAX_REPLAY_CELLS_PER_FRAME == MAX_OPTIMIZATION_REPLAY_CELLS_PER_FRAME
