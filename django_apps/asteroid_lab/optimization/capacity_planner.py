"""Phase C — capacity estimation for external RouteGoal counts (PR2.5)."""

from __future__ import annotations

import math
from dataclasses import dataclass

PLATFORM_FOOTPRINT_CELLS = 5
DEFAULT_MINEABLE_PACKING_EFFICIENCY = 0.75
SHAPE_PLATFORMS_PER_GOAL = 12
FLUID_PLATFORMS_PER_GOAL = 72
MAX_SHAPE_GOALS = 8
MIN_SHAPE_GOALS_WHEN_ACTIVE = 2
EXTRACTOR_GROUPS_PER_SHAPE_GOAL_CAP = 2

# Back-compat alias (OD-2 footprint heuristic, not a game rule).
DEFAULT_AVG_GENE_FOOTPRINT = PLATFORM_FOOTPRINT_CELLS


@dataclass(frozen=True, slots=True)
class CapacityPlan:
    """Throughput-based goal count estimates (no transport materialization)."""

    mineable_cell_count: int
    estimated_extractor_groups: int
    shape_goal_count: int
    fluid_goal_count: int
    packing_efficiency: float
    platform_footprint_cells: int
    fluid_platform_count: int = 0
    shape_platforms_per_goal: int = SHAPE_PLATFORMS_PER_GOAL
    fluid_platforms_per_goal: int = FLUID_PLATFORMS_PER_GOAL

    @property
    def estimated_max_samples(self) -> int:
        """Deprecated alias for ``estimated_extractor_groups``."""

        return self.estimated_extractor_groups

    @property
    def estimated_shape_platforms(self) -> int:
        """Alias: shape capacity uses the same extractor-group estimate."""

        return self.estimated_extractor_groups


def _shape_goal_count(estimated_extractor_groups: int) -> int:
    """Throughput-based goals capped by extractor scale (avoid goal pile-up)."""

    if estimated_extractor_groups <= 0:
        return 0
    throughput = math.ceil(estimated_extractor_groups / SHAPE_PLATFORMS_PER_GOAL)
    extractor_scaled = estimated_extractor_groups * EXTRACTOR_GROUPS_PER_SHAPE_GOAL_CAP
    blended = min(throughput, extractor_scaled)
    return min(
        MAX_SHAPE_GOALS,
        max(MIN_SHAPE_GOALS_WHEN_ACTIVE, blended),
    )


def plan_capacity(
    *,
    mineable_cell_count: int,
    fluid_platform_count: int = 0,
    packing_efficiency: float = DEFAULT_MINEABLE_PACKING_EFFICIENCY,
    platform_footprint_cells: int = PLATFORM_FOOTPRINT_CELLS,
) -> CapacityPlan:
    """Estimate extractor groups and external shape/fluid goal counts (CANON 12 / 72)."""

    if platform_footprint_cells < 1:
        msg = "platform_footprint_cells must be >= 1"
        raise ValueError(msg)
    if not (0.0 < packing_efficiency <= 1.0):
        msg = "packing_efficiency must be in (0, 1]"
        raise ValueError(msg)

    estimated_extractor_groups = int(
        math.floor(
            mineable_cell_count * packing_efficiency / platform_footprint_cells
        )
    )
    shape_goals = _shape_goal_count(estimated_extractor_groups)
    fluid_goals = math.ceil(fluid_platform_count / FLUID_PLATFORMS_PER_GOAL)

    return CapacityPlan(
        mineable_cell_count=mineable_cell_count,
        estimated_extractor_groups=estimated_extractor_groups,
        shape_goal_count=shape_goals,
        fluid_goal_count=fluid_goals,
        packing_efficiency=packing_efficiency,
        platform_footprint_cells=platform_footprint_cells,
        fluid_platform_count=fluid_platform_count,
    )
