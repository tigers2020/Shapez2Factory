"""Sequence 4 — genome and deterministic fitness evaluation."""

from __future__ import annotations

from dataclasses import fields, replace

import pytest

from django_apps.shapez_asteroid.optimization.coords import Coord
from django_apps.shapez_asteroid.optimization.dto import (
    BundleCandidate,
    FitnessBreakdown,
    FitnessMetrics,
    Gene,
    Genome,
    RouteCellDomain,
    RouteGoal,
    RouteProbeResult,
)
from django_apps.shapez_asteroid.optimization.enums import (
    CardinalDirection,
    RouteClass,
    RouteGoalKind,
    RouteProbeFailureReason,
    TransportKind,
    TransportMask,
)
from django_apps.shapez_asteroid.optimization.genome_fitness import (
    build_fitness_metrics,
    evaluate_genome,
    fitness_breakdown_total_matches_components,
    genome_selected_candidates,
    probe_unreachable_or_stale,
)


def _goal(
    c: Coord,
    *,
    kind: RouteGoalKind,
    priority: int = 1,
    existing_trunk: bool = False,
) -> RouteGoal:
    return RouteGoal(
        coord=c,
        goal_kind=kind,
        transport_kind=None,
        priority=priority,
        existing_trunk=existing_trunk,
    )


def _probe_ok(
    *,
    goal: RouteGoal,
    cost: int = 3,
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


def _probe_unreachable(*, cost: int = 0) -> RouteProbeResult:
    return RouteProbeResult(
        reachable=False,
        path=(),
        cost=cost,
        expanded_nodes=0,
        reached_goal=None,
        goal_priority=None,
        failure_reason=RouteProbeFailureReason.EXHAUSTED,
    )


def _probe_stale_reachable_no_goal() -> RouteProbeResult:
    return RouteProbeResult(
        reachable=True,
        path=(Coord(0, 0),),
        cost=1,
        expanded_nodes=1,
        reached_goal=None,
        goal_priority=None,
        failure_reason=None,
    )


def _bundle(
    candidate_id: str,
    probe: RouteProbeResult,
    *,
    occupied_cells: frozenset[Coord] | None = None,
    throughput: int = 10,
    extensions: tuple[Coord, ...] = (),
) -> BundleCandidate:
    ex = Coord(0, 0)
    cells = occupied_cells if occupied_cells is not None else frozenset({ex})
    return BundleCandidate(
        candidate_id=candidate_id,
        pattern_id="pat",
        topology_signature="topo",
        extractor=ex,
        extensions=extensions,
        occupied_cells=cells,
        output_stub=Coord(1, 0),
        output_dir=CardinalDirection.EAST,
        transport_kind=TransportKind.SHAPE_BELT,
        base_throughput=throughput,
        base_score=float(throughput),
        route_probe_result=probe,
    )


def test_genome_uses_candidate_ids_only() -> None:
    g_margin = _goal(Coord(2, 0), kind=RouteGoalKind.EXTERNAL_MARGIN, priority=2)
    c = _bundle("a", _probe_ok(goal=g_margin))
    genome = Genome(
        genome_id="g1",
        genes=(Gene("a", True, 0), Gene("missing", True, 1)),
        seed=7,
    )
    sel = genome_selected_candidates(genome, (c,))
    assert len(sel) == 1 and sel[0].candidate_id == "a"
    assert all(isinstance(x, Gene) for x in genome.genes)
    assert not any(hasattr(x, "occupied_cells") for x in genome.genes)


def test_duplicate_pool_ids_rejected() -> None:
    g0 = _goal(Coord(0, 0), kind=RouteGoalKind.EXTERNAL_MARGIN)
    a = _bundle("dup", _probe_ok(goal=g0), occupied_cells=frozenset({Coord(0, 0)}))
    b = replace(a, topology_signature="other")
    with pytest.raises(ValueError, match="duplicate candidate_id"):
        genome_selected_candidates(Genome("g", (), 0), (a, b))


def test_fitness_deterministic() -> None:
    g0 = _goal(Coord(0, 0), kind=RouteGoalKind.EXTERNAL_MARGIN, priority=3)
    c = _bundle("x", _probe_ok(goal=g0))
    genome = Genome("g", (Gene("x", True, 1), Gene("x", False, 0)), seed=99)
    p = (c,)
    a = evaluate_genome(genome, p)
    b = evaluate_genome(genome, p)
    assert a == b


def test_overlap_penalty_dominates_throughput_gain() -> None:
    g0 = _goal(Coord(0, 0), kind=RouteGoalKind.EXTERNAL_MARGIN, priority=1)
    shared = frozenset({Coord(5, 5), Coord(5, 6)})
    hi = _bundle("hi", _probe_ok(goal=g0), occupied_cells=shared, throughput=500)
    ov = _bundle("ov", _probe_ok(goal=g0), occupied_cells=shared, throughput=500)
    solo = _bundle(
        "solo", _probe_ok(goal=g0), occupied_cells=frozenset({Coord(9, 9)}), throughput=1
    )
    pool = (hi, ov, solo)
    g_overlap = Genome("go", (Gene("hi", True, 0), Gene("ov", True, 1)), seed=1)
    g_clean = Genome("gc", (Gene("solo", True, 0),), seed=1)
    f_overlap = evaluate_genome(g_overlap, pool)
    f_clean = evaluate_genome(g_clean, pool)
    assert f_overlap.metrics.overlap_count >= 1
    assert f_clean.metrics.overlap_count == 0
    assert f_clean.total > f_overlap.total


def test_unreachable_penalty_dominates_extractor_gain() -> None:
    g0 = _goal(Coord(0, 0), kind=RouteGoalKind.EXTERNAL_MARGIN, priority=1)
    ok_a = _bundle("ok_a", _probe_ok(goal=g0), throughput=1)
    ok_b = _bundle("ok_b", _probe_ok(goal=g0), throughput=1)
    bad = _bundle("bad", _probe_unreachable(), throughput=999)
    pool = (ok_a, ok_b, bad)
    g_two_ok = Genome("two", (Gene("ok_a", True, 0), Gene("ok_b", True, 1)), seed=0)
    g_one_bad = Genome("mix", (Gene("ok_a", True, 0), Gene("bad", True, 1)), seed=0)
    assert evaluate_genome(g_two_ok, pool).total > evaluate_genome(g_one_bad, pool).total


def test_prefers_more_throughput_when_feasible() -> None:
    g0 = _goal(Coord(0, 0), kind=RouteGoalKind.EXTERNAL_MARGIN, priority=1)
    low = _bundle("low", _probe_ok(goal=g0), throughput=5)
    high = _bundle("high", _probe_ok(goal=g0), throughput=80)
    pool = (low, high)
    g_low = Genome("l", (Gene("low", True, 0),), seed=0)
    g_high = Genome("h", (Gene("high", True, 0),), seed=0)
    assert evaluate_genome(g_high, pool).total > evaluate_genome(g_low, pool).total


def test_fitness_breakdown_total_matches_components() -> None:
    g0 = _goal(Coord(0, 0), kind=RouteGoalKind.EXTERNAL_MARGIN, priority=2)
    c = _bundle("c", _probe_ok(goal=g0))
    b = evaluate_genome(Genome("g", (Gene("c", True, 0),), seed=0), (c,))
    assert fitness_breakdown_total_matches_components(b)


def test_fitness_metrics_populated() -> None:
    g0 = _goal(Coord(0, 0), kind=RouteGoalKind.EXTERNAL_MARGIN, priority=1)
    ext_coord = Coord(0, 1)
    c = _bundle(
        "c",
        _probe_ok(goal=g0, path=(Coord(0, 0), ext_coord)),
        extensions=(ext_coord,),
        throughput=4,
    )
    m = build_fitness_metrics((c,))
    assert m.selected_candidate_count == 1
    assert m.extractor_count == 1
    assert m.extension_count == 1
    assert m.overlap_count == 0
    assert m.unreachable_count == 0
    assert m.total_route_cost == c.route_probe_result.cost
    assert m.max_trunk_sharing == 0
    assert m.narrow_passage_occupied_count == 0


def test_route_goal_quality_prefers_trunk_over_margin_when_reachable_both() -> None:
    c_trunk = Coord(1, 1)
    c_margin = Coord(2, 2)
    g_trunk = _goal(c_trunk, kind=RouteGoalKind.TRUNK_SEED, priority=1, existing_trunk=True)
    g_margin = _goal(c_margin, kind=RouteGoalKind.EXTERNAL_MARGIN, priority=1, existing_trunk=False)
    b_trunk = _bundle("t", _probe_ok(goal=g_trunk))
    b_margin = _bundle("m", _probe_ok(goal=g_margin))
    qt = evaluate_genome(
        Genome("gt", (Gene("t", True, 0),), 0), (b_trunk,)
    ).route_goal_quality_score
    qm = evaluate_genome(
        Genome("gm", (Gene("m", True, 0),), 0), (b_margin,)
    ).route_goal_quality_score
    assert qt > qm


def test_narrow_corridor_hook_fields_exist() -> None:
    g0 = _goal(Coord(0, 0), kind=RouteGoalKind.EXTERNAL_MARGIN, priority=1)
    path = (Coord(0, 0), Coord(1, 0))
    c = _bundle("c", _probe_ok(goal=g0, path=path))
    domain = {
        Coord(0, 0): RouteCellDomain(
            Coord(0, 0),
            RouteClass.STANDARD,
            1,
            False,
            False,
            TransportMask.BOTH,
        ),
        Coord(1, 0): RouteCellDomain(
            Coord(1, 0),
            RouteClass.NARROW_CORRIDOR,
            1,
            False,
            False,
            TransportMask.BOTH,
        ),
    }
    b = evaluate_genome(Genome("g", (Gene("c", True, 0),), 0), (c,), route_domain=domain)
    assert b.metrics.narrow_passage_occupied_count == 1
    assert hasattr(b, "narrow_passage_penalty")
    assert b.narrow_passage_penalty == 0.0


def test_all_required_breakdown_fields_present_even_when_zero() -> None:
    g0 = _goal(Coord(0, 0), kind=RouteGoalKind.EXTERNAL_MARGIN, priority=1)
    c = _bundle("c", _probe_ok(goal=g0))
    b = evaluate_genome(Genome("g", (Gene("c", True, 0),), 0), (c,))
    names = {f.name for f in fields(FitnessBreakdown)} - {"metrics"}
    for n in names:
        assert hasattr(b, n)
    m_names = {f.name for f in fields(FitnessMetrics)}
    for n in m_names:
        assert hasattr(b.metrics, n)


def test_evaluation_does_not_mutate_candidate_pool() -> None:
    g0 = _goal(Coord(0, 0), kind=RouteGoalKind.EXTERNAL_MARGIN, priority=1)
    c = _bundle("c", _probe_ok(goal=g0), occupied_cells=frozenset({Coord(3, 3)}))
    before_cells = c.occupied_cells
    before_probe = c.route_probe_result
    pool = (c,)
    evaluate_genome(Genome("g", (Gene("c", True, 0),), 0), pool)
    assert c.occupied_cells == before_cells
    assert c.route_probe_result == before_probe


def test_same_input_same_breakdown() -> None:
    g0 = _goal(Coord(0, 0), kind=RouteGoalKind.EXTERNAL_MARGIN, priority=4)
    c = _bundle("c", _probe_ok(goal=g0))
    genome = Genome("g", (Gene("c", True, 2), Gene("c", False, 1)), seed=123)
    pool = (c,)
    assert evaluate_genome(genome, pool) == evaluate_genome(genome, tuple(pool))


def test_stale_unreachable_candidate_handled_deterministically() -> None:
    stale = _bundle("stale", _probe_stale_reachable_no_goal())
    assert probe_unreachable_or_stale(stale.route_probe_result)
    b = evaluate_genome(Genome("g", (Gene("stale", True, 0),), 0), (stale,))
    assert b.metrics.unreachable_count == 1
    assert b.unreachable_penalty == 20_000.0


def test_unknown_enabled_gene_ignored_deterministically() -> None:
    g0 = _goal(Coord(0, 0), kind=RouteGoalKind.EXTERNAL_MARGIN, priority=1)
    c = _bundle("only", _probe_ok(goal=g0))
    genome = Genome("g", (Gene("ghost", True, 0), Gene("only", True, 1)), seed=0)
    sel = genome_selected_candidates(genome, (c,))
    assert tuple(x.candidate_id for x in sel) == ("only",)
