"""Layer 04 inner pattern fill contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from shapez2_factory.domain.asteroid_lab.grid_contract import Coord

PATTERN_BUILTIN_1X1_FIELD_BLOCK = "builtin_1x1_field_block"


class Layer04SkipReason(StrEnum):
    NO_CANDIDATES = "no_candidates"
    BUDGET_EXHAUSTED = "budget_exhausted"
    MACRO_ONLY_DEFERRED = "macro_only_deferred"


@dataclass(frozen=True, slots=True)
class InnerPlacement:
    coord: Coord
    pattern_id: str
    rotation: int = 0


@dataclass(frozen=True, slots=True)
class RouteableInnerGroupPlacement:
    """L4 committed inner miner group consumable by L5 source adapter."""

    placement_id: str
    anchor: Coord
    miner_cells: frozenset[Coord]
    extension_cells: frozenset[Coord]
    m_output_stub: Coord
    throughput_factor: int


@dataclass(frozen=True, slots=True)
class Layer04FillMetrics:
    interior_occupied_cell_count: int
    coverage_ratio: float
    corridor_risk: float = 0.0
    fragment_penalty: float = 0.0
    budget_interrupted: bool = False


@dataclass(frozen=True, slots=True)
class Layer04InnerFillResult:
    interior_occupied_cells: frozenset[Coord] = frozenset()
    placements: tuple[InnerPlacement, ...] = ()
    routeable_inner_groups: tuple[RouteableInnerGroupPlacement, ...] = ()
    metrics: Layer04FillMetrics | None = None
    skip_reason: Layer04SkipReason | None = None
    corridor_shadow_cells: frozenset[Coord] = frozenset()

    @classmethod
    def empty(cls) -> Layer04InnerFillResult:
        return cls(
            interior_occupied_cells=frozenset(),
            placements=(),
            metrics=Layer04FillMetrics(
                interior_occupied_cell_count=0,
                coverage_ratio=0.0,
            ),
            skip_reason=None,
            corridor_shadow_cells=frozenset(),
        )


__all__ = [
    "PATTERN_BUILTIN_1X1_FIELD_BLOCK",
    "InnerPlacement",
    "Layer04FillMetrics",
    "Layer04InnerFillResult",
    "Layer04SkipReason",
    "RouteableInnerGroupPlacement",
]
