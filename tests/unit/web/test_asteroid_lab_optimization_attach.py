"""Lab run-solver optimization attach payload + replay compression."""

from __future__ import annotations

from django_apps.shapez_asteroid.optimization.dto import OptimizationReplayFrame
from django_apps.shapez_asteroid.optimization.enums import OptimizationReplayEventType
from django_apps.web.services.asteroid_lab_optimization_run import (
    _compress_rejected_candidate_replay_frames,
    build_optimization_replay_attach_payload,
)


def test_compress_rejected_candidate_replay_frames_adds_summary() -> None:
    et_rej = OptimizationReplayEventType.CANDIDATE_REJECTED
    et_in = OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED
    frames: list[OptimizationReplayFrame] = [
        OptimizationReplayFrame(
            frame_index=0,
            event_type=et_in,
            title="in",
            description="",
            visible_cells=(),
            overlay_cells=(),
            metrics={},
        )
    ]
    for i in range(30):
        frames.append(
            OptimizationReplayFrame(
                frame_index=1 + i,
                event_type=et_rej,
                title="rej",
                description="",
                visible_cells=(),
                overlay_cells=(),
                metrics={"candidate_reject_reason": "extension_not_mineable"},
            )
        )
    out = _compress_rejected_candidate_replay_frames(tuple(frames), max_detail=10)
    assert len(out) == 12
    assert out[0].event_type is et_in
    assert sum(1 for f in out if f.event_type is et_rej) == 11
    summary = out[-1]
    assert summary.metrics.get("lab_replay_compression") is True
    assert int(summary.metrics.get("omitted_candidate_rejected_frame_count") or 0) == 20


def test_build_optimization_replay_attach_payload_shape() -> None:
    dbg = {
        "reason": "empty_candidate_pool",
        "diagnostic": {
            "stage": "completed",
            "normal_candidate_count": 0,
            "rejected_candidate_count": 3,
            "reject_reason_counts": {"extension_not_mineable": 3},
        },
    }
    attach = build_optimization_replay_attach_payload(dbg)
    assert attach["reason"] == "empty_candidate_pool"
    assert attach["diagnostic"]["normal_candidate_count"] == 0
    assert attach["diagnostic"]["reject_reason_counts"]["extension_not_mineable"] == 3
