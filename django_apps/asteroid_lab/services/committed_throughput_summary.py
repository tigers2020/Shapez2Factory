"""Route-confirmed committed platform throughput (PR-2b; never replay or summary input).

Invariant: each committed physical extractor bundle is counted exactly once via
``BundleCandidate.throughput_factor`` and ``MiningExtractionRule.output_per_min``.
Macro parent IDs are not summed when absent from ``candidates_by_id``.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.services.reconstruction_capacity_summary import decimal_str
from django_apps.game_data.services.mining_extraction_rules import get_active_rule, output_per_min


def resource_kind_for_transport(transport_kind: TransportKind) -> str:
    if transport_kind is TransportKind.SHAPE_BELT:
        return "shape"
    if transport_kind is TransportKind.FLUID_PIPE:
        return "fluid"
    msg = f"unsupported transport_kind={transport_kind!r}"
    raise ValueError(msg)


def build_actual_committed_output_per_min(
    *,
    committed_ids: tuple[str, ...],
    candidates_by_id: Mapping[str, BundleCandidate],
    transport_kind: TransportKind,
) -> str:
    """Sum per-minute output for route-confirmed committed bundle candidates."""

    rule = get_active_rule(resource_kind_for_transport(transport_kind))
    total = Decimal(0)
    for cid in committed_ids:
        candidate = candidates_by_id.get(cid)
        if candidate is None:
            continue
        total += output_per_min(rule, int(candidate.throughput_factor))
    return decimal_str(total)


__all__ = [
    "build_actual_committed_output_per_min",
    "resource_kind_for_transport",
]
