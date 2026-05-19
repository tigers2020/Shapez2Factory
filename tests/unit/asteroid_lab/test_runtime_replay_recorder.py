"""RuntimeReplayRecorder overlay_cells preservation contract tests."""

from __future__ import annotations

import django_apps.asteroid_lab.services.runtime_replay_recorder as recorder_mod
from django_apps.asteroid_lab.optimization.enums import OptimizationReplayEventType
from django_apps.asteroid_lab.services.runtime_replay_recorder import RuntimeReplayRecorder


def _cells(n: int) -> tuple[dict, ...]:
    return tuple({"server_x": i, "server_y": 0, "cell_kind": "asteroid"} for i in range(n))


def test_no_truncation_when_within_limit() -> None:
    rec = RuntimeReplayRecorder()
    vis = _cells(10)
    ovl = _cells(5)
    rec.append(
        OptimizationReplayEventType.ROUTE_MATERIALIZED,
        title="t",
        visible_cells=vis,
        overlay_cells=ovl,
    )
    f = rec.frames()[0]
    assert len(f.visible_cells) == 10
    assert len(f.overlay_cells) == 5


def test_overlay_preserved_when_vis_plus_ovl_exceeds_cap() -> None:
    """overlay_cells must NOT be dropped when vis+ovl > cap — they carry the meaningful delta."""
    orig = recorder_mod.MAX_OPTIMIZATION_REPLAY_CELLS_PER_FRAME
    recorder_mod.MAX_OPTIMIZATION_REPLAY_CELLS_PER_FRAME = 20
    try:
        rec = RuntimeReplayRecorder(max_frames=500)
        vis = _cells(15)
        ovl = _cells(10)  # total 25 > 20
        rec.append(
            OptimizationReplayEventType.ROUTE_MATERIALIZED,
            title="t",
            visible_cells=vis,
            overlay_cells=ovl,
        )
    finally:
        recorder_mod.MAX_OPTIMIZATION_REPLAY_CELLS_PER_FRAME = orig

    f = rec.frames()[0]
    assert len(f.overlay_cells) == 10, "overlay_cells must be preserved in full (budget first)"
    assert len(f.visible_cells) == 10, "vis trimmed to cap - len(ovl)"
    assert len(f.visible_cells) + len(f.overlay_cells) == 20


def test_overlay_not_zeroed_when_visible_alone_equals_cap() -> None:
    """If vis alone == cap, adding any overlay must not silently discard overlay."""
    orig = recorder_mod.MAX_OPTIMIZATION_REPLAY_CELLS_PER_FRAME
    recorder_mod.MAX_OPTIMIZATION_REPLAY_CELLS_PER_FRAME = 10
    try:
        rec = RuntimeReplayRecorder(max_frames=500)
        vis = _cells(10)  # exactly cap
        ovl = _cells(5)   # total 15 > cap
        rec.append(
            OptimizationReplayEventType.ROUTE_MATERIALIZED,
            title="t",
            visible_cells=vis,
            overlay_cells=ovl,
        )
    finally:
        recorder_mod.MAX_OPTIMIZATION_REPLAY_CELLS_PER_FRAME = orig

    f = rec.frames()[0]
    assert len(f.overlay_cells) == 5, "overlay kept in full (fits within cap)"
    assert len(f.visible_cells) == 5, "vis budget = cap - len(ovl)"


def test_no_overlay_cells_truncates_visible_at_cap() -> None:
    """If overlay is empty, visible_cells are truncated normally at cap."""
    orig = recorder_mod.MAX_OPTIMIZATION_REPLAY_CELLS_PER_FRAME
    recorder_mod.MAX_OPTIMIZATION_REPLAY_CELLS_PER_FRAME = 10
    try:
        rec = RuntimeReplayRecorder(max_frames=500)
        vis = _cells(20)
        rec.append(
            OptimizationReplayEventType.ROUTE_MATERIALIZED,
            title="t",
            visible_cells=vis,
        )
    finally:
        recorder_mod.MAX_OPTIMIZATION_REPLAY_CELLS_PER_FRAME = orig

    f = rec.frames()[0]
    assert len(f.visible_cells) == 10
    assert len(f.overlay_cells) == 0
