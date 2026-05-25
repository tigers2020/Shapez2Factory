"""Queryable CANON extraction rates (L1b). No RTTP imports."""

from __future__ import annotations

from decimal import Decimal
from typing import cast

from django_apps.game_data.models.mining import MiningExtractionRule

VALID_THROUGHPUT_FACTORS: frozenset[int] = frozenset({4, 8, 12, 16})


def get_active_rule(resource_kind: str) -> MiningExtractionRule:
    row = MiningExtractionRule.objects.filter(
        resource_kind=resource_kind,
        is_active=True,
    ).first()
    if row is None:
        msg = f"no active MiningExtractionRule for resource_kind={resource_kind!r}"
        raise LookupError(msg)
    return row


def effective_mini_units(extension_count: int) -> int:
    if extension_count < 0 or extension_count > 3:
        msg = "extension_count must be in 0..3"
        raise ValueError(msg)
    return 4 + 4 * extension_count


def output_per_min(rule: MiningExtractionRule, throughput_factor: int) -> Decimal:
    if throughput_factor not in VALID_THROUGHPUT_FACTORS:
        msg = f"throughput_factor must be one of {sorted(VALID_THROUGHPUT_FACTORS)}"
        raise ValueError(msg)
    return cast(
        Decimal,
        rule.mini_unit_output_per_min * Decimal(throughput_factor),
    )


def max_output_per_miner(rule: MiningExtractionRule) -> Decimal:
    factor = effective_mini_units(int(rule.max_extension_count))
    return output_per_min(rule, factor)


def assert_throughput_factor_matches_extensions(
    throughput_factor: int,
    extension_count: int,
) -> None:
    if throughput_factor != effective_mini_units(extension_count):
        msg = (
            f"throughput_factor {throughput_factor} != " f"effective_mini_units({extension_count})"
        )
        raise ValueError(msg)
