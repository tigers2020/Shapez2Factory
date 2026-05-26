"""EVTC exterior connector planner output."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import RouteGoal


@dataclass(frozen=True, slots=True)
class ExteriorConnectorPlan:
    selected_goals: tuple[RouteGoal, ...]
    candidate_margin_coords: frozenset[Coord]
    planner_shortfall: bool
    required_count: int


__all__ = ["ExteriorConnectorPlan"]
