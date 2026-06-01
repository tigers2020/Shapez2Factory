"""Test helpers for RimBundleCandidateSet with Layer03Observability."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import (
    Layer03ExpansionMetrics,
    RimBundleCandidateSet,
    RouteProbedBundleCandidate,
    build_rim_bundle_candidate_set,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer03_observability import (
    build_layer03_observability,
)


def rim_bundle_candidate_set_for_test(
    *,
    normal_candidates: tuple[RouteProbedBundleCandidate, ...] = (),
    diagnostic_rejected_candidates: tuple[RouteProbedBundleCandidate, ...] = (),
    metrics: Layer03ExpansionMetrics | None = None,
) -> RimBundleCandidateSet:
    resolved_metrics = metrics if metrics is not None else Layer03ExpansionMetrics.empty()
    return build_rim_bundle_candidate_set(
        normal_candidates=normal_candidates,
        diagnostic_rejected_candidates=diagnostic_rejected_candidates,
        metrics=resolved_metrics,
        observability=build_layer03_observability(
            metrics=resolved_metrics,
            normal_candidates=normal_candidates,
        ),
    )


__all__ = ["rim_bundle_candidate_set_for_test"]
