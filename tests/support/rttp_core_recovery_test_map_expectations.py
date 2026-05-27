"""Derived expectations for ``tests/fixtures/asteroid_lab/test_map.txt`` recovery import.

Do not hardcode placement_goal_count or field cell counts in tests — derive from
``ReconstructionCompleteMap`` × ``placement_target_percent`` (Task 4 / recovery spec).
"""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.reconstruction.field_cells import (
    asteroid_field_cell_count_for_placement,
)
from django_apps.asteroid_lab.services.placement_goal import compute_placement_goal_count


def expected_placement_metrics_for_complete_map(
    complete_map: ReconstructionCompleteMap,
    transport_kind: TransportKind,
    *,
    placement_target_percent: int,
) -> tuple[int, int]:
    """Return ``(asteroid_field_cell_count, placement_goal_count)`` for recovery assertions."""

    platform = asteroid_field_cell_count_for_placement(complete_map, transport_kind)
    goal = compute_placement_goal_count(
        asteroid_field_cell_count=platform,
        placement_target_percent=placement_target_percent,
    )
    return platform, goal


__all__ = ["expected_placement_metrics_for_complete_map"]
