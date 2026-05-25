"""RTTP v1 macro-only pipeline — RTTP-G14 (PR-F)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.input_contracts import RttpPipelineConfig
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from tests.support.macro_triple_greenfield_fixture import build_macro_triple_greenfield_input


@pytest.mark.skip(
    reason="Macro-only on 4×4: macro_normal_count=0 under OUTSIDE_MINEABLE (PR-B follow-up)"
)
def test_macro_only_pipeline_deterministic() -> None:
    inp = build_macro_triple_greenfield_input()
    config = RttpPipelineConfig(macro_only_mode=True)

    first = run_rttp_pipeline(
        inp,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=config,
    )
    second = run_rttp_pipeline(
        inp,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=config,
    )

    assert first == second
    assert first.validation_passed
    assert first.genome.commit_order
    assert all(len(slot_id) == 64 for slot_id in first.genome.commit_order)
    assert len(first.commit_result.committed_ids) >= 3


def test_v01_pipeline_unchanged_when_macro_only_false(
    greenfield_optimization_input,
) -> None:
    from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput

    inp: OptimizationInput = greenfield_optimization_input
    default = run_rttp_pipeline(inp, policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM)
    explicit = run_rttp_pipeline(
        inp,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(macro_only_mode=False),
    )
    assert default == explicit
