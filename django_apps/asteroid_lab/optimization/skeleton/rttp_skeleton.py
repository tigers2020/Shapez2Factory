"""RTTP Layer 1 skeleton DTO."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import LiftColumn, RingPort


@dataclass(frozen=True, slots=True)
class RttpSkeleton:
    ring_cells: frozenset[Coord]
    ring_ports: tuple[RingPort, ...]
    lift_columns: tuple[LiftColumn, ...]
    trunk_mask_cells: frozenset[Coord]
    capacity_goals: int
    inner_cells: frozenset[Coord]
    skeleton_id: str


__all__ = ["RttpSkeleton"]
