"""Shim — relocated to ``shapez2_factory.domain.asteroid_lab.reconstruction.confidence`` (2f)."""

from __future__ import annotations

from shapez2_factory.domain.asteroid_lab.reconstruction.confidence import (
    QUALITY_TIER_AMBIGUOUS,
    QUALITY_TIER_CONFIDENT,
    QUALITY_TIER_FAILED,
    QUALITY_TIER_PARTIAL,
    apply_confidence_to_result,
    build_candidate_masks,
    compute_confidence_metrics,
    merge_mask_agreement,
    quality_tier_from_metrics,
    reconstruction_acceptance_ok,
    reconstruction_persist_summary,
)

__all__ = [
    "QUALITY_TIER_AMBIGUOUS",
    "QUALITY_TIER_CONFIDENT",
    "QUALITY_TIER_FAILED",
    "QUALITY_TIER_PARTIAL",
    "apply_confidence_to_result",
    "build_candidate_masks",
    "compute_confidence_metrics",
    "merge_mask_agreement",
    "quality_tier_from_metrics",
    "reconstruction_acceptance_ok",
    "reconstruction_persist_summary",
]
