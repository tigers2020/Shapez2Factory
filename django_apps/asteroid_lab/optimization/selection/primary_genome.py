"""Primary genome selection by SelectionMode (PR-GA-2)."""

from __future__ import annotations

from collections.abc import Sequence

from django_apps.asteroid_lab.contracts.ga_evolution_shadow import GaEvolutionShadowConfig
from django_apps.asteroid_lab.contracts.selection_mode import SelectionMode
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.selection.ga_evolution import select_genome_evolution
from django_apps.asteroid_lab.optimization.selection.greedy_regret import (
    PlacementGenome,
    select_genome,
)
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton


def select_primary_genome(
    *,
    mode: SelectionMode,
    normal_candidates: Sequence[BundleCandidate],
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    goal_count: int,
    ga_config: GaEvolutionShadowConfig,
) -> PlacementGenome:
    pool = tuple(normal_candidates)
    if mode is SelectionMode.EVOLUTION:
        return select_genome_evolution(
            pool,
            skeleton,
            inp,
            goal_count=goal_count,
            config=ga_config,
        )
    return select_genome(pool, skeleton, inp, goal_count=goal_count)


__all__ = ["select_primary_genome"]
