"""Golden asteroid L4 capacity / inner-fill target metrics (measurement only).

Separates:
- Golden Valid Minimum Guard (regression floor, see ``golden_valid_baseline``)
- L4 inner-fill target (remaining inner capacity fill ratio)

Criterion B (canon for golden 578-field map):
  inner target = ceil(inner_max_group_sets * MIN_INNER_FILL_RATIO)
  total routeable target = rim_baseline + inner target
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_solver_run import (
    GoldenSolverArtifacts,
)

# Golden empty.shapez.txt reconstructed field (shape resource on 578-field asteroid).
CANONICAL_GOLDEN_FIELD_COUNT = 578
FIELD_CELLS_PER_GROUP_SET = 4
MIN_INNER_FILL_RATIO = 0.80

# Rim-only valid regression baseline (L3 committed placements / L5 sources today).
RIM_BASELINE_GROUP_COUNT = 76


@dataclass(frozen=True, slots=True)
class GoldenL4CapacityMetrics:
    total_field_count: int
    max_group_sets: int
    rim_group_count: int
    routeable_group_count: int
    inner_routeable_group_count: int
    l4_interior_occupied_cell_count: int
    l4_interior_group_set_equivalent: int
    inner_max_group_sets: int
    min_inner_group_sets_target: int
    min_total_routeable_target: int
    total_fill_ratio: float
    inner_routeable_fill_ratio: float
    l4_cell_fill_ratio_of_inner_max: float
    meets_l4_inner_target_b: bool
    routeable_gap_to_target_b: int


def max_group_sets_for_field_count(field_count: int) -> int:
    return field_count // FIELD_CELLS_PER_GROUP_SET


def min_inner_group_sets_target(inner_max_group_sets: int) -> int:
    return math.ceil(inner_max_group_sets * MIN_INNER_FILL_RATIO)


def compute_golden_l4_capacity_metrics(
    artifacts: GoldenSolverArtifacts,
) -> GoldenL4CapacityMetrics:
    total_field_count = len(artifacts.complete_map.field_cells)
    max_group_sets = max_group_sets_for_field_count(total_field_count)

    rim_group_count = (
        len(artifacts.rim_result.committed_placements) if artifacts.rim_result is not None else 0
    )
    routeable_group_count = (
        artifacts.route_plan.metrics.source_count if artifacts.route_plan is not None else 0
    )
    inner_routeable_group_count = max(0, routeable_group_count - rim_group_count)

    l4_interior_occupied_cell_count = 0
    if artifacts.inner_fill is not None:
        l4_interior_occupied_cell_count = artifacts.inner_fill.metrics.interior_occupied_cell_count

    l4_interior_group_set_equivalent = l4_interior_occupied_cell_count // FIELD_CELLS_PER_GROUP_SET
    inner_max_group_sets = max(0, max_group_sets - rim_group_count)
    min_inner_target = min_inner_group_sets_target(inner_max_group_sets)
    min_total_target = rim_group_count + min_inner_target

    total_fill_ratio = routeable_group_count / max_group_sets if max_group_sets > 0 else 0.0
    inner_routeable_fill_ratio = (
        inner_routeable_group_count / inner_max_group_sets if inner_max_group_sets > 0 else 0.0
    )
    l4_cell_fill_ratio_of_inner_max = (
        l4_interior_group_set_equivalent / inner_max_group_sets if inner_max_group_sets > 0 else 0.0
    )

    return GoldenL4CapacityMetrics(
        total_field_count=total_field_count,
        max_group_sets=max_group_sets,
        rim_group_count=rim_group_count,
        routeable_group_count=routeable_group_count,
        inner_routeable_group_count=inner_routeable_group_count,
        l4_interior_occupied_cell_count=l4_interior_occupied_cell_count,
        l4_interior_group_set_equivalent=l4_interior_group_set_equivalent,
        inner_max_group_sets=inner_max_group_sets,
        min_inner_group_sets_target=min_inner_target,
        min_total_routeable_target=min_total_target,
        total_fill_ratio=total_fill_ratio,
        inner_routeable_fill_ratio=inner_routeable_fill_ratio,
        l4_cell_fill_ratio_of_inner_max=l4_cell_fill_ratio_of_inner_max,
        meets_l4_inner_target_b=routeable_group_count >= min_total_target,
        routeable_gap_to_target_b=max(0, min_total_target - routeable_group_count),
    )


def format_l4_capacity_diagnostics(metrics: GoldenL4CapacityMetrics) -> tuple[str, ...]:
    return (
        f"l4_capacity:field_count={metrics.total_field_count}",
        f"l4_capacity:max_group_sets={metrics.max_group_sets}",
        f"l4_capacity:rim_group_count={metrics.rim_group_count}",
        f"l4_capacity:routeable_group_count={metrics.routeable_group_count}",
        f"l4_capacity:inner_routeable_group_count={metrics.inner_routeable_group_count}",
        ("l4_capacity:l4_interior_occupied_cells=" f"{metrics.l4_interior_occupied_cell_count}"),
        (
            "l4_capacity:l4_interior_group_set_equivalent="
            f"{metrics.l4_interior_group_set_equivalent}"
        ),
        f"l4_capacity:inner_max_group_sets={metrics.inner_max_group_sets}",
        f"l4_capacity:min_inner_group_sets_target={metrics.min_inner_group_sets_target}",
        f"l4_capacity:min_total_routeable_target={metrics.min_total_routeable_target}",
        f"l4_capacity:total_fill_ratio={metrics.total_fill_ratio:.4f}",
        f"l4_capacity:inner_routeable_fill_ratio={metrics.inner_routeable_fill_ratio:.4f}",
        (
            "l4_capacity:l4_cell_fill_ratio_of_inner_max="
            f"{metrics.l4_cell_fill_ratio_of_inner_max:.4f}"
        ),
        f"l4_capacity:meets_inner_target_b={metrics.meets_l4_inner_target_b}",
        f"l4_capacity:routeable_gap_to_target_b={metrics.routeable_gap_to_target_b}",
    )


__all__ = [
    "CANONICAL_GOLDEN_FIELD_COUNT",
    "FIELD_CELLS_PER_GROUP_SET",
    "GoldenL4CapacityMetrics",
    "MIN_INNER_FILL_RATIO",
    "RIM_BASELINE_GROUP_COUNT",
    "compute_golden_l4_capacity_metrics",
    "format_l4_capacity_diagnostics",
    "max_group_sets_for_field_count",
    "min_inner_group_sets_target",
]
