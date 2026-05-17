"""Deterministic genome evaluation and fitness breakdown (Sequence 4)."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from django_apps.shapez_asteroid.optimization.coords import Coord
from django_apps.shapez_asteroid.optimization.dto import (
    BundleCandidate,
    FitnessBreakdown,
    FitnessMetrics,
    Genome,
    RouteCellDomain,
    RouteProbeResult,
)
from django_apps.shapez_asteroid.optimization.enums import PenaltyMode, RouteClass, RouteGoalKind

# v0 weights (tunable; documented in asteroid_lab_05_genome_fitness.md)
_W_EXTRACTOR = 1000
_W_EXTENSION = 250
_W_ROUTE_COST = 5
_W_OVERLAP = 10_000
_W_UNREACHABLE = 20_000


def _pool_by_id(pool: Sequence[BundleCandidate]) -> dict[str, BundleCandidate]:
    out: dict[str, BundleCandidate] = {}
    for c in sorted(pool, key=lambda z: z.candidate_id):
        if c.candidate_id in out:
            raise ValueError(f"duplicate candidate_id in pool: {c.candidate_id!r}")
        out[c.candidate_id] = c
    return out


def genome_selected_candidates(
    genome: Genome,
    candidate_pool: Sequence[BundleCandidate],
) -> tuple[BundleCandidate, ...]:
    """Enabled genes that resolve to known pool ids; each id at most once; deterministic order."""

    by_id = _pool_by_id(candidate_pool)
    enabled_known = frozenset(
        g.candidate_id for g in genome.genes if g.enabled and g.candidate_id in by_id
    )
    return tuple(by_id[cid] for cid in sorted(enabled_known))


def probe_unreachable_or_stale(probe: RouteProbeResult) -> bool:
    """Unreachable or defensive stale snapshot (deterministic, probe-only)."""

    if not probe.reachable:
        return True
    if probe.reached_goal is None:
        return True
    if probe.goal_priority is None:
        return True
    if probe.failure_reason is not None:
        return True
    return False


def compute_overlap_metrics(selected: Sequence[BundleCandidate]) -> int:
    """Count distinct occupied cells used by more than one selected candidate."""

    counts: dict[Coord, int] = {}
    for cand in sorted(selected, key=lambda z: z.candidate_id):
        for cell in sorted(cand.occupied_cells, key=lambda z: (z.x, z.y)):
            counts[cell] = counts.get(cell, 0) + 1
    return sum(1 for _c, k in sorted(counts.items(), key=lambda z: (z[0].x, z[0].y)) if k > 1)


def _goal_kind_quality_tier(goal_kind: RouteGoalKind) -> float:
    if goal_kind is RouteGoalKind.EXISTING_TRANSPORT_ATTACHMENT:
        return 90.0
    if goal_kind is RouteGoalKind.TRUNK_SEED:
        return 85.0
    if goal_kind is RouteGoalKind.SOFT_CORRIDOR:
        return 65.0
    if goal_kind is RouteGoalKind.CORRIDOR_ENTRY:
        return 60.0
    if goal_kind is RouteGoalKind.EXTERNAL_MARGIN:
        return 40.0
    return 0.0


def compute_route_goal_quality(probe: RouteProbeResult) -> float:
    """Quality from probe snapshot only; 0 if unreachable/stale."""

    if probe_unreachable_or_stale(probe):
        return 0.0
    assert probe.reached_goal is not None
    rg = probe.reached_goal
    q = _goal_kind_quality_tier(rg.goal_kind)
    if rg.existing_trunk:
        q += 100.0
    return q


def compute_route_goal_priority_penalty(probe: RouteProbeResult) -> float:
    """Lower ``RouteGoal.priority`` is better; penalty scales with stored priority."""

    if probe_unreachable_or_stale(probe):
        return 0.0
    assert probe.goal_priority is not None
    return float(probe.goal_priority)


def _route_fragility_penalty_value(
    selected: Sequence[BundleCandidate],
    route_domain: Mapping[Coord, RouteCellDomain] | None,
) -> float:
    """Narrow-corridor traversals on probe paths (deterministic; pre-commit heuristic)."""

    total = 0.0
    for cand in sorted(selected, key=lambda z: z.candidate_id):
        pr = cand.route_probe_result
        if probe_unreachable_or_stale(pr):
            continue
        for cell in pr.path:
            if route_domain is None:
                total += 50.0
            else:
                dom = route_domain.get(cell)
                if dom is not None and dom.route_class is RouteClass.NARROW_CORRIDOR:
                    total += 80.0
    return total


def _shared_cell_weight_for_domain(dom: RouteCellDomain | None) -> float:
    if dom is None:
        return 0.0
    if dom.route_class is RouteClass.NARROW_CORRIDOR:
        return 1500.0
    if dom.route_class is RouteClass.PREFERRED_TRUNK:
        return 400.0
    return 100.0


def _shared_corridor_pressure_penalty_value(
    selected: Sequence[BundleCandidate],
    route_domain: Mapping[Coord, RouteCellDomain] | None,
) -> float:
    """Penalty when multiple selected candidates share route cells (deterministic)."""

    path_sets: list[set[Coord]] = []
    for cand in sorted(selected, key=lambda z: z.candidate_id):
        pr = cand.route_probe_result
        if probe_unreachable_or_stale(pr):
            continue
        path_sets.append(set(pr.path))
    if len(path_sets) < 2:
        return 0.0
    shared: set[Coord] = set()
    for i in range(len(path_sets)):
        for j in range(i + 1, len(path_sets)):
            shared |= path_sets[i] & path_sets[j]
    weight = 0.0
    for cell in sorted(shared, key=lambda z: (z.x, z.y)):
        if route_domain is None:
            weight += 900.0
        else:
            weight += _shared_cell_weight_for_domain(route_domain.get(cell))
    return weight


def compute_conservative_penalties(
    selected: Sequence[BundleCandidate],
    route_domain: Mapping[Coord, RouteCellDomain] | None,
    *,
    penalty_mode: PenaltyMode = PenaltyMode.OFF,
) -> tuple[
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
]:
    """Nine-tuple aligns with ``build_fitness_breakdown`` penalty slots (v0 + Sequence 10B)."""

    if penalty_mode is not PenaltyMode.CONSERVATIVE:
        return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    route_fragility = _route_fragility_penalty_value(selected, route_domain)
    shared_pressure = _shared_corridor_pressure_penalty_value(selected, route_domain)
    return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, route_fragility, shared_pressure)


def _narrow_passage_occupied_count(
    selected: Sequence[BundleCandidate],
    route_domain: Mapping[Coord, RouteCellDomain] | None,
) -> int:
    if route_domain is None:
        return 0
    total = 0
    for cand in sorted(selected, key=lambda z: z.candidate_id):
        pr = cand.route_probe_result
        if probe_unreachable_or_stale(pr):
            continue
        for cell in pr.path:
            dom = route_domain.get(cell)
            if dom is not None and dom.route_class is RouteClass.NARROW_CORRIDOR:
                total += 1
    return total


def build_fitness_metrics(
    selected: tuple[BundleCandidate, ...],
    *,
    route_domain: Mapping[Coord, RouteCellDomain] | None = None,
) -> FitnessMetrics:
    overlap_count = compute_overlap_metrics(selected)
    unreachable_count = sum(1 for c in selected if probe_unreachable_or_stale(c.route_probe_result))
    extractor_count = len(selected)
    extension_count = sum(len(c.extensions) for c in sorted(selected, key=lambda z: z.candidate_id))
    total_route_cost = sum(
        c.route_probe_result.cost
        for c in selected
        if not probe_unreachable_or_stale(c.route_probe_result)
    )
    narrow_passage_occupied_count = _narrow_passage_occupied_count(selected, route_domain)
    return FitnessMetrics(
        selected_candidate_count=len(selected),
        extractor_count=extractor_count,
        extension_count=extension_count,
        overlap_count=overlap_count,
        unreachable_count=unreachable_count,
        total_route_cost=total_route_cost,
        max_trunk_sharing=0,
        narrow_passage_occupied_count=narrow_passage_occupied_count,
    )


def build_fitness_breakdown(
    metrics: FitnessMetrics,
    *,
    throughput_score: float,
    route_goal_quality_score: float,
    route_goal_priority_penalty: float,
    congestion_penalty: float,
    orphan_penalty: float,
    corridor_block_penalty: float,
    future_expansion_penalty: float,
    narrow_passage_penalty: float,
    trunk_sharing_penalty: float,
    dead_end_penalty: float,
    route_fragility_penalty: float,
    shared_corridor_pressure_penalty: float,
) -> FitnessBreakdown:
    extractor_score = float(metrics.extractor_count) * _W_EXTRACTOR
    extension_score = float(metrics.extension_count) * _W_EXTENSION
    route_cost_penalty = float(metrics.total_route_cost) * _W_ROUTE_COST
    overlap_penalty = float(metrics.overlap_count) * _W_OVERLAP
    unreachable_penalty = float(metrics.unreachable_count) * _W_UNREACHABLE

    positives = extractor_score + extension_score + throughput_score + route_goal_quality_score
    penalties = (
        route_cost_penalty
        + route_goal_priority_penalty
        + overlap_penalty
        + unreachable_penalty
        + congestion_penalty
        + orphan_penalty
        + corridor_block_penalty
        + future_expansion_penalty
        + narrow_passage_penalty
        + trunk_sharing_penalty
        + dead_end_penalty
        + route_fragility_penalty
        + shared_corridor_pressure_penalty
    )
    total = positives - penalties

    return FitnessBreakdown(
        extractor_score=extractor_score,
        extension_score=extension_score,
        throughput_score=throughput_score,
        route_cost_penalty=route_cost_penalty,
        overlap_penalty=overlap_penalty,
        unreachable_penalty=unreachable_penalty,
        congestion_penalty=congestion_penalty,
        orphan_penalty=orphan_penalty,
        corridor_block_penalty=corridor_block_penalty,
        future_expansion_penalty=future_expansion_penalty,
        narrow_passage_penalty=narrow_passage_penalty,
        trunk_sharing_penalty=trunk_sharing_penalty,
        dead_end_penalty=dead_end_penalty,
        route_goal_quality_score=route_goal_quality_score,
        route_goal_priority_penalty=route_goal_priority_penalty,
        route_fragility_penalty=route_fragility_penalty,
        shared_corridor_pressure_penalty=shared_corridor_pressure_penalty,
        total=total,
        metrics=metrics,
    )


def evaluate_genome(
    genome: Genome,
    candidate_pool: Sequence[BundleCandidate],
    *,
    route_domain: Mapping[Coord, RouteCellDomain] | None = None,
    penalty_mode: PenaltyMode = PenaltyMode.OFF,
) -> FitnessBreakdown:
    """Evaluate ``genome`` against ``candidate_pool`` without mutating pool or candidates."""

    _ = genome.seed  # reserved for future evolution tie-break; not used in fitness v0
    selected = genome_selected_candidates(genome, candidate_pool)
    metrics = build_fitness_metrics(selected, route_domain=route_domain)

    ordered = tuple(sorted(selected, key=lambda z: z.candidate_id))
    throughput_score = float(sum(c.base_throughput for c in ordered))
    route_goal_quality_score = float(
        sum(compute_route_goal_quality(c.route_probe_result) for c in ordered)
    )
    route_goal_priority_penalty = float(
        sum(compute_route_goal_priority_penalty(c.route_probe_result) for c in ordered)
    )

    (
        congestion_penalty,
        orphan_penalty,
        corridor_block_penalty,
        future_expansion_penalty,
        narrow_passage_penalty,
        trunk_sharing_penalty,
        dead_end_penalty,
        route_fragility_penalty,
        shared_corridor_pressure_penalty,
    ) = compute_conservative_penalties(ordered, route_domain, penalty_mode=penalty_mode)

    return build_fitness_breakdown(
        metrics,
        throughput_score=throughput_score,
        route_goal_quality_score=route_goal_quality_score,
        route_goal_priority_penalty=route_goal_priority_penalty,
        congestion_penalty=congestion_penalty,
        orphan_penalty=orphan_penalty,
        corridor_block_penalty=corridor_block_penalty,
        future_expansion_penalty=future_expansion_penalty,
        narrow_passage_penalty=narrow_passage_penalty,
        trunk_sharing_penalty=trunk_sharing_penalty,
        dead_end_penalty=dead_end_penalty,
        route_fragility_penalty=route_fragility_penalty,
        shared_corridor_pressure_penalty=shared_corridor_pressure_penalty,
    )


def fitness_breakdown_total_matches_components(b: FitnessBreakdown) -> bool:
    """Tie-safe recomputation for tests."""

    positives = (
        b.extractor_score + b.extension_score + b.throughput_score + b.route_goal_quality_score
    )
    penalties = (
        b.route_cost_penalty
        + b.route_goal_priority_penalty
        + b.overlap_penalty
        + b.unreachable_penalty
        + b.congestion_penalty
        + b.orphan_penalty
        + b.corridor_block_penalty
        + b.future_expansion_penalty
        + b.narrow_passage_penalty
        + b.trunk_sharing_penalty
        + b.dead_end_penalty
        + b.route_fragility_penalty
        + b.shared_corridor_pressure_penalty
    )
    expected = positives - penalties
    return math.isclose(b.total, expected, rel_tol=0.0, abs_tol=1e-9)
