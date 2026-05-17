"""Sequence 5 — deterministic evolutionary search (candidate ids only)."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest

from django_apps.shapez_asteroid.optimization.coords import Coord
from django_apps.shapez_asteroid.optimization.dto import (
    BundleCandidate,
    EvolutionConfig,
    EvolutionResult,
    Gene,
    Genome,
    RouteCellDomain,
    RouteGoal,
    RouteProbeResult,
)
from django_apps.shapez_asteroid.optimization.enums import (
    CardinalDirection,
    EvolutionConvergenceReason,
    RouteClass,
    RouteGoalKind,
    RouteProbeFailureReason,
    TransportKind,
    TransportMask,
)
from django_apps.shapez_asteroid.optimization.evolutionary_search import (
    _reassign_commit_order,
    compute_population_diversity,
    deterministic_sort_key,
    initialize_population,
    mutate_genome,
    repair_genome,
    run_evolutionary_search,
    tournament_select,
    validate_evolution_config,
)
from django_apps.shapez_asteroid.optimization.genome_fitness import evaluate_genome


def _goal(
    c: Coord,
    *,
    kind: RouteGoalKind = RouteGoalKind.EXTERNAL_MARGIN,
    priority: int = 1,
) -> RouteGoal:
    return RouteGoal(
        coord=c,
        goal_kind=kind,
        transport_kind=None,
        priority=priority,
        existing_trunk=False,
    )


def _probe_ok(
    *,
    goal: RouteGoal,
    cost: int = 2,
    path: tuple[Coord, ...] | None = None,
) -> RouteProbeResult:
    c0 = goal.coord
    return RouteProbeResult(
        reachable=True,
        path=path or (c0,),
        cost=cost,
        expanded_nodes=1,
        reached_goal=goal,
        goal_priority=goal.priority,
        failure_reason=None,
    )


def _probe_bad() -> RouteProbeResult:
    return RouteProbeResult(
        reachable=False,
        path=(),
        cost=0,
        expanded_nodes=0,
        reached_goal=None,
        goal_priority=None,
        failure_reason=RouteProbeFailureReason.EXHAUSTED,
    )


def _bundle(
    candidate_id: str,
    probe: RouteProbeResult,
    *,
    extractor: Coord | None = None,
    occupied: frozenset[Coord] | None = None,
    throughput: int = 10,
) -> BundleCandidate:
    ex = extractor or Coord(0, 0)
    cells = occupied if occupied is not None else frozenset({ex})
    return BundleCandidate(
        candidate_id=candidate_id,
        pattern_id="p",
        topology_signature=f"sig-{candidate_id}",
        extractor=ex,
        extensions=(),
        occupied_cells=cells,
        output_stub=Coord(1, 0),
        output_dir=CardinalDirection.EAST,
        transport_kind=TransportKind.SHAPE_BELT,
        base_throughput=throughput,
        base_score=float(throughput),
        route_probe_result=probe,
    )


def _small_config(**overrides: object) -> EvolutionConfig:
    base = dict(
        seed=4242,
        population_size=6,
        elite_count=2,
        mutation_rate=0.55,
        tournament_size=3,
        max_generation=4,
        max_stall_generation=0,
        time_budget_ms=None,
        forced_distant_mutation_period=None,
    )
    base.update(overrides)
    return EvolutionConfig(**base)  # type: ignore[arg-type]


def test_tournament_select_deterministic() -> None:
    g0 = _goal(Coord(0, 0))
    c = _bundle("a", _probe_ok(goal=g0))
    g1 = Genome("g1", (Gene("a", True, 0),), 0)
    g2 = Genome("g2", (Gene("a", True, 0),), 0)
    f1 = evaluate_genome(g1, (c,))
    f2 = evaluate_genome(g2, (c,))
    scored = [(g1, f1), (g2, f2)]
    rng = __import__("random").Random(123)
    a = tournament_select(scored, rng, tournament_size=2)
    rng2 = __import__("random").Random(123)
    b = tournament_select(scored, rng2, tournament_size=2)
    assert a == b


def test_same_seed_deterministic() -> None:
    g0 = _goal(Coord(0, 0))
    pool = (
        _bundle("a", _probe_ok(goal=g0), throughput=10),
        _bundle("b", _probe_ok(goal=g0), throughput=20, extractor=Coord(2, 0)),
    )
    cfg = _small_config()
    r1 = run_evolutionary_search(cfg, pool)
    r2 = run_evolutionary_search(cfg, pool)
    assert r1 == r2


def test_hall_of_fame_total_non_decreasing() -> None:
    g0 = _goal(Coord(0, 0))
    pool = (
        _bundle("a", _probe_ok(goal=g0)),
        _bundle("b", _probe_ok(goal=g0), extractor=Coord(3, 0)),
    )
    trace: list[float] = []
    run_evolutionary_search(
        _small_config(mutation_rate=0.4, max_generation=8),
        pool,
        hall_of_fame_total_trace=trace,
    )
    for i in range(1, len(trace)):
        assert trace[i] + 1e-9 >= trace[i - 1]


def test_mutation_keeps_valid_candidate_ids() -> None:
    g0 = _goal(Coord(0, 0))
    pool = (
        _bundle("x", _probe_ok(goal=g0)),
        _bundle("y", _probe_ok(goal=g0), extractor=Coord(1, 0)),
    )
    rng = __import__("random").Random(99)
    g = Genome("t", (Gene("x", True, 0),), seed=1)
    seq = [0]
    known = {c.candidate_id for c in pool}
    for _ in range(40):
        m = mutate_genome(
            g,
            pool,
            rng,
            mutation_rate=1.0,
            next_genome_seq=seq,
            forced_distant=False,
        )
        for gg in m.genes:
            assert gg.candidate_id in known
        g = m


def test_repair_removes_overlap() -> None:
    g0 = _goal(Coord(0, 0))
    shared = frozenset({Coord(5, 5)})
    pool = (
        _bundle("p", _probe_ok(goal=g0), occupied=shared),
        _bundle("q", _probe_ok(goal=g0), occupied=shared, extractor=Coord(1, 0)),
    )
    g = Genome("ov", (Gene("p", True, 0), Gene("q", True, 1)), seed=0)
    r = repair_genome(g, pool)
    sel = [x for x in r.genes if x.enabled]
    assert len(sel) <= 1 or evaluate_genome(r, pool).metrics.overlap_count == 0


def test_repair_removes_unreachable() -> None:
    g0 = _goal(Coord(0, 0))
    pool = (
        _bundle("ok", _probe_ok(goal=g0)),
        _bundle("bad", _probe_bad()),
    )
    g = Genome("u", (Gene("ok", True, 0), Gene("bad", True, 1)), seed=0)
    r = repair_genome(g, pool)
    assert not any(
        gg.enabled and gg.candidate_id == "bad" for gg in r.genes
    ), "unreachable gene should be disabled"


def test_no_duplicate_enabled_candidate_ids_after_repair() -> None:
    g0 = _goal(Coord(0, 0))
    pool = (_bundle("d", _probe_ok(goal=g0)),)
    g = Genome(
        "dup",
        (
            Gene("d", True, 0),
            Gene("d", True, 1),
        ),
        seed=0,
    )
    r = repair_genome(g, pool)
    enabled_ids = [gg.candidate_id for gg in r.genes if gg.enabled]
    assert len(enabled_ids) == len(frozenset(enabled_ids))


def test_dedupe_keeps_lowest_commit_order_for_duplicate_id() -> None:
    """Duplicate candidate_id: representative is earliest commit_order, not list order."""

    g0 = _goal(Coord(0, 0))
    pool = (_bundle("d", _probe_ok(goal=g0)),)
    g = Genome(
        "dupco",
        (
            Gene("d", True, 9),
            Gene("d", True, 0),
        ),
        seed=0,
    )
    r = repair_genome(g, pool)
    enabled = [gg for gg in r.genes if gg.enabled and gg.candidate_id == "d"]
    assert len(enabled) == 1
    assert enabled[0].commit_order == 0


def test_convergence_reason_enum() -> None:
    g0 = _goal(Coord(0, 0))
    pool = (_bundle("solo", _probe_ok(goal=g0)),)
    r = run_evolutionary_search(
        _small_config(
            population_size=4,
            elite_count=1,
            mutation_rate=0.0,
            max_generation=3,
            max_stall_generation=0,
        ),
        pool,
    )
    assert isinstance(r.convergence_reason, EvolutionConvergenceReason)
    assert r.convergence_reason == EvolutionConvergenceReason.NO_IMPROVEMENT


def test_fitness_tie_break_deterministic() -> None:
    g0 = _goal(Coord(0, 0))
    c = _bundle("z", _probe_ok(goal=g0))
    base = evaluate_genome(Genome("x", (Gene("z", True, 0),), 0), (c,))
    m_hi = replace(base.metrics, selected_candidate_count=3)
    m_lo = replace(base.metrics, selected_candidate_count=1)
    f_hi = replace(base, total=100.0, metrics=m_hi)
    f_lo = replace(base, total=100.0, metrics=m_lo)
    assert deterministic_sort_key(Genome("b", (), 0), f_hi) < deterministic_sort_key(
        Genome("b", (), 0), f_lo
    )
    assert deterministic_sort_key(Genome("a", (), 0), f_hi) < deterministic_sort_key(
        Genome("b", (), 0), f_hi
    )


def test_forced_distant_mutation_period_deterministic() -> None:
    g0 = _goal(Coord(0, 0))
    pool = (
        _bundle("c0", _probe_ok(goal=g0), extractor=Coord(0, 0)),
        _bundle("c1", _probe_ok(goal=g0), extractor=Coord(10, 0)),
        _bundle("c2", _probe_ok(goal=g0), extractor=Coord(0, 10)),
    )
    parent = Genome(
        "p",
        (
            Gene("c0", True, 0),
            Gene("c1", True, 1),
            Gene("c2", True, 2),
        ),
        seed=1,
    )
    rng_a = __import__("random").Random(5)
    rng_b = __import__("random").Random(5)
    a = mutate_genome(
        parent,
        pool,
        rng_a,
        mutation_rate=0.0,
        next_genome_seq=[0],
        forced_distant=False,
    )
    b = mutate_genome(
        parent,
        pool,
        rng_b,
        mutation_rate=0.0,
        next_genome_seq=[0],
        forced_distant=True,
    )
    assert a.genes != b.genes or a.genome_id != b.genome_id


def test_population_initialization_deterministic() -> None:
    g0 = _goal(Coord(0, 0))
    pool = tuple(_bundle(chr(97 + i), _probe_ok(goal=g0), extractor=Coord(i, 0)) for i in range(5))
    cfg = _small_config(seed=777, population_size=5)
    rng1 = __import__("random").Random(cfg.seed)
    rng2 = __import__("random").Random(cfg.seed)
    a = initialize_population(cfg, pool, rng1, next_genome_seq=[0])
    b = initialize_population(cfg, pool, rng2, next_genome_seq=[0])
    assert [x.genes for x in a] == [x.genes for x in b]


def test_candidate_pool_not_mutated() -> None:
    g0 = _goal(Coord(0, 0))
    pool = [
        _bundle("a", _probe_ok(goal=g0)),
        _bundle("b", _probe_ok(goal=g0), extractor=Coord(2, 0)),
    ]
    snap = deepcopy(pool)
    run_evolutionary_search(_small_config(), tuple(pool))
    assert pool[0].occupied_cells == snap[0].occupied_cells
    assert pool[1].route_probe_result == snap[1].route_probe_result


def test_reassign_commit_order_respects_commit_order_not_candidate_id() -> None:
    """Regression: candidate_id lexicographic sort must not erase commit_order semantics."""

    genes = (
        Gene("z", True, 0),
        Gene("a", True, 1),
    )
    out = _reassign_commit_order(genes)
    assert [g.candidate_id for g in out] == ["z", "a"]
    assert [g.commit_order for g in out] == [0, 1]


def test_repair_unreachable_before_bundle_limit() -> None:
    """Unreachable slots should not consume limit before they are disabled."""

    g0 = _goal(Coord(0, 0))
    pool = (
        _bundle("hi", _probe_ok(goal=g0), throughput=100),
        _bundle("lo", _probe_ok(goal=g0), throughput=1, extractor=Coord(1, 0)),
        _bundle("bad", _probe_bad(), throughput=50, extractor=Coord(2, 0)),
    )
    g = Genome(
        "lim",
        (
            Gene("bad", True, 0),
            Gene("hi", True, 1),
            Gene("lo", True, 2),
        ),
        seed=0,
    )
    r = repair_genome(g, pool)
    assert any(gg.enabled and gg.candidate_id == "hi" for gg in r.genes), (
        "high-throughput reachable should survive after unreachable is dropped "
        "before bundle limit"
    )


def test_genome_commit_order_preserved_under_zero_mutation() -> None:
    g0 = _goal(Coord(0, 0))
    pool = (
        _bundle("a", _probe_ok(goal=g0)),
        _bundle("b", _probe_ok(goal=g0), extractor=Coord(2, 0)),
    )
    g = Genome(
        "co",
        (
            Gene("a", True, 5),
            Gene("b", True, 2),
        ),
        seed=1,
    )
    rng = __import__("random").Random(0)
    seq = [0]
    m = mutate_genome(g, pool, rng, mutation_rate=0.0, next_genome_seq=seq, forced_distant=False)
    assert tuple((x.candidate_id, x.commit_order, x.enabled) for x in m.genes) == tuple(
        (x.candidate_id, x.commit_order, x.enabled) for x in g.genes
    )


def test_no_cell_level_genome_generation() -> None:
    g0 = _goal(Coord(0, 0))
    pool = (_bundle("only", _probe_ok(goal=g0)),)
    rng = __import__("random").Random(3)
    seq = [0]
    m = mutate_genome(
        Genome("x", (Gene("only", True, 0),), 0),
        pool,
        rng,
        mutation_rate=1.0,
        next_genome_seq=seq,
        forced_distant=False,
    )
    for gg in m.genes:
        assert hasattr(gg, "candidate_id") and isinstance(gg.candidate_id, str)
        assert not hasattr(gg, "coord")


def test_evolution_result_populated() -> None:
    g0 = _goal(Coord(0, 0))
    pool = (
        _bundle("a", _probe_ok(goal=g0)),
        _bundle("b", _probe_ok(goal=g0), extractor=Coord(4, 0)),
    )
    r = run_evolutionary_search(_small_config(), pool)
    assert isinstance(r, EvolutionResult)
    assert r.generation_count >= 1
    assert r.evaluated_genome_count >= r.generation_count
    assert r.best_genome.genes
    assert r.best_fitness.metrics.selected_candidate_count >= 0


def test_max_stall_generation_convergence() -> None:
    g0 = _goal(Coord(0, 0))
    pool = (_bundle("only", _probe_ok(goal=g0)),)
    r = run_evolutionary_search(
        _small_config(
            population_size=4,
            elite_count=1,
            mutation_rate=0.0,
            max_generation=20,
            max_stall_generation=2,
        ),
        pool,
    )
    assert r.convergence_reason == EvolutionConvergenceReason.MAX_STALL_GENERATION


def test_time_budget_convergence(monkeypatch: pytest.MonkeyPatch) -> None:
    g0 = _goal(Coord(0, 0))
    pool = (
        _bundle("a", _probe_ok(goal=g0)),
        _bundle("b", _probe_ok(goal=g0), extractor=Coord(2, 0)),
    )
    t = iter([0.0, 1000.0])

    def fake_perf() -> float:
        return next(t)

    monkeypatch.setattr(
        "django_apps.shapez_asteroid.optimization.evolutionary_search.time.perf_counter",
        fake_perf,
    )
    r = run_evolutionary_search(
        _small_config(max_generation=50, time_budget_ms=1),
        pool,
    )
    assert r.convergence_reason == EvolutionConvergenceReason.TIME_BUDGET_MS


def test_candidate_pool_exhausted_empty_pool() -> None:
    r = run_evolutionary_search(_small_config(population_size=2, elite_count=1), ())
    assert r.convergence_reason == EvolutionConvergenceReason.CANDIDATE_POOL_EXHAUSTED


def test_validate_evolution_config_rejects_bad_elite() -> None:
    with pytest.raises(ValueError, match="elite_count"):
        validate_evolution_config(
            EvolutionConfig(
                seed=1,
                population_size=3,
                elite_count=3,
                mutation_rate=0.5,
                tournament_size=2,
                max_generation=2,
                max_stall_generation=0,
                time_budget_ms=None,
                forced_distant_mutation_period=None,
            )
        )


def test_genome_diversity_metrics_fields() -> None:
    g0 = _goal(Coord(0, 0))
    pool = (
        _bundle("a", _probe_ok(goal=g0)),
        _bundle("b", _probe_ok(goal=g0), extractor=Coord(2, 0)),
    )
    pop = [
        Genome("1", (Gene("a", True, 0),), 0),
        Genome("2", (Gene("b", True, 0),), 0),
    ]
    d = compute_population_diversity(pop, pool)
    assert d.distinct_topology_signatures >= 1
    assert isinstance(d.rim_cell_entropy_bits, float)
    assert isinstance(d.transport_kind_mix_score, float)


def test_repair_corridor_blocker_with_domain() -> None:
    g0 = _goal(Coord(0, 0))
    path = (Coord(0, 0), Coord(1, 0))
    pool = (
        _bundle(
            "n",
            _probe_ok(goal=g0, cost=1, path=path),
            extractor=Coord(0, 0),
            occupied=frozenset({Coord(0, 0)}),
        ),
    )
    dom = {
        Coord(0, 0): RouteCellDomain(
            Coord(0, 0), RouteClass.STANDARD, 1, False, False, TransportMask.BOTH
        ),
        Coord(1, 0): RouteCellDomain(
            Coord(1, 0), RouteClass.NARROW_CORRIDOR, 1, False, False, TransportMask.BOTH
        ),
    }
    g = Genome("blk", (Gene("n", True, 0),), seed=0)
    r = repair_genome(g, pool, route_domain=dom)
    assert not any(gg.enabled and gg.candidate_id == "n" for gg in r.genes)


def test_evolution_convergence_reason_members() -> None:
    assert frozenset(EvolutionConvergenceReason) == frozenset(
        {
            EvolutionConvergenceReason.MAX_GENERATION,
            EvolutionConvergenceReason.MAX_STALL_GENERATION,
            EvolutionConvergenceReason.TIME_BUDGET_MS,
            EvolutionConvergenceReason.NO_IMPROVEMENT,
            EvolutionConvergenceReason.CANDIDATE_POOL_EXHAUSTED,
        }
    )
