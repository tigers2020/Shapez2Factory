from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from functools import reduce
from math import gcd, lcm

from django_apps.shapez_core.domain.shape import QUADRANT_COUNT, Shape, ShapeLayer, ShapePart

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


def compute_base_demands(target: Shape) -> tuple[BaseDemand, ...]:
    return compute_factory_batch(target).base_demands


def inventory_search_goal_shape_code(target: Shape) -> str:
    """Primitive search는 색을 바꾸지 않으므로, 목표 코드는 무채색 골격과 맞춘다."""

    return _uncolored_skeleton(target).canonical_code


def inventory_search_rejects_target_for_missing_paint(target: Shape) -> bool:
    """painter 없는 인벤토리 탐색에서, 단일 종류·단일 비-u 색만 있는 풀 레이어는 불가."""

    if not target.is_single_layer():
        return False
    layer = target.layers[0]
    nonempty = tuple(part for part in layer.quadrants if not part.is_empty)
    if len(nonempty) != QUADRANT_COUNT:
        return False
    kinds = {part.kind for part in nonempty}
    colors = {part.color for part in nonempty}
    if len(kinds) != 1 or len(colors) != 1:
        return False
    (only_color,) = colors
    if only_color == "u":
        return False
    return inventory_search_goal_shape_code(target) != target.canonical_code


def compute_factory_batch(target: Shape) -> FactoryBatch:
    needs = _per_target_needs(target)
    target_count = minimal_balanced_target_count(needs)

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
    "inventory_search_goal_shape_code",
    "inventory_search_rejects_target_for_missing_paint",
    "minimal_balanced_target_count",
]
