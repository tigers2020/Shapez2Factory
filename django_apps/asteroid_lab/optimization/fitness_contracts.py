"""Phase 5 fitness / Phase 10B survivability DTOs and conservative penalties."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.enums import PenaltyMode


@dataclass(frozen=True, slots=True)
class FitnessMetrics:
    """Aggregates attached to FitnessBreakdown (Phase 5)."""

    selected_candidate_count: int
    extractor_count: int
    extension_count: int
    overlap_count: int
    unreachable_count: int
    total_route_cost: int
    max_trunk_sharing: int
    narrow_passage_occupied_count: int


@dataclass(frozen=True, slots=True)
class FitnessBreakdown:
    """Pre-commit predictive fitness (candidate probe snapshot). Not commit proof."""

    extractor_score: float
    extension_score: float
    throughput_score: float
    route_cost_penalty: float
    overlap_penalty: float
    unreachable_penalty: float
    congestion_penalty: float
    orphan_penalty: float
    corridor_block_penalty: float
    future_expansion_penalty: float
    narrow_passage_penalty: float
    trunk_sharing_penalty: float
    dead_end_penalty: float
    route_goal_quality_score: float
    route_goal_priority_penalty: float
    route_fragility_penalty: float
    shared_corridor_pressure_penalty: float
    total: float
    metrics: FitnessMetrics


@dataclass(frozen=True, slots=True)
class CommitSurvivabilityMetrics:
    """Post-commit observed metrics (replay / diagnostics only; never GA input)."""

    commit_attempt_count: int
    commit_confirmed_count: int
    commit_rolled_back_count: int
    commit_success_ratio: float
    rollback_reason_counts: dict[str, int]
    route_probe_failed_count: int
    transport_kind_conflict_count: int


def compute_conservative_fragility_penalties(
    *,
    penalty_mode: PenaltyMode,
    path_cells: frozenset[Coord],
    other_candidate_path_cells: frozenset[Coord],
    narrow_segment_count: int,
    alpha: float = 1.0,
    beta: float = 1.0,
) -> tuple[float, float]:
    """Predictive penalties from candidate-domain geometry (not observed commit outcome)."""

    if penalty_mode is PenaltyMode.OFF:
        return 0.0, 0.0
    shared = len(path_cells & other_candidate_path_cells)
    corridor_pressure = alpha * float(shared)
    fragility = beta * float(max(0, narrow_segment_count))
    return fragility, corridor_pressure


def evolution_distant_mutation_slot_index(
    *,
    seed: int,
    generation: int,
    genome_id: str,
    population_size: int,
) -> int:
    """Deterministic slot for forced distant mutation (Phase 6; no unseeded random)."""

    if population_size <= 0:
        raise ValueError("population_size must be positive")
    payload = f"{seed}:{generation}:{genome_id}".encode()
    digest = hashlib.sha256(payload).digest()
    value = int.from_bytes(digest[:8], "big")
    return value % population_size
