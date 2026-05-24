"""Minimal optimization input contracts for RTTP Layer 1 (PR-1 + PR-2)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from django_apps.asteroid_lab.contracts.building_catalog_slice import BuildingCatalogSlice
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame


class TransportKind(StrEnum):
    SHAPE_BELT = "shape_belt"
    FLUID_PIPE = "fluid_pipe"


class RouteGoalKind(StrEnum):
    TRUNK_SEED = "trunk_seed"
    EXTERNAL_MARGIN = "external_margin"
    CORRIDOR_ENTRY = "corridor_entry"


@dataclass(frozen=True, slots=True)
class RouteGoal:
    coord: Coord
    goal_kind: RouteGoalKind
    transport_kind: TransportKind | None
    priority: int
    existing_trunk: bool


@dataclass(frozen=True, slots=True)
class ExistingTransportCell:
    coord: Coord
    transport_kind: TransportKind


@dataclass(frozen=True, slots=True)
class OptimizationInput:
    mineable_cells: frozenset[Coord]
    rim_cells: frozenset[Coord]
    inner_cells: frozenset[Coord]
    external_void_cells: frozenset[Coord]
    protected_corridor_cells: frozenset[Coord]
    existing_trunk_cells: frozenset[Coord]
    transport_kind: TransportKind
    route_goals: tuple[RouteGoal, ...]
    existing_transport_cells: frozenset[ExistingTransportCell]
    blocked_incompatible_transport_cells: frozenset[Coord] = frozenset()
    coord_frame: CoordFrame = CoordFrame.ISLAND_RAW
    catalog_slice: BuildingCatalogSlice | None = None


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


@dataclass(frozen=True, slots=True)
class RttpPipelineConfig:
    """RTTP pipeline mode (v0.1 default; v1 macro-only when ``macro_only_mode``)."""

    macro_only_mode: bool = False
    allow_singleton_genome_slots: bool = False
    max_macro_candidates: int = 64


__all__ = [
    "CoordFrame",
    "ExistingTransportCell",
    "LiftColumn",
    "OptimizationInput",
    "RingPort",
    "RouteGoal",
    "RouteGoalKind",
    "RttpPipelineConfig",
    "RttpSkeletonConfig",
    "TransportKind",
]
