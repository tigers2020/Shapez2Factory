"""Sequence 10B — commit survivability metrics and penalty off/on (narrow bridge)."""

from __future__ import annotations

import json

import pytest

from django_apps.shapez_asteroid.optimization.commit_survivability_metrics import (
    commit_survivability_metrics_to_replay_metrics,
    summarize_incremental_commit,
)
from django_apps.shapez_asteroid.optimization.dto import EvolutionConfig, Gene, Genome
from django_apps.shapez_asteroid.optimization.enums import (
    CommitConflictReason,
    OptimizationReplayEventType,
    PenaltyMode,
)
from django_apps.shapez_asteroid.optimization.evolutionary_search import run_evolutionary_search
from django_apps.shapez_asteroid.optimization.genome_fitness import evaluate_genome
from django_apps.shapez_asteroid.optimization.incremental_commit import commit_best_genome
from django_apps.shapez_asteroid.optimization.optimization_replay import (
    OptimizationReplayRecorder,
    optimization_replay_frame_to_json_dict,
)
from django_apps.shapez_asteroid.optimization.route_domain_snapshot_builder import (
    RouteDomainSnapshotBuilder,
)

from .fixtures.narrow_corridor import (
    build_narrow_bridge_optimization_input,
    build_rim_competition_pool,
)


def _narrow_evo_config() -> EvolutionConfig:
    return EvolutionConfig(
        seed=9001,
        population_size=8,
        elite_count=2,
        mutation_rate=0.35,
        tournament_size=3,
        max_generation=14,
        max_stall_generation=5,
        time_budget_ms=None,
        forced_distant_mutation_period=None,
    )


def test_commit_survivability_metrics_records_attempts_confirmed_and_rollbacks() -> None:
    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, genome = build_rim_competition_pool(inp)
    res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)
    m = summarize_incremental_commit(res)
    assert m.commit_attempt_count == 2
    assert m.commit_confirmed_count == 1
    assert m.commit_rolled_back_count == 1
    assert m.commit_success_ratio == pytest.approx(0.5)


def test_commit_survivability_metrics_records_rollback_reason_counts() -> None:
    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, genome = build_rim_competition_pool(inp)
    res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)
    m = summarize_incremental_commit(res)
    assert m.rollback_reason_counts == ((CommitConflictReason.ROUTE_PROBE_FAILED, 1),)
    assert m.route_probe_failed_count == 1
    assert m.transport_kind_conflict_count == 0


def test_fragility_penalty_off_reproduces_bridge_starvation() -> None:
    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, genome = build_rim_competition_pool(inp)
    res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)
    assert res.rolled_back_candidate_count >= 1
    fb = evaluate_genome(genome, pool, route_domain=None, penalty_mode=PenaltyMode.OFF)
    assert fb.route_fragility_penalty == 0.0
    assert fb.shared_corridor_pressure_penalty == 0.0


def test_fragility_penalty_on_reduces_bridge_starvation() -> None:
    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, _ = build_rim_competition_pool(inp)
    cfg = _narrow_evo_config()
    off = run_evolutionary_search(cfg, pool, route_domain=None, penalty_mode=PenaltyMode.OFF)
    on = run_evolutionary_search(
        cfg, pool, route_domain=None, penalty_mode=PenaltyMode.CONSERVATIVE
    )
    res_off = commit_best_genome(off.best_genome, pool, inp, RouteDomainSnapshotBuilder)
    res_on = commit_best_genome(on.best_genome, pool, inp, RouteDomainSnapshotBuilder)
    assert res_on.rolled_back_candidate_count <= res_off.rolled_back_candidate_count


def test_shared_corridor_pressure_penalty_changes_candidate_ranking() -> None:
    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, dual_genome = build_rim_competition_pool(inp)
    left_id, right_id = pool[0].candidate_id, pool[1].candidate_id
    single_left = Genome(
        "g_one",
        (Gene(left_id, True, 0), Gene(right_id, False, 1)),
        seed=1,
    )
    fb_dual = evaluate_genome(
        dual_genome, pool, route_domain=None, penalty_mode=PenaltyMode.CONSERVATIVE
    )
    fb_single = evaluate_genome(
        single_left, pool, route_domain=None, penalty_mode=PenaltyMode.CONSERVATIVE
    )
    assert fb_dual.shared_corridor_pressure_penalty > 0.0
    assert fb_single.shared_corridor_pressure_penalty == 0.0
    assert fb_single.total > fb_dual.total


def test_replay_records_commit_survivability_metrics() -> None:
    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, genome = build_rim_competition_pool(inp)
    rec = OptimizationReplayRecorder()
    commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder, replay_recorder=rec)
    summary = [
        f
        for f in rec.frames
        if f.event_type is OptimizationReplayEventType.COMMIT_SURVIVABILITY_SUMMARY
    ]
    assert len(summary) == 1
    raw = optimization_replay_frame_to_json_dict(summary[0])
    json.dumps(raw)
    assert raw["metrics"]["commit_success_ratio"] == 0.5
    assert raw["metrics"]["commit_attempt_count"] == 2
    assert raw["metrics"]["rollback_reason_counts"]["route_probe_failed"] == 1
    assert "route_fragility_penalty" in raw["metrics"]
    assert "shared_corridor_pressure_penalty" in raw["metrics"]


def test_commit_survivability_replay_metrics_json_roundtrip() -> None:
    inp, _ = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, genome = build_rim_competition_pool(inp)
    res = commit_best_genome(genome, pool, inp, RouteDomainSnapshotBuilder)
    m = summarize_incremental_commit(res)
    d = commit_survivability_metrics_to_replay_metrics(m)
    json.dumps(d)
    assert d["commit_rolled_back_count"] == 1
    assert d["rollback_reason_counts"]["route_probe_failed"] == 1
