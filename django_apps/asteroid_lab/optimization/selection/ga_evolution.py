"""Bounded GA genome selection (PR-GA-1 shadow + PR-GA-2 primary)."""

from __future__ import annotations

import random
from collections.abc import Sequence

from django_apps.asteroid_lab.contracts.ga_evolution_shadow import GaEvolutionShadowConfig
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.selection.equivalence import dedupe_candidates
from django_apps.asteroid_lab.optimization.selection.genome_fitness import (
    evaluate_genome_fitness,
    genome_layout_valid,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import (
    PlacementGenome,
    SelectionConfig,
)
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton


def _candidates_by_id(
    pool: Sequence[BundleCandidate],
) -> dict[str, BundleCandidate]:
    return {candidate.candidate_id: candidate for candidate in pool}


def _greedy_build_genome(
    pool: tuple[BundleCandidate, ...],
    *,
    candidates_by_id: dict[str, BundleCandidate],
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    goal_count: int,
    rng: random.Random,
    selection_config: SelectionConfig,
) -> PlacementGenome:
    shuffled = list(pool)
    rng.shuffle(shuffled)
    order: list[str] = []
    for candidate in shuffled:
        if len(order) >= goal_count:
            break
        tentative = (*order, candidate.candidate_id)
        if genome_layout_valid(tentative, candidates_by_id, goal_count=goal_count):
            order.append(candidate.candidate_id)
    return PlacementGenome(commit_order=tuple(order))


def _tournament_pick(
    population: list[PlacementGenome],
    fitness_by_id: dict[int, float],
    *,
    tournament_size: int,
    rng: random.Random,
) -> PlacementGenome:
    contenders = rng.sample(population, k=min(tournament_size, len(population)))
    return max(contenders, key=lambda genome: fitness_by_id[id(genome)])


def _order_crossover(
    parent_a: PlacementGenome,
    parent_b: PlacementGenome,
    *,
    candidates_by_id: dict[str, BundleCandidate],
    goal_count: int,
) -> PlacementGenome:
    if not parent_a.commit_order or not parent_b.commit_order:
        return parent_a if parent_a.commit_order else parent_b
    cut = len(parent_a.commit_order) // 2
    prefix = parent_a.commit_order[:cut]
    suffix_ids = [cid for cid in parent_b.commit_order if cid not in prefix]
    child: list[str] = []
    for candidate_id in (*prefix, *suffix_ids):
        tentative = (*child, candidate_id)
        if genome_layout_valid(tentative, candidates_by_id, goal_count=goal_count):
            child.append(candidate_id)
        if len(child) >= goal_count:
            break
    return PlacementGenome(commit_order=tuple(child))


def _mutate(
    genome: PlacementGenome,
    pool: tuple[BundleCandidate, ...],
    *,
    candidates_by_id: dict[str, BundleCandidate],
    goal_count: int,
    rng: random.Random,
) -> PlacementGenome:
    order = list(genome.commit_order)
    if not pool:
        return PlacementGenome(commit_order=tuple(order))
    roll = rng.random()
    if roll < 0.33 and len(order) > 1:
        i, j = rng.sample(range(len(order)), k=2)
        order[i], order[j] = order[j], order[i]
    elif roll < 0.66:
        if order:
            drop = rng.randrange(len(order))
            order.pop(drop)
    else:
        available = [c for c in pool if c.candidate_id not in order]
        rng.shuffle(available)
        for candidate in available:
            tentative = (*order, candidate.candidate_id)
            if genome_layout_valid(tentative, candidates_by_id, goal_count=goal_count):
                order.append(candidate.candidate_id)
            if len(order) >= goal_count:
                break
    if genome_layout_valid(order, candidates_by_id, goal_count=goal_count):
        return PlacementGenome(commit_order=tuple(order))
    return genome


def select_genome_evolution(
    normal_candidates: tuple[BundleCandidate, ...],
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    *,
    goal_count: int,
    config: GaEvolutionShadowConfig,
    selection_config: SelectionConfig | None = None,
) -> PlacementGenome:
    """Bounded GA; deterministic with ``config.random_seed``."""

    resolved_goal = max(0, goal_count)
    pool = tuple(dedupe_candidates(normal_candidates))
    if not pool or resolved_goal == 0:
        return PlacementGenome(commit_order=())

    candidates_map = _candidates_by_id(pool)
    resolved_selection = selection_config if selection_config is not None else SelectionConfig()
    rng = random.Random(config.random_seed)
    pop_size = max(2, config.population_size)
    generations = max(1, config.generations)

    population: list[PlacementGenome] = []
    for _ in range(pop_size):
        population.append(
            _greedy_build_genome(
                pool,
                candidates_by_id=candidates_map,
                skeleton=skeleton,
                inp=inp,
                goal_count=resolved_goal,
                rng=rng,
                selection_config=resolved_selection,
            )
        )

    def fitness(genome: PlacementGenome) -> float:
        return evaluate_genome_fitness(
            genome.commit_order,
            candidates_by_id=candidates_map,
            skeleton=skeleton,
            inp=inp,
            config=resolved_selection,
            goal_count=resolved_goal,
        )

    best = max(population, key=fitness)
    best_score = fitness(best)

    for _ in range(generations):
        fitness_map = {id(genome): fitness(genome) for genome in population}
        elite_count = min(config.elite_count, len(population))
        sorted_pop = sorted(population, key=fitness, reverse=True)
        next_pop = list(sorted_pop[:elite_count])
        while len(next_pop) < pop_size:
            parent_a = _tournament_pick(
                population,
                fitness_map,
                tournament_size=config.tournament_size,
                rng=rng,
            )
            parent_b = _tournament_pick(
                population,
                fitness_map,
                tournament_size=config.tournament_size,
                rng=rng,
            )
            child = _order_crossover(
                parent_a,
                parent_b,
                candidates_by_id=candidates_map,
                goal_count=resolved_goal,
            )
            if rng.random() < config.mutation_rate:
                child = _mutate(
                    child,
                    pool,
                    candidates_by_id=candidates_map,
                    goal_count=resolved_goal,
                    rng=rng,
                )
            next_pop.append(child)
        population = next_pop
        gen_best = max(population, key=fitness)
        gen_score = fitness(gen_best)
        if gen_score > best_score:
            best = gen_best
            best_score = gen_score

    return best


__all__ = ["select_genome_evolution"]
