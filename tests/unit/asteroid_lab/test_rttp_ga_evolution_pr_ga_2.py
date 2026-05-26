"""PR-GA-2 — config-gated selection.mode primary selector."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.contracts.ga_evolution_shadow import GaEvolutionShadowConfig
from django_apps.asteroid_lab.contracts.selection_mode import SelectionMode
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import ExtractorPlacementPolicy
from django_apps.asteroid_lab.optimization.commit.incremental_commit import incremental_commit
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpPipelineConfig,
)
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.rttp_solver_summary import RttpAlgorithmStepId
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.selection.primary_genome import select_primary_genome
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_RTTP_SELECTION_KEY,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    _rttp_pipeline_config_from_run_config,
    _selection_mode_from_run_config,
)
from tests.unit.asteroid_lab.test_ga_evolution_shadow import (
    _bundle_candidate,
    _skeleton_with_goals,
)


def test_selection_mode_defaults_greedy_regret() -> None:
    cfg = RttpPipelineConfig()
    assert cfg.selection_mode is SelectionMode.GREEDY_REGRET


def test_selection_mode_enum_values() -> None:
    assert SelectionMode.GREEDY_REGRET.value == "greedy_regret"
    assert SelectionMode.EVOLUTION.value == "evolution"


def test_selection_mode_from_run_config_default() -> None:
    assert _selection_mode_from_run_config({}) is SelectionMode.GREEDY_REGRET


def test_selection_mode_evolution() -> None:
    mode = _selection_mode_from_run_config(
        {SOLVER_RUN_CONFIG_RTTP_SELECTION_KEY: {"mode": "evolution"}}
    )
    assert mode is SelectionMode.EVOLUTION


def test_selection_mode_invalid_raises() -> None:
    with pytest.raises(ValueError, match="selection.mode"):
        _selection_mode_from_run_config({SOLVER_RUN_CONFIG_RTTP_SELECTION_KEY: {"mode": "genetic"}})


def test_pipeline_config_wires_selection_mode() -> None:
    cfg = _rttp_pipeline_config_from_run_config(
        {SOLVER_RUN_CONFIG_RTTP_SELECTION_KEY: {"mode": "evolution"}}
    )
    assert cfg.selection_mode is SelectionMode.EVOLUTION


def test_select_primary_genome_evolution_respects_goal_count(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    skeleton = _skeleton_with_goals(greenfield_optimization_input, capacity_goals=4)
    pool = tuple(_bundle_candidate((i * 4, 0)) for i in range(4))
    ga_cfg = GaEvolutionShadowConfig(enabled=True, random_seed=11, generations=2, population_size=8)
    evolved = select_primary_genome(
        mode=SelectionMode.EVOLUTION,
        normal_candidates=pool,
        skeleton=skeleton,
        inp=greenfield_optimization_input,
        goal_count=2,
        ga_config=ga_cfg,
    )
    assert len(evolved.commit_order) <= 2


def test_default_pipeline_matches_explicit_greedy_mode(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    baseline = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    explicit = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(selection_mode=SelectionMode.GREEDY_REGRET),
    )
    assert explicit.genome.commit_order == baseline.genome.commit_order
    assert explicit.commit_result.committed_ids == baseline.commit_result.committed_ids
    assert explicit.validation_passed == baseline.validation_passed


def test_incremental_commit_receives_evolution_genome_when_mode_evolution(
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
    ga_cfg = GaEvolutionShadowConfig(enabled=True, random_seed=5, generations=2, population_size=8)
    result = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(
            selection_mode=SelectionMode.EVOLUTION,
            ga_evolution_shadow=ga_cfg,
        ),
    )
    assert len(captured) == 1
    assert captured[0].commit_order == result.genome.commit_order
    selection_step = next(
        row
        for row in result.algorithm_steps
        if row["step_id"] == RttpAlgorithmStepId.RTTP_GENOME_SELECTION.value
    )
    assert selection_step["metrics"]["selection_mode"] == "evolution"


def test_evolution_mode_pipeline_records_commit_step(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    result = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(
            selection_mode=SelectionMode.EVOLUTION,
            ga_evolution_shadow=GaEvolutionShadowConfig(
                random_seed=2,
                generations=1,
                population_size=6,
            ),
        ),
    )
    step_ids = [row["step_id"] for row in result.algorithm_steps]
    assert RttpAlgorithmStepId.RTTP_COMMIT.value in step_ids
    sel_idx = step_ids.index(RttpAlgorithmStepId.RTTP_GENOME_SELECTION.value)
    commit_idx = step_ids.index(RttpAlgorithmStepId.RTTP_COMMIT.value)
    assert sel_idx < commit_idx


def test_macro_path_unchanged_by_selection_mode_evolution(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    macro_baseline = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(macro_only_mode=True),
    )
    macro_evolution = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(
            macro_only_mode=True,
            selection_mode=SelectionMode.EVOLUTION,
            ga_evolution_shadow=GaEvolutionShadowConfig(
                enabled=True,
                random_seed=1,
                generations=1,
            ),
        ),
    )
    assert macro_evolution.genome.commit_order == macro_baseline.genome.commit_order
    assert macro_evolution.commit_result.committed_ids == macro_baseline.commit_result.committed_ids


def test_evolution_mode_algorithm_steps_expose_selection_mode(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    result = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(
            selection_mode=SelectionMode.EVOLUTION,
            ga_evolution_shadow=GaEvolutionShadowConfig(
                enabled=True,
                random_seed=1,
                generations=1,
            ),
        ),
    )
    sel = next(
        row
        for row in result.algorithm_steps
        if row["step_id"] == RttpAlgorithmStepId.RTTP_GENOME_SELECTION.value
    )
    shadow = next(
        row
        for row in result.algorithm_steps
        if row["step_id"] == RttpAlgorithmStepId.RTTP_GA_EVOLUTION_SHADOW.value
    )
    assert sel["metrics"]["selection_mode"] == "evolution"
    assert shadow["metrics"]["primary_selection_mode"] == "evolution"


def test_observe_only_false_does_not_switch_commit_authority(
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
    ga_cfg = GaEvolutionShadowConfig(
        enabled=True,
        observe_only=False,
        random_seed=3,
        generations=1,
    )
    result = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(
            selection_mode=SelectionMode.GREEDY_REGRET,
            ga_evolution_shadow=ga_cfg,
        ),
    )
    assert len(captured) == 1
    assert captured[0].commit_order == result.genome.commit_order
