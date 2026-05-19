"""Phase C — capacity estimation for external RouteGoal counts (PR2.5)."""

from __future__ import annotations

import math
from dataclasses import dataclass

DEFAULT_AVG_GENE_FOOTPRINT = 5
SHAPE_PLATFORMS_PER_GOAL = 12
FLUID_PLATFORMS_PER_GOAL = 72


@dataclass(frozen=True, slots=True)
class CapacityPlan:
    """Throughput-based goal count estimates (no transport materialization)."""

    mineable_cell_count: int
    estimated_max_samples: int
    estimated_shape_platforms: int
    estimated_fluid_platforms: int
    shape_goal_count: int
    fluid_goal_count: int
    avg_gene_footprint: int
    shape_platforms_per_goal: int = SHAPE_PLATFORMS_PER_GOAL
    fluid_platforms_per_goal: int = FLUID_PLATFORMS_PER_GOAL


def plan_capacity(
    *,
    mineable_cell_count: int,
    shape_platform_count: int,
    fluid_platform_count: int,
    avg_gene_footprint: int = DEFAULT_AVG_GENE_FOOTPRINT,
) -> CapacityPlan:
    """Estimate sample budget and shape/fluid external goal counts (CANON 12 / 72)."""

    if avg_gene_footprint < 1:
        msg = "avg_gene_footprint must be >= 1"
        raise ValueError(msg)

    estimated_max_samples = mineable_cell_count // avg_gene_footprint
    shape_goals = math.ceil(shape_platform_count / SHAPE_PLATFORMS_PER_GOAL)
    fluid_goals = math.ceil(fluid_platform_count / FLUID_PLATFORMS_PER_GOAL)

    return CapacityPlan(
        mineable_cell_count=mineable_cell_count,
        estimated_max_samples=estimated_max_samples,
        estimated_shape_platforms=shape_platform_count,
        estimated_fluid_platforms=fluid_platform_count,
        shape_goal_count=shape_goals,
        fluid_goal_count=fluid_goals,
        avg_gene_footprint=avg_gene_footprint,
    )
