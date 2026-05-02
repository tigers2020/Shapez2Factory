from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from functools import reduce
from math import gcd, lcm

from django_apps.shapez_core.domain.shape import Shape, ShapeLayer, ShapePart

FULL_SOURCE_CAPACITY = 4


@dataclass(frozen=True, slots=True)
class BaseDemand:
    base_shape_code: str
    quadrants_per_target: int
    total_quadrants: int
    full_source_count: int


@dataclass(frozen=True, slots=True)
class FactoryBatch:
    target_count: int
    base_demands: tuple[BaseDemand, ...]

    @property
    def base_source_counts(self) -> dict[str, int]:
        return {demand.base_shape_code: demand.full_source_count for demand in self.base_demands}

    @property
    def per_target_needs(self) -> dict[str, int]:
        return {demand.base_shape_code: demand.quadrants_per_target for demand in self.base_demands}


class UnsupportedFactoryDemandError(Exception):
    """Raised when factory demand computation is outside the current batch scope."""


def compute_base_demands(target: Shape, target_count: int) -> tuple[BaseDemand, ...]:
    batch = compute_factory_batch(target, requested_target_count=target_count, auto_balance=False)
    return batch.base_demands


def compute_factory_batch(
    target: Shape,
    *,
    requested_target_count: int | None = None,
    auto_balance: bool = True,
) -> FactoryBatch:
    needs = _per_target_needs(target)
    minimal_target_count = minimal_balanced_target_count(needs)

    if requested_target_count is None:
        target_count = minimal_target_count if auto_balance else 1
    else:
        if requested_target_count < 1:
            raise ValueError("target_count must be greater than or equal to 1")
        if auto_balance:
            target_count = _round_up_to_multiple(requested_target_count, minimal_target_count)
        else:
            target_count = requested_target_count

    demands = tuple(
        BaseDemand(
            base_shape_code=base_shape_code,
            quadrants_per_target=quadrants_per_target,
            total_quadrants=quadrants_per_target * target_count,
            full_source_count=(quadrants_per_target * target_count) // FULL_SOURCE_CAPACITY,
        )
        for base_shape_code, quadrants_per_target in needs
    )
    return FactoryBatch(target_count=target_count, base_demands=demands)


def minimal_balanced_target_count(
    per_target_needs: tuple[tuple[str, int], ...],
) -> int:
    factors = [
        FULL_SOURCE_CAPACITY // gcd(FULL_SOURCE_CAPACITY, quadrants_per_target)
        for _, quadrants_per_target in per_target_needs
    ]
    return reduce(lcm, factors, 1)


def _per_target_needs(target: Shape) -> tuple[tuple[str, int], ...]:
    _validate_target(target)
    skeleton = _uncolored_skeleton(target)
    counts = Counter(part.kind for part in skeleton.non_empty_parts())
    return tuple(
        sorted(
            (
                (_full_source_code(kind), quadrants_per_target)
                for kind, quadrants_per_target in counts.items()
            ),
            key=lambda item: item[0],
        )
    )


def _validate_target(target: Shape) -> None:
    if not target.is_single_layer():
        raise UnsupportedFactoryDemandError(
            "Factory demand MVP supports single-layer targets only."
        )
    if target.has_unsupported_materials():
        raise UnsupportedFactoryDemandError(
            "Factory demand MVP does not support pin or crystal targets."
        )


def _round_up_to_multiple(value: int, factor: int) -> int:
    return ((value + factor - 1) // factor) * factor


def _uncolored_skeleton(target: Shape) -> Shape:
    layer = target.layers[0]
    quadrants = tuple(_uncolored_part(part) for part in layer.quadrants)
    return Shape(
        layers=(
            ShapeLayer(
                quadrants=(quadrants[0], quadrants[1], quadrants[2], quadrants[3]),
            ),
        )
    )


def _uncolored_part(part: ShapePart) -> ShapePart:
    if part.is_empty:
        return part
    return ShapePart(kind=part.kind, color="u", material=part.material)


def _full_source_code(kind: str) -> str:
    return f"{kind}u" * FULL_SOURCE_CAPACITY


__all__ = [
    "BaseDemand",
    "FactoryBatch",
    "UnsupportedFactoryDemandError",
    "compute_base_demands",
    "compute_factory_batch",
    "minimal_balanced_target_count",
]
