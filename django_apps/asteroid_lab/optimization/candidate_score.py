"""Phase I — candidate scoring for greedy selection (PR4)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.candidate_dtos import GeneCandidate
from django_apps.asteroid_lab.optimization.capacity_planner import (
    FLUID_PLATFORMS_PER_GOAL,
    SHAPE_PLATFORMS_PER_GOAL,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.enums import TransportKind
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput

THROUGHPUT_WEIGHT = 100
ROUTE_COST_WEIGHT = 5
GOAL_PRIORITY_WEIGHT = 20
CORRIDOR_CELL_WEIGHT = 1
TRUNK_LOAD_WEIGHT = 50

GoalLoadKey = tuple[Coord, TransportKind]


@dataclass(frozen=True, slots=True)
class CandidateScoreBreakdown:
    throughput_term: float
    route_cost_penalty: float
    goal_priority_penalty: float
    corridor_pressure_penalty: float
    trunk_load_penalty: float
    total: float


def goal_load_key_for_candidate(candidate: GeneCandidate) -> GoalLoadKey:
    goal = candidate.route_probe_result.reached_goal
    if goal is None:
        msg = "normal candidate requires reached_goal for scoring"
        raise ValueError(msg)
    kind = goal.transport_kind if goal.transport_kind is not None else candidate.transport_kind
    return (goal.coord, kind)


def _trunk_capacity(transport_kind: TransportKind) -> int:
    if transport_kind == TransportKind.FLUID_PIPE:
        return FLUID_PLATFORMS_PER_GOAL
    return SHAPE_PLATFORMS_PER_GOAL


def _corridor_pressure_penalty(
    candidate: GeneCandidate,
    *,
    inp: OptimizationInput,
) -> float:
    protected = inp.protected_corridor_cells
    if not protected:
        return 0.0
    overlap = sum(1 for cell in candidate.route_probe_result.path if cell in protected)
    return float(overlap * CORRIDOR_CELL_WEIGHT)


def _trunk_load_penalty(
    candidate: GeneCandidate,
    *,
    goal_assigned_platforms: Mapping[GoalLoadKey, int],
) -> float:
    key = goal_load_key_for_candidate(candidate)
    assigned = goal_assigned_platforms.get(key, 0)
    capacity = _trunk_capacity(candidate.transport_kind)
    load_ratio = assigned / capacity
    return load_ratio * TRUNK_LOAD_WEIGHT


def score_gene_candidate(
    candidate: GeneCandidate,
    *,
    inp: OptimizationInput,
    goal_assigned_platforms: Mapping[GoalLoadKey, int],
) -> CandidateScoreBreakdown:
    """Phase I v0 score; read-only ``inp``."""

    probe = candidate.route_probe_result
    if probe.goal_priority is None:
        msg = "normal candidate requires goal_priority for scoring"
        raise ValueError(msg)

    throughput_term = float(candidate.base_throughput * THROUGHPUT_WEIGHT)
    route_cost_penalty = float(probe.cost * ROUTE_COST_WEIGHT)
    goal_priority_penalty = float(probe.goal_priority * GOAL_PRIORITY_WEIGHT)
    corridor_pressure_penalty = _corridor_pressure_penalty(candidate, inp=inp)
    trunk_load_penalty = _trunk_load_penalty(
        candidate,
        goal_assigned_platforms=goal_assigned_platforms,
    )
    total = (
        throughput_term
        - route_cost_penalty
        - goal_priority_penalty
        - corridor_pressure_penalty
        - trunk_load_penalty
    )
    return CandidateScoreBreakdown(
        throughput_term=throughput_term,
        route_cost_penalty=route_cost_penalty,
        goal_priority_penalty=goal_priority_penalty,
        corridor_pressure_penalty=corridor_pressure_penalty,
        trunk_load_penalty=trunk_load_penalty,
        total=total,
    )
