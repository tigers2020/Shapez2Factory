"""EVTC required exterior connector count (ceildiv over DB-derived transport cap)."""

from __future__ import annotations

from decimal import Decimal

from django_apps.asteroid_lab.contracts.rttp_exterior_throughput_tier import (
    ExteriorThroughputTier,
)
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.services.rttp_exterior_transport_resolver import (
    transport_max_throughput_per_min,
)


def required_external_connectors(
    *,
    max_asteroid_throughput_per_min: Decimal,
    transport_kind: TransportKind,
    tier: ExteriorThroughputTier = ExteriorThroughputTier.TIER_1,
) -> int:
    transport_cap = transport_max_throughput_per_min(transport_kind, tier=tier)
    if transport_cap <= 0:
        return 0
    if max_asteroid_throughput_per_min <= 0:
        return 0
    quotient, remainder = divmod(max_asteroid_throughput_per_min, transport_cap)
    return int(quotient) if remainder == 0 else int(quotient) + 1


__all__ = ["required_external_connectors"]
