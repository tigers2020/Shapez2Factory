"""GA evolution observe-only shadow (PR-GA-1)."""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab.contracts.ga_evolution_shadow import (
    GaEvolutionShadowConfig,
    GaEvolutionShadowSummary,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.selection.ga_evolution import select_genome_evolution
from django_apps.asteroid_lab.optimization.selection.genome_fitness import (
    evaluate_genome_fitness,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import (
    PlacementGenome,
    SelectionConfig,
)
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton


def _order_agreement_ratio(
    primary: tuple[str, ...],
    shadow: tuple[str, ...],
) -> float:
    if not primary and not shadow:
        return 1.0
    shared_prefix = 0
    for left, right in zip(primary, shadow, strict=False):
        if left != right:
            break
        shared_prefix += 1
    return shared_prefix / float(max(len(primary), len(shadow), 1))


def _anchor_count(
    commit_order: tuple[str, ...],
    candidates_by_id: dict[str, BundleCandidate],
) -> int:
    anchors: set[tuple[int, int]] = set()
    for candidate_id in commit_order:
        candidate = candidates_by_id.get(candidate_id)
        if candidate is not None:
            anchors.add(candidate.anchor_coord)
    return len(anchors)


def build_ga_evolution_shadow_summary(
    *,
    primary_genome: PlacementGenome,
    normal_candidates: tuple[BundleCandidate, ...],
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    goal_count: int,
    config: GaEvolutionShadowConfig,
) -> GaEvolutionShadowSummary:
    primary_order = tuple(primary_genome.commit_order)
    if not config.enabled:
        return GaEvolutionShadowSummary(
            enabled=False,
            observe_only=True,
            primary_commit_order=primary_order,
            shadow_proposed_commit_order=(),
            shadow_fitness_total=0.0,
            generations_run=0,
            population_size=config.population_size,
            overlap_violation_count=0,
            gene_count=0,
            anchor_count=0,
            order_agreement_ratio=1.0 if not primary_order else 0.0,
        )

    if not config.observe_only:
        msg = "ga_evolution_shadow.observe_only must be true in PR-GA-1"
        raise ValueError(msg)

    candidates_by_id = {candidate.candidate_id: candidate for candidate in normal_candidates}
    shadow_genome = select_genome_evolution(
        normal_candidates,
        skeleton,
        inp,
        goal_count=goal_count,
        config=config,
    )
    shadow_order = tuple(shadow_genome.commit_order)
    shadow_fitness = evaluate_genome_fitness(
        shadow_order,
        candidates_by_id=candidates_by_id,
        skeleton=skeleton,
        inp=inp,
        config=SelectionConfig(),
        goal_count=goal_count,
    )

    return GaEvolutionShadowSummary(
        enabled=True,
        observe_only=True,
        primary_commit_order=primary_order,
        shadow_proposed_commit_order=shadow_order,
        shadow_fitness_total=shadow_fitness,
        generations_run=max(1, config.generations),
        population_size=config.population_size,
        overlap_violation_count=0,
        gene_count=len(shadow_order),
        anchor_count=_anchor_count(shadow_order, candidates_by_id),
        order_agreement_ratio=_order_agreement_ratio(primary_order, shadow_order),
    )


def ga_evolution_shadow_metrics(summary: GaEvolutionShadowSummary) -> dict[str, Any]:
    return {
        "enabled": summary.enabled,
        "observe_only": summary.observe_only,
        "primary_commit_order": list(summary.primary_commit_order),
        "shadow_proposed_commit_order": list(summary.shadow_proposed_commit_order),
        "shadow_fitness_total": summary.shadow_fitness_total,
        "generations_run": summary.generations_run,
        "population_size": summary.population_size,
        "overlap_violation_count": summary.overlap_violation_count,
        "gene_count": summary.gene_count,
        "anchor_count": summary.anchor_count,
        "order_agreement_ratio": summary.order_agreement_ratio,
    }


__all__ = [
    "build_ga_evolution_shadow_summary",
    "ga_evolution_shadow_metrics",
]
