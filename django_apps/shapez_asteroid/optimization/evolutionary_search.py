"""Deterministic mutation + repair + elitism evolutionary search (Sequence 5)."""

from __future__ import annotations

import math
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import replace
from random import Random

from django_apps.shapez_asteroid.optimization.coords import Coord
from django_apps.shapez_asteroid.optimization.dto import (
    BundleCandidate,
    EvolutionConfig,
    EvolutionResult,
    FitnessBreakdown,
    Gene,
    Genome,
    GenomeDiversityMetrics,
    RouteCellDomain,
)
from django_apps.shapez_asteroid.optimization.enums import EvolutionConvergenceReason, RouteClass
from django_apps.shapez_asteroid.optimization.genome_fitness import (
    evaluate_genome,
    probe_unreachable_or_stale,
)

_MAX_BUNDLES_PER_GENOME = 8


def _commit_order_sort_key(g: Gene) -> tuple[int, str, bool]:
    """Sort key: ``commit_order`` is authoritative; ``candidate_id`` tie-break; enabled first."""

    return (g.commit_order, g.candidate_id, not g.enabled)


_MUTATION_OPS: tuple[str, ...] = (
    "add_candidate",
    "remove_candidate",
    "swap_candidate",
    "replace_with_nearby_candidate",
    "toggle_candidate",
    "commit_order_shuffle",
)


def validate_evolution_config(cfg: EvolutionConfig) -> None:
    if cfg.population_size <= 0:
        raise ValueError("population_size must be > 0")
    if not (0 <= cfg.elite_count < cfg.population_size):
        raise ValueError("elite_count must satisfy 0 <= elite_count < population_size")
    if not (0.0 <= cfg.mutation_rate <= 1.0):
        raise ValueError("mutation_rate must be in [0.0, 1.0]")
    if cfg.tournament_size < 1:
        raise ValueError("tournament_size must be >= 1")
    if cfg.max_generation < 1:
        raise ValueError("max_generation must be >= 1")
    if cfg.max_stall_generation < 0:
        raise ValueError("max_stall_generation must be >= 0")
    if cfg.time_budget_ms is not None and cfg.time_budget_ms <= 0:
        raise ValueError("time_budget_ms must be None or > 0")
    if cfg.forced_distant_mutation_period is not None and cfg.forced_distant_mutation_period < 1:
        raise ValueError("forced_distant_mutation_period must be None or >= 1")


def _pool_by_id(pool: Sequence[BundleCandidate]) -> dict[str, BundleCandidate]:
    out: dict[str, BundleCandidate] = {}
    for c in sorted(pool, key=lambda z: z.candidate_id):
        if c.candidate_id in out:
            raise ValueError(f"duplicate candidate_id in pool: {c.candidate_id!r}")
        out[c.candidate_id] = c
    return out


def deterministic_sort_key(genome: Genome, fitness: FitnessBreakdown) -> tuple[float, float, str]:
    """Ascending sort picks the better genome (higher total, then count, then id ascending)."""

    return (
        -fitness.total,
        -float(fitness.metrics.selected_candidate_count),
        genome.genome_id,
    )


def _better_key(a: tuple[float, float, str], b: tuple[float, float, str]) -> bool:
    """True if ``a`` is strictly better than ``b`` (lower sort key)."""

    return a < b


def tournament_select(
    scored: Sequence[tuple[Genome, FitnessBreakdown]],
    rng: Random,
    *,
    tournament_size: int,
) -> tuple[Genome, FitnessBreakdown]:
    """Deterministic tournament on pre-evaluated population."""

    if not scored:
        raise ValueError("empty population")
    k = min(tournament_size, len(scored))
    indices = sorted(rng.sample(range(len(scored)), k=k))
    best = scored[indices[0]]
    best_key = deterministic_sort_key(best[0], best[1])
    for idx in indices[1:]:
        cand = scored[idx]
        key = deterministic_sort_key(cand[0], cand[1])
        if _better_key(key, best_key):
            best, best_key = cand, key
    return best


def compute_population_diversity(
    population: Sequence[Genome],
    candidate_pool: Sequence[BundleCandidate],
) -> GenomeDiversityMetrics:
    """Observability metrics only; v0 may use coarse heuristics."""

    by_id = _pool_by_id(candidate_pool)
    sigs: list[str] = []
    kinds: list[str] = []
    rim_cells: list[Coord] = []
    for g in sorted(population, key=lambda z: z.genome_id):
        for gene in sorted(g.genes, key=lambda gg: (gg.candidate_id, gg.commit_order)):
            if not gene.enabled:
                continue
            c = by_id.get(gene.candidate_id)
            if c is None:
                continue
            sigs.append(c.topology_signature)
            kinds.append(c.transport_kind.value)
            rim_cells.append(c.extractor)
    distinct_sigs = len(frozenset(sigs)) if sigs else 0
    if not rim_cells:
        return GenomeDiversityMetrics(
            distinct_topology_signatures=distinct_sigs,
            rim_cell_entropy_bits=0.0,
            transport_kind_mix_score=0.0,
        )
    n = len(rim_cells)
    counts = Counter(rim_cells)
    entropy = 0.0
    for _cell, k in sorted(counts.items(), key=lambda z: (z[0].x, z[0].y)):
        p = k / n
        entropy -= p * math.log2(p)
    kind_counts = Counter(kinds)
    if not kind_counts:
        mix = 0.0
    else:
        dominant = max(kind_counts.values())
        mix = 1.0 - (dominant / n)
    return GenomeDiversityMetrics(
        distinct_topology_signatures=distinct_sigs,
        rim_cell_entropy_bits=float(entropy),
        transport_kind_mix_score=float(mix),
    )


def _reassign_commit_order(genes: Sequence[Gene]) -> tuple[Gene, ...]:
    """Renumber ``commit_order`` to ``0..n-1`` without collapsing shuffle semantics.

    Genes are ordered by ``_commit_order_sort_key`` so ``commit_order_shuffle`` and repair
    steps explore real commit permutations instead of reverting to ``candidate_id`` order.
    """

    ordered = sorted(genes, key=_commit_order_sort_key)
    return tuple(replace(g, commit_order=i) for i, g in enumerate(ordered))


def _genes_tuple(genes: Sequence[Gene]) -> tuple[Gene, ...]:
    return tuple(genes)


def initialize_population(
    cfg: EvolutionConfig,
    candidate_pool: Sequence[BundleCandidate],
    rng: Random,
    *,
    next_genome_seq: list[int],
) -> list[Genome]:
    """Deterministic random initial genomes (candidate ids only, no within-genome dupes)."""

    pool_ids = sorted(c.candidate_id for c in candidate_pool)
    if not pool_ids:
        return []
    pop: list[Genome] = []
    for pi in range(cfg.population_size):
        upper = min(len(pool_ids), _MAX_BUNDLES_PER_GENOME)
        k = 1 + (abs(cfg.seed + pi * 7919) % upper)
        k = max(1, k)
        chosen = rng.sample(pool_ids, k=min(k, len(pool_ids)))
        chosen_sorted = sorted(chosen)
        genes = tuple(
            Gene(candidate_id=cid, enabled=True, commit_order=i)
            for i, cid in enumerate(chosen_sorted)
        )
        next_genome_seq[0] += 1
        gid = f"g{next_genome_seq[0]:08d}-{cfg.seed}-{pi}"
        pop.append(Genome(genome_id=gid, genes=genes, seed=cfg.seed))
    return pop


def _manhattan(a: Coord, b: Coord) -> int:
    return abs(a.x - b.x) + abs(a.y - b.y)


def _nearby_candidate_ids(
    current_id: str,
    by_id: dict[str, BundleCandidate],
) -> tuple[str, ...]:
    cur = by_id.get(current_id)
    if cur is None:
        return ()
    out: list[str] = []
    for cid in sorted(by_id):
        if cid == current_id:
            continue
        o = by_id[cid]
        if _manhattan(cur.extractor, o.extractor) <= 1:
            out.append(cid)
    return tuple(out)


def _far_replace_candidate_id(
    current_id: str,
    by_id: dict[str, BundleCandidate],
    rng: Random,
) -> str | None:
    ids = sorted(by_id)
    if len(ids) < 2:
        return None
    pos = ids.index(current_id) if current_id in ids else 0
    offset = 1 + (rng.randint(0, 10_007) % (len(ids) - 1))
    return ids[(pos + offset) % len(ids)]


def mutate_genome(
    genome: Genome,
    candidate_pool: Sequence[BundleCandidate],
    rng: Random,
    *,
    mutation_rate: float,
    next_genome_seq: list[int],
    forced_distant: bool,
) -> Genome:
    """Single-step mutation on candidate ids / flags / commit_order only."""

    if rng.random() >= mutation_rate and not forced_distant:
        next_genome_seq[0] += 1
        return replace(genome, genome_id=f"g{next_genome_seq[0]:08d}-clone")

    by_id = _pool_by_id(candidate_pool)
    pool_ids = sorted(by_id)
    genes = list(genome.genes)

    if forced_distant and len(pool_ids) >= 2 and genes:
        idx = rng.randint(0, len(genes) - 1)
        g0 = genes[idx]
        rep = _far_replace_candidate_id(g0.candidate_id, by_id, rng)
        if rep is not None and rep != g0.candidate_id:
            used = {x.candidate_id for x in genes if x.enabled and x is not g0}
            if rep not in used:
                genes[idx] = replace(g0, candidate_id=rep)
                next_genome_seq[0] += 1
                gid = f"g{next_genome_seq[0]:08d}-fdm"
                return Genome(
                    genome_id=gid,
                    genes=_genes_tuple(_reassign_commit_order(genes)),
                    seed=genome.seed,
                )
        i2 = rng.randint(0, len(genes) - 1)
        if len(genes) >= 2:
            i1 = idx
            if i1 != i2:
                genes[i1], genes[i2] = genes[i2], genes[i1]
                next_genome_seq[0] += 1
                gid = f"g{next_genome_seq[0]:08d}-fdmswap"
                return Genome(
                    genome_id=gid,
                    genes=_genes_tuple(_reassign_commit_order(genes)),
                    seed=genome.seed,
                )

    op = _MUTATION_OPS[rng.randint(0, len(_MUTATION_OPS) - 1)]
    enabled_idx = [i for i, gg in enumerate(genes) if gg.enabled]
    present_ids = {gg.candidate_id for gg in genes}

    if op == "add_candidate" and len(present_ids) < min(len(pool_ids), _MAX_BUNDLES_PER_GENOME):
        free = [cid for cid in pool_ids if cid not in present_ids]
        if free:
            cid = free[rng.randint(0, len(free) - 1)]
            genes.append(Gene(cid, True, max((g.commit_order for g in genes), default=-1) + 1))
    elif op == "remove_candidate" and enabled_idx:
        ri = enabled_idx[rng.randint(0, len(enabled_idx) - 1)]
        genes[ri] = replace(genes[ri], enabled=False)
    elif op == "swap_candidate" and len(genes) >= 2:
        i = rng.randint(0, len(genes) - 1)
        j = rng.randint(0, len(genes) - 1)
        if i != j:
            genes[i], genes[j] = genes[j], genes[i]
    elif op == "replace_with_nearby_candidate" and genes:
        i = rng.randint(0, len(genes) - 1)
        g0 = genes[i]
        near = _nearby_candidate_ids(g0.candidate_id, by_id)
        if near:
            rep = near[rng.randint(0, len(near) - 1)]
            used = {x.candidate_id for x in genes if x is not g0}
            if rep not in used:
                genes[i] = replace(g0, candidate_id=rep)
    elif op == "toggle_candidate" and genes:
        i = rng.randint(0, len(genes) - 1)
        genes[i] = replace(genes[i], enabled=not genes[i].enabled)
    elif op == "commit_order_shuffle" and len(genes) >= 2:
        orders = list(range(len(genes)))
        rng.shuffle(orders)
        new_genes: list[Gene] = []
        for g0, co in zip(genes, orders, strict=True):
            new_genes.append(replace(g0, commit_order=co))
        genes = new_genes

    next_genome_seq[0] += 1
    gid = f"g{next_genome_seq[0]:08d}-mut"
    return Genome(
        genome_id=gid,
        genes=_genes_tuple(_reassign_commit_order(genes)),
        seed=genome.seed,
    )


def _overlap_low_score_removal(
    genes: Sequence[Gene],
    by_id: dict[str, BundleCandidate],
) -> tuple[Gene, ...]:
    selected = tuple(by_id[g.candidate_id] for g in genes if g.enabled and g.candidate_id in by_id)
    if len(selected) < 2:
        return _genes_tuple(genes)

    counts: dict[Coord, list[str]] = {}
    for cand in sorted(selected, key=lambda z: z.candidate_id):
        for cell in sorted(cand.occupied_cells, key=lambda z: (z.x, z.y)):
            counts.setdefault(cell, []).append(cand.candidate_id)
    offenders: set[str] = set()
    for _cell, ids in sorted(counts.items(), key=lambda z: (z[0].x, z[0].y)):
        u = sorted(frozenset(ids))
        if len(u) > 1:
            offenders.update(u)

    if not offenders:
        return _genes_tuple(genes)

    scored: list[tuple[float, str]] = []
    for cid in sorted(offenders):
        c = by_id[cid]
        marginal = float(c.base_throughput) - 0.01 * float(c.route_probe_result.cost)
        scored.append((marginal, cid))
    scored.sort(key=lambda z: (z[0], z[1]))
    drop = scored[0][1]
    out: list[Gene] = []
    for g in genes:
        if g.enabled and g.candidate_id == drop:
            out.append(replace(g, enabled=False))
        else:
            out.append(g)
    return _genes_tuple(_reassign_commit_order(out))


def _remove_unreachable(
    genes: Sequence[Gene],
    by_id: dict[str, BundleCandidate],
) -> tuple[Gene, ...]:
    out: list[Gene] = []
    for g in genes:
        c = by_id.get(g.candidate_id)
        if c is not None and g.enabled and probe_unreachable_or_stale(c.route_probe_result):
            out.append(replace(g, enabled=False))
        else:
            out.append(g)
    return _genes_tuple(_reassign_commit_order(out))


def _remove_corridor_blocker(
    genes: Sequence[Gene],
    by_id: dict[str, BundleCandidate],
    route_domain: Mapping[Coord, RouteCellDomain] | None,
) -> tuple[Gene, ...]:
    if route_domain is None:
        return _genes_tuple(genes)

    narrow_scores: list[tuple[int, str]] = []
    for g in genes:
        if not g.enabled:
            continue
        c = by_id.get(g.candidate_id)
        if c is None or probe_unreachable_or_stale(c.route_probe_result):
            continue
        n = 0
        for cell in c.route_probe_result.path:
            dom = route_domain.get(cell)
            if dom is not None and dom.route_class is RouteClass.NARROW_CORRIDOR:
                n += 1
        narrow_scores.append((n, g.candidate_id))
    if not narrow_scores or max(narrow_scores, key=lambda z: z[0])[0] == 0:
        return _genes_tuple(genes)
    worst_n = max(n for n, _ in narrow_scores)
    worst_ids = sorted({cid for n, cid in narrow_scores if n == worst_n})
    drop = worst_ids[-1]
    out: list[Gene] = []
    for g in genes:
        if g.enabled and g.candidate_id == drop:
            out.append(replace(g, enabled=False))
        else:
            out.append(g)
    return _genes_tuple(_reassign_commit_order(out))


def _pick_duplicate_keeper(group: Sequence[Gene]) -> Gene:
    """Per ``candidate_id`` group: prefer enabled genes, earliest ``commit_order`` among them."""

    group_list = list(group)
    enabled = [g for g in group_list if g.enabled]
    if enabled:
        return min(enabled, key=lambda g: (g.commit_order, g.candidate_id))
    return min(group_list, key=_commit_order_sort_key)


def _dedupe_candidates(genes: Sequence[Gene]) -> tuple[Gene, ...]:
    """At most one *active* representative per ``candidate_id``; ``commit_order``-canonical keeper.

    Iteration uses ``_commit_order_sort_key`` so ``candidate_id`` never leads the ordering.
    The keeper for a duplicate id is the earliest enabled gene by ``commit_order``; if none
    are enabled, the earliest slot by ``_commit_order_sort_key`` wins (deterministic).
    """

    by_cid: dict[str, list[Gene]] = {}
    for g in genes:
        by_cid.setdefault(g.candidate_id, []).append(g)
    keepers = {cid: _pick_duplicate_keeper(grp) for cid, grp in sorted(by_cid.items())}

    out: list[Gene] = []
    for g in sorted(genes, key=_commit_order_sort_key):
        k = keepers[g.candidate_id]
        if g is k:
            out.append(g)
        else:
            out.append(replace(g, enabled=False))
    return _genes_tuple(_reassign_commit_order(out))


def _limit_bundle_count(
    genes: Sequence[Gene],
    by_id: dict[str, BundleCandidate],
) -> tuple[Gene, ...]:
    enabled = [g for g in genes if g.enabled]
    limit = min(_MAX_BUNDLES_PER_GENOME, max(1, len(by_id)))
    if len(enabled) <= limit:
        return _genes_tuple(genes)

    def marginal(g: Gene) -> tuple[float, str]:
        c = by_id[g.candidate_id]
        return (float(c.base_throughput), g.candidate_id)

    ranked = sorted(enabled, key=marginal)
    drop_ids = frozenset(g.candidate_id for g in ranked[: len(enabled) - limit])
    out: list[Gene] = []
    for g in genes:
        if g.enabled and g.candidate_id in drop_ids:
            out.append(replace(g, enabled=False))
        else:
            out.append(g)
    return _genes_tuple(_reassign_commit_order(out))


def repair_genome(
    genome: Genome,
    candidate_pool: Sequence[BundleCandidate],
    *,
    route_domain: Mapping[Coord, RouteCellDomain] | None = None,
) -> Genome:
    """Deterministic repair pipeline; never introduces unknown candidate ids."""

    by_id = _pool_by_id(candidate_pool)
    genes = genome.genes
    genes = _dedupe_candidates(genes)
    genes = _remove_unreachable(genes, by_id)
    genes = _overlap_low_score_removal(genes, by_id)
    genes = _remove_corridor_blocker(genes, by_id, route_domain)
    genes = _limit_bundle_count(genes, by_id)
    if genes == genome.genes:
        return genome
    return replace(genome, genes=genes)


def _evaluate(
    genome: Genome,
    candidate_pool: Sequence[BundleCandidate],
    route_domain: Mapping[Coord, RouteCellDomain] | None,
    counter: list[int],
) -> FitnessBreakdown:
    counter[0] += 1
    return evaluate_genome(genome, candidate_pool, route_domain=route_domain)


def run_evolutionary_search(
    cfg: EvolutionConfig,
    candidate_pool: Sequence[BundleCandidate],
    *,
    route_domain: Mapping[Coord, RouteCellDomain] | None = None,
    hall_of_fame_total_trace: list[float] | None = None,
) -> EvolutionResult:
    """Evolution on candidate ids only; does not mutate ``candidate_pool``.

    ``hall_of_fame_total_trace`` is optional; when provided, each generation appends the
    current hall-of-fame ``best_fitness.total`` (test / observability only).
    """

    validate_evolution_config(cfg)
    pool_tuple = tuple(candidate_pool)
    if not pool_tuple:
        evaluated = [0]
        dummy = Genome("empty", (), cfg.seed)
        fb = _evaluate(dummy, pool_tuple, route_domain, evaluated)
        return EvolutionResult(
            best_genome=dummy,
            best_fitness=fb,
            generation_count=0,
            evaluated_genome_count=evaluated[0],
            convergence_reason=EvolutionConvergenceReason.CANDIDATE_POOL_EXHAUSTED,
        )

    rng = Random(cfg.seed)
    next_genome_seq = [0]
    evaluated = [0]

    pop = initialize_population(cfg, pool_tuple, rng, next_genome_seq=next_genome_seq)

    scored: list[tuple[Genome, FitnessBreakdown]] = []
    for g in pop:
        r = repair_genome(g, pool_tuple, route_domain=route_domain)
        fit = _evaluate(r, pool_tuple, route_domain, evaluated)
        scored.append((r, fit))

    def sort_pop() -> None:
        scored.sort(key=lambda z: deterministic_sort_key(z[0], z[1]))

    sort_pop()
    best_g, best_f = scored[0]
    initial_best_total = best_f.total
    improved_flag = False
    if hall_of_fame_total_trace is not None:
        hall_of_fame_total_trace.append(best_f.total)

    stall = 0
    convergence: EvolutionConvergenceReason | None = None
    start = time.perf_counter()
    pop_best_key = deterministic_sort_key(scored[0][0], scored[0][1])

    def time_exceeded() -> bool:
        if cfg.time_budget_ms is None:
            return False
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return elapsed_ms >= float(cfg.time_budget_ms)

    generation_done = 0
    for gen in range(cfg.max_generation):
        if time_exceeded():
            convergence = EvolutionConvergenceReason.TIME_BUDGET_MS
            generation_done = gen
            break

        elites = scored[: cfg.elite_count]
        children: list[tuple[Genome, FitnessBreakdown]] = []
        child_target = cfg.population_size - cfg.elite_count
        distant_period = cfg.forced_distant_mutation_period

        for ci in range(child_target):
            parent = tournament_select(scored, rng, tournament_size=cfg.tournament_size)[0]
            forced = bool(
                distant_period is not None
                and distant_period > 0
                and gen > 0
                and gen % distant_period == 0
            )
            mutated = mutate_genome(
                parent,
                pool_tuple,
                rng,
                mutation_rate=cfg.mutation_rate,
                next_genome_seq=next_genome_seq,
                forced_distant=forced and ci == 0,
            )
            repaired = repair_genome(mutated, pool_tuple, route_domain=route_domain)
            fitc = _evaluate(repaired, pool_tuple, route_domain, evaluated)
            children.append((repaired, fitc))

        scored[:] = elites + children
        sort_pop()
        new_key = deterministic_sort_key(scored[0][0], scored[0][1])
        if _better_key(new_key, pop_best_key):
            stall = 0
        else:
            stall += 1
        pop_best_key = new_key
        generation_done = gen + 1

        hall_key = deterministic_sort_key(best_g, best_f)
        cur_key = deterministic_sort_key(scored[0][0], scored[0][1])
        if _better_key(cur_key, hall_key):
            best_g, best_f = scored[0]
        if scored[0][1].total > initial_best_total + 1e-12:
            improved_flag = True
        if hall_of_fame_total_trace is not None:
            hall_of_fame_total_trace.append(best_f.total)

        if cfg.max_stall_generation > 0 and stall >= cfg.max_stall_generation:
            convergence = EvolutionConvergenceReason.MAX_STALL_GENERATION
            break

        if time_exceeded():
            convergence = EvolutionConvergenceReason.TIME_BUDGET_MS
            break

    if convergence is None:
        if (
            cfg.max_stall_generation == 0
            and not improved_flag
            and math.isclose(
                best_f.total,
                initial_best_total,
            )
        ):
            convergence = EvolutionConvergenceReason.NO_IMPROVEMENT
        else:
            convergence = EvolutionConvergenceReason.MAX_GENERATION

    hall_key = deterministic_sort_key(best_g, best_f)
    cur_key = deterministic_sort_key(scored[0][0], scored[0][1])
    if _better_key(cur_key, hall_key):
        best_g, best_f = scored[0]
    if hall_of_fame_total_trace is not None:
        hall_of_fame_total_trace.append(best_f.total)

    return EvolutionResult(
        best_genome=best_g,
        best_fitness=best_f,
        generation_count=generation_done,
        evaluated_genome_count=evaluated[0],
        convergence_reason=convergence,
    )


__all__ = [
    "compute_population_diversity",
    "deterministic_sort_key",
    "initialize_population",
    "mutate_genome",
    "repair_genome",
    "run_evolutionary_search",
    "tournament_select",
    "validate_evolution_config",
]
