"""PR-GA-1 — GA evolution observe-only shadow."""

from __future__ import annotations

from dataclasses import replace

import pytest

from django_apps.asteroid_lab.contracts.ga_evolution_shadow import (
    GaEvolutionShadowConfig,
    GaEvolutionShadowSummary,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    BundleCandidate,
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.pattern_library import build_pattern_library
from django_apps.asteroid_lab.optimization.commit.incremental_commit import incremental_commit
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpPipelineConfig,
    RttpSkeletonConfig,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.rttp_solver_summary import RttpAlgorithmStepId
from django_apps.asteroid_lab.optimization.selection.ga_evolution import select_genome_evolution
from django_apps.asteroid_lab.optimization.selection.ga_evolution_shadow import (
    build_ga_evolution_shadow_summary,
    ga_evolution_shadow_metrics,
)
from django_apps.asteroid_lab.optimization.selection.genome_fitness import (
    evaluate_genome_fitness,
    genome_layout_valid,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import (
    PlacementGenome,
    SelectionConfig,
    select_genome,
)
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_RTTP_GA_EVOLUTION_SHADOW_KEY,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    _ga_evolution_shadow_config_from_run_config,
    _rttp_pipeline_config_from_run_config,
)


def _pattern_by_id(pattern_id: str):
    for pattern in build_pattern_library():
        if pattern.pattern_id == pattern_id:
            return pattern
    msg = f"pattern not found: {pattern_id!r}"
    raise AssertionError(msg)


def _translate(anchor: tuple[int, int], offset: tuple[int, int]) -> tuple[int, int]:
    return (anchor[0] + offset[0], anchor[1] + offset[1])


def _bundle_candidate(
    anchor: tuple[int, int],
    *,
    pattern_id: str = "lin_e_len0",
    throughput_factor: int | None = None,
    route_probe_cost: int = 5,
) -> BundleCandidate:
    pattern = _pattern_by_id(pattern_id)
    occupied = frozenset(_translate(anchor, offset) for offset in pattern.occupied_offsets)
    output_stub = _translate(anchor, pattern.output_stub_offset)
    throughput = throughput_factor if throughput_factor is not None else pattern.throughput_factor
    return BundleCandidate(
        candidate_id=f"{anchor[0]},{anchor[1]}:{pattern.pattern_id}:shape_belt",
        anchor_coord=anchor,
        pattern=pattern,
        occupied_cells=occupied,
        output_stub=output_stub,
        output_dir=pattern.output_dir,
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=throughput,
        route_probe_cost=route_probe_cost,
        reachable=True,
    )


def _skeleton_with_goals(
    greenfield_optimization_input: OptimizationInput,
    capacity_goals: int,
) -> RttpSkeleton:
    skeleton = RttpSkeletonBuilder.build(
        greenfield_optimization_input,
        config=RttpSkeletonConfig(),
    )
    return replace(skeleton, capacity_goals=capacity_goals)


def test_ga_shadow_config_defaults_disabled() -> None:
    cfg = GaEvolutionShadowConfig()
    assert cfg.enabled is False
    assert cfg.observe_only is True
    assert cfg.population_size == 24
    assert cfg.generations == 8


def test_ga_shadow_summary_frozen() -> None:
    summary = GaEvolutionShadowSummary(
        enabled=True,
        observe_only=True,
        primary_commit_order=("a",),
        shadow_proposed_commit_order=("b",),
        shadow_fitness_total=1.0,
        generations_run=1,
        population_size=24,
        overlap_violation_count=0,
        gene_count=1,
        anchor_count=1,
        order_agreement_ratio=0.0,
    )
    assert summary.enabled is True


def test_overlapping_genome_invalid_fitness(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    skeleton = _skeleton_with_goals(greenfield_optimization_input, capacity_goals=2)
    first = _bundle_candidate((5, 5))
    second = _bundle_candidate((5, 5), pattern_id="lin_n_len0")
    candidates_by_id = {
        first.candidate_id: first,
        second.candidate_id: second,
    }
    order = (first.candidate_id, second.candidate_id)
    assert genome_layout_valid(order, candidates_by_id, goal_count=2) is False
    assert evaluate_genome_fitness(
        order,
        candidates_by_id=candidates_by_id,
        skeleton=skeleton,
        inp=greenfield_optimization_input,
        config=SelectionConfig(),
        goal_count=2,
    ) == float("-inf")


def test_select_genome_evolution_respects_goal_count(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    skeleton = _skeleton_with_goals(greenfield_optimization_input, capacity_goals=4)
    pool = tuple(
        _bundle_candidate((i * 4, 0), throughput_factor=4, route_probe_cost=5) for i in range(4)
    )
    ga_cfg = GaEvolutionShadowConfig(enabled=True, random_seed=7, generations=2, population_size=6)
    genome = select_genome_evolution(
        pool,
        skeleton,
        greenfield_optimization_input,
        goal_count=2,
        config=ga_cfg,
    )
    assert isinstance(genome, PlacementGenome)
    assert len(genome.commit_order) <= 2


def test_shadow_disabled_returns_empty_proposal(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    skeleton = _skeleton_with_goals(greenfield_optimization_input, capacity_goals=1)
    summary = build_ga_evolution_shadow_summary(
        primary_genome=PlacementGenome(commit_order=("c1",)),
        normal_candidates=(),
        skeleton=skeleton,
        inp=greenfield_optimization_input,
        goal_count=1,
        config=GaEvolutionShadowConfig(enabled=False),
    )
    assert summary.enabled is False
    assert summary.shadow_proposed_commit_order == ()


def test_enabled_shadow_produces_proposal_on_toy_pool(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    skeleton = _skeleton_with_goals(greenfield_optimization_input, capacity_goals=2)
    pool = (
        _bundle_candidate((0, 0)),
        _bundle_candidate((8, 0)),
        _bundle_candidate((16, 0)),
    )
    greedy = select_genome(pool, skeleton, greenfield_optimization_input, goal_count=2)
    summary = build_ga_evolution_shadow_summary(
        primary_genome=greedy,
        normal_candidates=pool,
        skeleton=skeleton,
        inp=greenfield_optimization_input,
        goal_count=2,
        config=GaEvolutionShadowConfig(
            enabled=True,
            random_seed=3,
            generations=2,
            population_size=6,
        ),
    )
    assert summary.enabled is True
    assert summary.observe_only is True
    assert len(summary.shadow_proposed_commit_order) <= 2
    metrics = ga_evolution_shadow_metrics(summary)
    assert metrics["enabled"] is True
    assert isinstance(metrics["shadow_proposed_commit_order"], list)


def test_ga_shadow_config_key_constant() -> None:
    assert SOLVER_RUN_CONFIG_RTTP_GA_EVOLUTION_SHADOW_KEY == "ga_evolution_shadow"


def test_ga_shadow_config_from_run_config_enabled() -> None:
    cfg = _ga_evolution_shadow_config_from_run_config(
        {SOLVER_RUN_CONFIG_RTTP_GA_EVOLUTION_SHADOW_KEY: {"enabled": True, "generations": 4}}
    )
    assert cfg.enabled is True
    assert cfg.generations == 4
    assert cfg.observe_only is True


def test_ga_shadow_observe_only_false_allowed_not_commit_switch() -> None:
    cfg = _ga_evolution_shadow_config_from_run_config(
        {SOLVER_RUN_CONFIG_RTTP_GA_EVOLUTION_SHADOW_KEY: {"observe_only": False}}
    )
    assert cfg.observe_only is False
    pipeline_cfg = _rttp_pipeline_config_from_run_config(
        {SOLVER_RUN_CONFIG_RTTP_GA_EVOLUTION_SHADOW_KEY: {"observe_only": False}}
    )
    from django_apps.asteroid_lab.contracts.selection_mode import SelectionMode

    assert pipeline_cfg.selection_mode is SelectionMode.GREEDY_REGRET


def test_pipeline_config_includes_ga_shadow() -> None:
    cfg = _rttp_pipeline_config_from_run_config(
        {SOLVER_RUN_CONFIG_RTTP_GA_EVOLUTION_SHADOW_KEY: {"enabled": True, "generations": 3}}
    )
    assert cfg.ga_evolution_shadow.enabled is True
    assert cfg.ga_evolution_shadow.generations == 3


def test_pipeline_includes_ga_shadow_step_after_selection(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    result = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(
            ga_evolution_shadow=GaEvolutionShadowConfig(enabled=True, random_seed=1, generations=1),
        ),
    )
    step_ids = [row["step_id"] for row in result.algorithm_steps]
    assert RttpAlgorithmStepId.RTTP_GA_EVOLUTION_SHADOW.value in step_ids
    selection_idx = step_ids.index(RttpAlgorithmStepId.RTTP_GENOME_SELECTION.value)
    ga_idx = step_ids.index(RttpAlgorithmStepId.RTTP_GA_EVOLUTION_SHADOW.value)
    deferred_idx = step_ids.index(RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_SHADOW.value)
    assert selection_idx < ga_idx < deferred_idx


def test_disabled_ga_shadow_step_present_with_empty_proposal(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    result = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(
            ga_evolution_shadow=GaEvolutionShadowConfig(enabled=False),
        ),
    )
    shadow = next(
        row
        for row in result.algorithm_steps
        if row["step_id"] == RttpAlgorithmStepId.RTTP_GA_EVOLUTION_SHADOW.value
    )
    assert shadow["passed"] is True
    assert shadow["metrics"]["enabled"] is False
    assert shadow["metrics"]["shadow_proposed_commit_order"] == []


def test_disabled_ga_shadow_does_not_change_commit_or_validation(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    baseline = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    disabled = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(
            ga_evolution_shadow=GaEvolutionShadowConfig(enabled=False),
        ),
    )
    assert disabled.commit_result.committed_ids == baseline.commit_result.committed_ids
    assert disabled.validation_passed == baseline.validation_passed
    assert disabled.genome.commit_order == baseline.genome.commit_order


def test_incremental_commit_receives_greedy_genome_when_ga_enabled(
    greenfield_optimization_input: OptimizationInput,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[PlacementGenome] = []
    original = incremental_commit

    def _spy(genome: PlacementGenome, *args, **kwargs):
        captured.append(genome)
        return original(genome, *args, **kwargs)

    monkeypatch.setattr(
        "django_apps.asteroid_lab.optimization.pipeline.incremental_commit",
        _spy,
    )
    result = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(
            ga_evolution_shadow=GaEvolutionShadowConfig(enabled=True, random_seed=2, generations=1),
        ),
    )
    assert len(captured) == 1
    assert result.genome.commit_order == tuple(
        cid
        for cid in captured[0].commit_order
        if cid in result.commit_result.committed_ids
    )
