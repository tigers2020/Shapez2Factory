"""GA evolution shadow contracts (PR-GA-1 observe-only)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GaEvolutionShadowConfig:
    enabled: bool = False
    observe_only: bool = True
    population_size: int = 24
    generations: int = 8
    mutation_rate: float = 0.15
    tournament_size: int = 3
    elite_count: int = 2
    random_seed: int = 0


@dataclass(frozen=True, slots=True)
class GaEvolutionShadowSummary:
    enabled: bool
    observe_only: bool
    primary_commit_order: tuple[str, ...]
    shadow_proposed_commit_order: tuple[str, ...]
    shadow_fitness_total: float
    generations_run: int
    population_size: int
    overlap_violation_count: int
    gene_count: int
    anchor_count: int
    order_agreement_ratio: float


__all__ = ["GaEvolutionShadowConfig", "GaEvolutionShadowSummary"]
