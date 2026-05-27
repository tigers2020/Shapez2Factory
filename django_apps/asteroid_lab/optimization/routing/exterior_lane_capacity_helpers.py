"""Pure ELCP helpers (no Django DB I/O)."""

from __future__ import annotations

from decimal import Decimal


def normalize_required_lane_count(
    *,
    max_asteroid_throughput_per_min: Decimal,
    lane_capacity_per_min: Decimal,
) -> int:
    """Ceildiv of map max throughput over saturated exterior lane capacity (ELCP-N1)."""

    if lane_capacity_per_min <= 0:
        return 0
    if max_asteroid_throughput_per_min <= 0:
        return 0
    quotient, remainder = divmod(max_asteroid_throughput_per_min, lane_capacity_per_min)
    lane_quotient = int(quotient)
    if remainder == 0:
        return lane_quotient
    return lane_quotient + 1


def lane_target_loads_per_min(
    *,
    max_asteroid_throughput_per_min: Decimal,
    lane_capacity_per_min: Decimal,
    required_lane_count: int,
) -> tuple[Decimal, ...]:
    """Per-lane target loads: full capacity except optional remainder on the last lane."""

    if required_lane_count <= 0:
        return ()
    if lane_capacity_per_min <= 0 or max_asteroid_throughput_per_min <= 0:
        return ()

    _, remainder = divmod(max_asteroid_throughput_per_min, lane_capacity_per_min)
    loads: list[Decimal] = []
    for index in range(required_lane_count):
        is_last = index == required_lane_count - 1
        if is_last and remainder != 0:
            loads.append(remainder)
        else:
            loads.append(lane_capacity_per_min)
    return tuple(loads)


__all__ = [
    "lane_target_loads_per_min",
    "normalize_required_lane_count",
]
