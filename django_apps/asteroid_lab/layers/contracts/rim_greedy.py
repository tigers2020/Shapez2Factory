"""Shim: relocated to shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    LAYER_03_GREEDY_SOURCE,
    CommittedRimSeedPlacement,
    IntegratedRimGreedyResult,
    Layer03AppendResult,
    RimGreedyMetrics,
    RimGreedyObservationEvent,
    RimGreedyObservationPhase,
    RimGreedyPass2Report,
    RimGreedyPolicy,
    RimGreedyReject,
    RimGreedyRejectReason,
    RimGreedyScoreAtoms,
    _skip_observability_events,
    build_empty_integrated_rim_greedy_result,
)

__all__ = [
    "CommittedRimSeedPlacement",
    "IntegratedRimGreedyResult",
    "Layer03AppendResult",
    "LAYER_03_GREEDY_SOURCE",
    "RimGreedyMetrics",
    "RimGreedyObservationEvent",
    "RimGreedyObservationPhase",
    "RimGreedyPass2Report",
    "RimGreedyPolicy",
    "RimGreedyReject",
    "RimGreedyRejectReason",
    "RimGreedyScoreAtoms",
    "_skip_observability_events",
    "build_empty_integrated_rim_greedy_result",
]
