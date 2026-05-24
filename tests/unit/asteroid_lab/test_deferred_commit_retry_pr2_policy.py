"""PR-2 — runtime deferred_retry_shadow policy wiring."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.contracts.deferred_retry_shadow import DeferredRetryShadowConfig
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpPipelineConfig,
)
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.rttp_solver_summary import RttpAlgorithmStepId
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY,
    SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY,
    SOLVER_RUN_CONFIG_RTTP_MAX_MACRO_CANDIDATES_KEY,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    _deferred_retry_shadow_config_from_run_config,
    _rttp_pipeline_config_from_run_config,
)


def test_deferred_retry_shadow_config_key_constant() -> None:
    assert SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY == "deferred_retry_shadow"


def test_absent_key_uses_defaults() -> None:
    cfg = _deferred_retry_shadow_config_from_run_config({})
    assert cfg == DeferredRetryShadowConfig()


def test_enabled_false_maps_to_disabled_config() -> None:
    cfg = _deferred_retry_shadow_config_from_run_config(
        {SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY: {"enabled": False}}
    )
    assert cfg.enabled is False
    assert cfg.observe_only is True
    assert cfg.max_retry_rounds == 1


def test_enabled_true_with_overrides() -> None:
    cfg = _deferred_retry_shadow_config_from_run_config(
        {
            SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY: {
                "enabled": True,
                "max_retry_rounds": 2,
                "max_candidates": 8,
                "route_probe_max_expansions": 250,
            }
        }
    )
    assert cfg.enabled is True
    assert cfg.max_retry_rounds == 2
    assert cfg.max_candidates == 8
    assert cfg.route_probe_max_expansions == 250


def test_observe_only_false_raises() -> None:
    with pytest.raises(ValueError, match="observe_only"):
        _deferred_retry_shadow_config_from_run_config(
            {
                SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY: {
                    "enabled": True,
                    "observe_only": False,
                }
            }
        )


def test_enabled_string_false_raises() -> None:
    with pytest.raises(ValueError, match="enabled"):
        _deferred_retry_shadow_config_from_run_config(
            {
                SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY: {
                    "enabled": "false",
                }
            }
        )


def test_non_dict_shadow_value_raises() -> None:
    with pytest.raises(ValueError, match="deferred_retry_shadow"):
        _deferred_retry_shadow_config_from_run_config(
            {SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY: "off"}
        )


def test_pipeline_config_includes_shadow_and_preserves_macro() -> None:
    cfg = _rttp_pipeline_config_from_run_config(
        {
            SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY: True,
            SOLVER_RUN_CONFIG_RTTP_MAX_MACRO_CANDIDATES_KEY: 32,
            SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY: {"enabled": False},
        }
    )
    assert cfg.macro_only_mode is True
    assert cfg.max_macro_candidates == 32
    assert cfg.deferred_retry_shadow.enabled is False


def test_solver_summary_does_not_drive_shadow_config() -> None:
    cfg = _rttp_pipeline_config_from_run_config(
        {
            "solver_summary": {
                "algorithm_steps": [
                    {
                        "step_id": "rttp.deferred_commit_retry_shadow",
                        "metrics": {"enabled": False, "candidate_count": 99},
                    }
                ]
            },
            SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY: {"enabled": True},
        }
    )
    assert cfg.deferred_retry_shadow.enabled is True


def test_disabled_shadow_step_present_with_empty_metrics(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    result = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(
            deferred_retry_shadow=DeferredRetryShadowConfig(enabled=False),
        ),
    )
    shadow = next(
        row
        for row in result.algorithm_steps
        if row["step_id"] == RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_SHADOW.value
    )
    assert shadow["passed"] is True
    assert shadow["metrics"]["enabled"] is False
    assert shadow["metrics"]["observe_only"] is True
    assert shadow["metrics"]["candidate_count"] == 0
    assert shadow["metrics"]["eligible_candidate_ids"] == []


def test_disabled_shadow_does_not_change_commit_or_validation(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    baseline = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(
            deferred_retry_shadow=DeferredRetryShadowConfig(),
        ),
    )
    disabled = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(
            deferred_retry_shadow=DeferredRetryShadowConfig(enabled=False),
        ),
    )
    assert disabled.commit_result.committed_ids == baseline.commit_result.committed_ids
    assert disabled.commit_result.conflicts == baseline.commit_result.conflicts
    assert disabled.validation_passed == baseline.validation_passed
    assert disabled.genome.commit_order == baseline.genome.commit_order
