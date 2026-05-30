"""Shim: relocated to shapez2_factory.application.asteroid_lab.layers.contracts.candidates."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import (
    BundleCandidate,
    BundleCellRole,
    BundlePlacement,
    CandidateRejectReason,
    Layer03ExpansionMetrics,
    Layer03SkipReason,
    Layer03Slug,
    RimBundleCandidateSet,
    RouteProbedBundleCandidate,
    RouteProbeResult,
    RouteProbeStatus,
    build_rim_bundle_candidate_set,
    make_bundle_candidate_for_test,
)

__all__ = [
    "BundleCandidate",
    "BundleCellRole",
    "BundlePlacement",
    "CandidateRejectReason",
    "Layer03ExpansionMetrics",
    "Layer03SkipReason",
    "Layer03Slug",
    "RimBundleCandidateSet",
    "RouteProbeResult",
    "RouteProbeStatus",
    "RouteProbedBundleCandidate",
    "build_rim_bundle_candidate_set",
    "make_bundle_candidate_for_test",
]
