"""ELCP-TM shared trunk state and path partition helpers."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from django_apps.asteroid_lab.contracts.exterior_lane_capacity import (
    ExteriorLaneCapacityPlan,
    ExteriorLaneTrunkState,
)
from django_apps.asteroid_lab.optimization.coords import Coord


def initial_trunk_states(plan: ExteriorLaneCapacityPlan) -> tuple[ExteriorLaneTrunkState, ...]:
    """One trunk state row per plan lane; only index 0 starts active when lanes exist."""

    return tuple(
        ExteriorLaneTrunkState(
            lane_id=lane.lane_id,
            transport_kind=lane.transport_kind,
            active=index == 0 and plan.required_lane_count > 0,
            assigned_load_per_min=Decimal("0"),
            trunk_cells=frozenset(),
            connector_coord=lane.connector_goal.coord,
        )
        for index, lane in enumerate(plan.lanes)
    )


def partition_path_branch_and_trunk(
    *,
    path: tuple[Coord, ...],
    existing_trunk: frozenset[Coord],
    connector_coord: Coord,
) -> tuple[tuple[Coord, ...], tuple[Coord, ...], tuple[Coord, ...]]:
    """Split probe path into branch (new), reused trunk hits, and new trunk cells.

    First commit on a lane (empty ``existing_trunk``): all path cells establish trunk;
    ``branch`` is empty.

    Later commits: ``branch`` is the path prefix until the first cell already in trunk;
    ``reused`` is trunk cells visited in path order; ``new_trunk`` is empty in v0 when
    reusing (branch-only delta — no promotion of branch into trunk on reuse commits).

    ``connector_coord`` is reserved for callers that validate goal reach; partition
    uses path membership only.
    """

    _ = connector_coord
    if not path:
        return (), (), ()

    reused = tuple(cell for cell in path if cell in existing_trunk)
    if not existing_trunk:
        return (), (), path

    branch: list[Coord] = []
    for cell in path:
        if cell in existing_trunk:
            break
        branch.append(cell)
    return tuple(branch), reused, ()


def shareable_trunk_cells_from_states(
    states: tuple[ExteriorLaneTrunkState, ...],
) -> frozenset[Coord]:
    """Union of active lane trunk cells (same transport_kind per lane row)."""

    merged: set[Coord] = set()
    for state in states:
        if state.active:
            merged.update(state.trunk_cells)
    return frozenset(merged)


def update_trunk_state_after_commit(
    state: ExteriorLaneTrunkState,
    *,
    new_trunk_cells: tuple[Coord, ...],
    assigned_delta: Decimal,
) -> ExteriorLaneTrunkState:
    """Append new trunk geometry and throughput after a successful commit."""

    return replace(
        state,
        trunk_cells=frozenset(state.trunk_cells | frozenset(new_trunk_cells)),
        assigned_load_per_min=state.assigned_load_per_min + assigned_delta,
    )


def activate_trunk_state(state: ExteriorLaneTrunkState) -> ExteriorLaneTrunkState:
    """Mark a plan lane active for fill-first probing."""

    return replace(state, active=True)


__all__ = [
    "activate_trunk_state",
    "initial_trunk_states",
    "partition_path_branch_and_trunk",
    "shareable_trunk_cells_from_states",
    "update_trunk_state_after_commit",
]
