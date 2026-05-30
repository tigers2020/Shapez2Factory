"""Integer ceiling division for Decimal throughput rates."""

from __future__ import annotations

from decimal import ROUND_CEILING, Decimal


def ceildiv_decimal(numerator: Decimal, denominator: Decimal) -> int:
    if denominator <= 0 or numerator <= 0:
        return 0
    return int((numerator / denominator).to_integral_value(rounding=ROUND_CEILING))


__all__ = ["ceildiv_decimal"]
