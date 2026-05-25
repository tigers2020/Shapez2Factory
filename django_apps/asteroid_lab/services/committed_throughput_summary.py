"""Route-confirmed committed platform throughput (PR-2b; never replay or summary input).

Invariant: each committed physical extractor bundle is counted exactly once via
``BundleCandidate.throughput_factor`` and ``MiningExtractionRule.output_per_min``.
Macro parent IDs are not summed when absent from ``candidates_by_id``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.services.reconstruction_capacity_summary import decimal_str


def resource_kind_for_transport(transport_kind: TransportKind) -> str:
    if transport_kind is TransportKind.SHAPE_BELT:
        return "shape"
    if transport_kind is TransportKind.FLUID_PIPE:
        return "fluid"
    msg = f"unsupported transport_kind={transport_kind!r}"
    raise ValueError(msg)


def collect_committed_throughput_factors(
    *,
    committed_ids: tuple[str, ...],
    candidates_by_id: Mapping[str, BundleCandidate],
) -> tuple[int, ...]:
    """Throughput factors from committed candidates only (no DB; safe inside pipeline)."""

    return tuple(
        int(candidates_by_id[cid].throughput_factor)
        for cid in committed_ids
        if cid in candidates_by_id
    )


def best_bundle_output_per_min_from_factors(
    *,
    throughput_factors: Sequence[int],
    transport_kind: TransportKind,
) -> Decimal:
    """Max per-bundle output/min for placement goal sizing (PR-2d)."""

    if not throughput_factors:
        return Decimal(0)
    from django_apps.game_data.services.mining_extraction_rules import (
        get_active_rule,
        output_per_min,
    )

    rule = get_active_rule(resource_kind_for_transport(transport_kind))
    return max(output_per_min(rule, int(factor)) for factor in throughput_factors)


def build_actual_committed_output_per_min_from_factors(
    *,
    throughput_factors: tuple[int, ...],
    transport_kind: TransportKind,
) -> str:
    """Sum per-minute output; requires active MiningExtractionRule (call from runtime entry)."""

    from django_apps.game_data.services.mining_extraction_rules import (
        get_active_rule,
        output_per_min,
    )

    rule = get_active_rule(resource_kind_for_transport(transport_kind))
    total = Decimal(0)
    for factor in throughput_factors:
        total += output_per_min(rule, factor)
    return decimal_str(total)


def build_actual_committed_output_per_min(
    *,
    committed_ids: tuple[str, ...],
    candidates_by_id: Mapping[str, BundleCandidate],
    transport_kind: TransportKind,
) -> str:
    """Sum per-minute output for route-confirmed committed bundle candidates."""

    factors = collect_committed_throughput_factors(
        committed_ids=committed_ids,
        candidates_by_id=candidates_by_id,
    )
    return build_actual_committed_output_per_min_from_factors(
        throughput_factors=factors,
        transport_kind=transport_kind,
    )


__all__ = [
    "best_bundle_output_per_min_from_factors",
    "build_actual_committed_output_per_min",
    "build_actual_committed_output_per_min_from_factors",
    "collect_committed_throughput_factors",
    "resource_kind_for_transport",
]
