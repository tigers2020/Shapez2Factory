"""Deterministic RTTP skeleton builder (Layer 1)."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import (
    LiftColumn,
    OptimizationInput,
    RingPort,
    RttpSkeletonConfig,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.skeleton.ring_builder import (
    RingOption,
    RingVariant,
    build_ring_options,
)
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton
from django_apps.asteroid_lab.snapshots.grid_contract import neighbors4

# CANON throughput heuristics — see shapez2_asteroid_space_transport_throughput.md
CELLS_PER_PLATFORM_ESTIMATE = 5
PLATFORM_ESTIMATE_RATIO = 0.75
SHAPE_PLATFORMS_PER_GOAL = 12
FLUID_PLATFORMS_PER_GOAL = 72
LANE_COUNT = 12

_DIR_DELTAS: dict[str, Coord] = {
    "N": (0, -1),
    "E": (1, 0),
    "S": (0, 1),
    "W": (-1, 0),
}


@dataclass(frozen=True, slots=True)
class _ScoredSkeleton:
    skeleton: RttpSkeleton
    score: float


class RttpSkeletonBuilder:
    @staticmethod
    def build(inp: OptimizationInput, *, config: RttpSkeletonConfig) -> RttpSkeleton:
        base_inner = _resolve_inner_cells(inp)
        ring_options = build_ring_options(inp.mineable_cells)
        scored = [_score_option(inp, config, option, base_inner) for option in ring_options]
        scored.sort(key=lambda item: (-item.score, item.skeleton.skeleton_id))
        return scored[0].skeleton


def _resolve_inner_cells(inp: OptimizationInput) -> frozenset[Coord]:
    if inp.inner_cells:
        return inp.inner_cells
    return inp.mineable_cells - inp.rim_cells - inp.protected_corridor_cells


def _score_option(
    inp: OptimizationInput,
    config: RttpSkeletonConfig,
    option: RingOption,
    base_inner: frozenset[Coord],
) -> _ScoredSkeleton:
    inner_cells = base_inner - option.ring_cells - inp.protected_corridor_cells
    ring_ports = _ring_ports(option.ring_cells, inp.external_void_cells)
    lift_columns = _lift_columns(inp.rim_cells, option.ring_cells)
    # P1 map class: merge ring spine with same-kind existing trunk; strip incompatible (B2-T3).
    incompatible = inp.blocked_incompatible_transport_cells
    trunk_mask_cells = frozenset((option.ring_cells | inp.existing_trunk_cells) - incompatible)
    capacity_goals = _capacity_goals(inp)
    skeleton_id = _skeleton_id(
        option.variant,
        option.ring_cells,
        ring_ports,
        lift_columns,
        trunk_mask_cells,
        inner_cells,
        capacity_goals,
    )
    port_accessibility = _port_accessibility(ring_ports, inp.external_void_cells)
    score = (
        config.w_inner * len(inner_cells)
        + config.w_port * port_accessibility
        - config.w_ring * len(option.ring_cells)
    )
    skeleton = RttpSkeleton(
        ring_cells=option.ring_cells,
        ring_ports=ring_ports,
        lift_columns=lift_columns,
        trunk_mask_cells=trunk_mask_cells,
        capacity_goals=capacity_goals,
        inner_cells=inner_cells,
        skeleton_id=skeleton_id,
    )
    return _ScoredSkeleton(skeleton=skeleton, score=score)


def _capacity_goals(inp: OptimizationInput) -> int:
    if inp.required_external_connector_count is not None:
        return max(0, inp.required_external_connector_count)
    mineable_count = len(inp.mineable_cells)
    platforms = math.floor(mineable_count * PLATFORM_ESTIMATE_RATIO / CELLS_PER_PLATFORM_ESTIMATE)
    if inp.transport_kind is TransportKind.FLUID_PIPE:
        divisor = FLUID_PLATFORMS_PER_GOAL
    else:
        divisor = SHAPE_PLATFORMS_PER_GOAL
    if platforms <= 0:
        return 0
    return math.ceil(platforms / divisor)


def _ring_ports(
    ring_cells: frozenset[Coord],
    external_void_cells: frozenset[Coord],
) -> tuple[RingPort, ...]:
    ports: list[RingPort] = []
    for coord in sorted(ring_cells):
        for direction, delta in _DIR_DELTAS.items():
            neighbor = (coord[0] + delta[0], coord[1] + delta[1])
            if neighbor in external_void_cells:
                ports.append(RingPort(coord=coord, preferred_dir=direction))
    return tuple(ports)


def _port_accessibility(
    ring_ports: tuple[RingPort, ...],
    external_void_cells: frozenset[Coord],
) -> int:
    accessible = 0
    for port in ring_ports:
        delta = _DIR_DELTAS[port.preferred_dir]
        neighbor = (port.coord[0] + delta[0], port.coord[1] + delta[1])
        if neighbor in external_void_cells:
            accessible += 1
    return accessible


def _lift_columns(
    rim_cells: frozenset[Coord],
    ring_cells: frozenset[Coord],
) -> tuple[LiftColumn, ...]:
    if not rim_cells or not ring_cells:
        return ()
    columns: list[LiftColumn] = []
    for index, platform in enumerate(sorted(rim_cells)):
        lift_coord = _nearest_ring_cell(platform, ring_cells)
        if lift_coord is None:
            continue
        columns.append(
            LiftColumn(
                platform_coord=platform,
                lift_coord=lift_coord,
                target_lane=index % LANE_COUNT,
            )
        )
    return tuple(columns)


def _nearest_ring_cell(platform: Coord, ring_cells: frozenset[Coord]) -> Coord | None:
    candidates = [neighbor for neighbor in neighbors4(platform) if neighbor in ring_cells]
    if not candidates:
        return None
    return min(candidates)


def _skeleton_id(
    variant: RingVariant,
    ring_cells: frozenset[Coord],
    ring_ports: tuple[RingPort, ...],
    lift_columns: tuple[LiftColumn, ...],
    trunk_mask_cells: frozenset[Coord],
    inner_cells: frozenset[Coord],
    capacity_goals: int,
) -> str:
    payload = {
        "variant": variant.value,
        "ring_cells": sorted(ring_cells),
        "ring_ports": sorted((port.coord, port.preferred_dir) for port in ring_ports),
        "lift_columns": sorted(
            (column.platform_coord, column.lift_coord, column.target_lane)
            for column in lift_columns
        ),
        "trunk_mask_cells": sorted(trunk_mask_cells),
        "inner_cells": sorted(inner_cells),
        "capacity_goals": capacity_goals,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(encoded).hexdigest()
    return digest[:16]


__all__ = ["RttpSkeletonBuilder"]
