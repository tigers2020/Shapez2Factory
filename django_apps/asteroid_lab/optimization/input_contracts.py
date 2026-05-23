"""Minimal optimization input contracts for RTTP Layer 1 (PR-1)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from django_apps.asteroid_lab.optimization.coords import Coord


class TransportKind(StrEnum):
    SHAPE_BELT = "shape_belt"
    FLUID_PIPE = "fluid_pipe"


@dataclass(frozen=True, slots=True)
class OptimizationInput:
    mineable_cells: frozenset[Coord]
    rim_cells: frozenset[Coord]
    inner_cells: frozenset[Coord]
    external_void_cells: frozenset[Coord]
    protected_corridor_cells: frozenset[Coord]
    existing_trunk_cells: frozenset[Coord]
    transport_kind: TransportKind


@dataclass(frozen=True, slots=True)
class RttpSkeletonConfig:
    w_inner: float = 1.0
    w_port: float = 2.0
    w_ring: float = 0.5


@dataclass(frozen=True, slots=True)
class RingPort:
    coord: Coord
    preferred_dir: str


@dataclass(frozen=True, slots=True)
class LiftColumn:
    platform_coord: Coord
    lift_coord: Coord
    target_lane: int


__all__ = [
    "LiftColumn",
    "OptimizationInput",
    "RingPort",
    "RttpSkeletonConfig",
    "TransportKind",
]
