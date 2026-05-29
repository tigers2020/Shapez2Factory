"""Layer 03 replay observability contract (output-only; not algorithm input)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, cast

from django_apps.asteroid_lab.layers.contracts.candidates import (
    Layer03ExpansionMetrics,
    Layer03SkipReason,
    RouteProbedBundleCandidate,
)
from django_apps.asteroid_lab.layers.contracts.layer_slugs import LAYER_03_RIM_MINING_BUNDLES

Layer03ObservabilitySlug = Literal["layer_03_rim_mining_bundles"]


@dataclass(frozen=True, slots=True)
class Layer03Observability:
    layer_slug: Layer03ObservabilitySlug
    skip_reason: Layer03SkipReason
    rim_anchor_count: int
    route_probe_attempt_count: int
    route_probe_succeeded_count: int
    normal_candidate_count: int
    diagnostic_rejected_count: int
    reject_reason_counts: tuple[tuple[str, int], ...]
    replay_pool_candidates: tuple[RouteProbedBundleCandidate, ...]


def sort_replay_pool_candidates(
    normal_candidates: Sequence[RouteProbedBundleCandidate],
) -> tuple[RouteProbedBundleCandidate, ...]:
    return tuple(
        sorted(
            normal_candidates,
            key=lambda entry: (
                entry.candidate.intrinsic_priority_rank,
                entry.candidate.anchor_coord[1],
                entry.candidate.anchor_coord[0],
                entry.candidate.equivalence_key,
                entry.candidate.candidate_id,
            ),
        )
    )


def build_layer03_observability(
    *,
    metrics: Layer03ExpansionMetrics,
    normal_candidates: tuple[RouteProbedBundleCandidate, ...],
) -> Layer03Observability:
    return Layer03Observability(
        layer_slug=cast(Layer03ObservabilitySlug, LAYER_03_RIM_MINING_BUNDLES),
        skip_reason=metrics.layer_skip_reason,
        rim_anchor_count=metrics.rim_anchor_count,
        route_probe_attempt_count=metrics.route_probe_attempt_count,
        route_probe_succeeded_count=metrics.route_probe_succeeded_count,
        normal_candidate_count=metrics.normal_candidate_count,
        diagnostic_rejected_count=metrics.diagnostic_rejected_count,
        reject_reason_counts=metrics.reject_reason_counts,
        replay_pool_candidates=sort_replay_pool_candidates(normal_candidates),
    )


def build_layer03_observability_for_test(
    *,
    skip_reason: Layer03SkipReason,
    rim_anchor_count: int = 0,
    route_probe_attempt_count: int = 0,
    route_probe_succeeded_count: int = 0,
    normal_candidate_count: int = 0,
    diagnostic_rejected_count: int = 0,
    reject_reason_counts: tuple[tuple[str, int], ...] = (),
    replay_pool_candidates: tuple[RouteProbedBundleCandidate, ...] = (),
) -> Layer03Observability:
    return Layer03Observability(
        layer_slug=cast(Layer03ObservabilitySlug, LAYER_03_RIM_MINING_BUNDLES),
        skip_reason=skip_reason,
        rim_anchor_count=rim_anchor_count,
        route_probe_attempt_count=route_probe_attempt_count,
        route_probe_succeeded_count=route_probe_succeeded_count,
        normal_candidate_count=normal_candidate_count,
        diagnostic_rejected_count=diagnostic_rejected_count,
        reject_reason_counts=reject_reason_counts,
        replay_pool_candidates=replay_pool_candidates,
    )


__all__ = [
    "Layer03Observability",
    "Layer03ObservabilitySlug",
    "build_layer03_observability",
    "build_layer03_observability_for_test",
    "sort_replay_pool_candidates",
]
