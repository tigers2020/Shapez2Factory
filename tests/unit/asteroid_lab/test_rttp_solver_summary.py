"""RTTP ``solver_summary`` contract — per-step summaries for observability."""

from __future__ import annotations

import base64
import gzip
import json

import pytest
from django.test import override_settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.rttp_solver_summary import (
    RttpAlgorithmStepId,
    build_rttp_solver_summary,
    reconstruction_step_from_result,
)
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.replay.event_types import RTTP_MILESTONE_EVENT_TYPES
from django_apps.asteroid_lab.services.input_service import create_copy_code_map_input
from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
    run_reconstruction_for_map_input,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


_RTTP_PIPELINE_STEP_IDS = (
    RttpAlgorithmStepId.RTTP_ROUTE_DOMAIN,
    RttpAlgorithmStepId.RTTP_CANDIDATE_POOL,
    RttpAlgorithmStepId.RTTP_GENOME_SELECTION,
    RttpAlgorithmStepId.RTTP_GA_EVOLUTION_SHADOW,
    RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_SHADOW,
    RttpAlgorithmStepId.RTTP_COMMIT,
    RttpAlgorithmStepId.RTTP_CATALOG_PLACEMENT_VALIDATION,
)

_RTTP_RUNTIME_STEP_IDS_AFTER_RECON = (
    RttpAlgorithmStepId.RTTP_CATALOG_SLICE,
    *_RTTP_PIPELINE_STEP_IDS,
)


def _minimal_valid_copy() -> str:
    payload = json.dumps(
        {
            "V": 1,
            "BP": {
                "$type": "Island",
                "Entries": [
                    {"X": 1, "Y": 0, "T": "Layout_ProMiner"},
                    {"X": 2, "Y": 0, "T": "SpaceBelt_Left"},
                ],
            },
        },
        separators=(",", ":"),
    ).encode("utf-8")
    b64 = base64.b64encode(gzip.compress(payload)).decode("ascii")
    return f"SHAPEZ2-4-{b64}"


def test_build_rttp_solver_summary_includes_reconstruction_capacity_when_provided() -> None:
    cap = {"capacity_basis": "terrain_upper_bound", "by_resource": {"shape": {}}}
    obs = {"cell_count": 10, "confirmed_cell_count": 8}
    summary = build_rttp_solver_summary(
        pipeline_ok=True,
        committed_count=1,
        normal_count=1,
        commit_order=("a",),
        algorithm_steps=(),
        reconstruction_capacity=cap,
        reconstruction_observability=obs,
    )
    assert summary["reconstruction_capacity"] == cap
    assert summary["reconstruction_observability"] == obs


def test_throughput_budget_satisfied_not_pipeline_ok_alias() -> None:
    summary = build_rttp_solver_summary(
        pipeline_ok=True,
        committed_count=1,
        normal_count=1,
        commit_order=("a",),
        algorithm_steps=(),
        throughput_budget_fields={
            "throughput_budget_satisfied": False,
            "throughput_target_percent": 60,
            "target_throughput_per_min": "2880.0000",
            "actual_committed_output_per_min": "2400.0000",
            "throughput_shortfall_per_min": "480.0000",
            "reconstruction_max_throughput_per_min": "4800.0000",
            "target_utilization_ratio": "0.6000",
            "actual_utilization_ratio": "0.5000",
            "throughput_target_status": "shortfall",
        },
    )
    assert summary["validation_passed"] is True
    assert summary["throughput_budget_satisfied"] is False
    assert summary["capacity_satisfied"] is False
    assert "throughput_target_shortfall" in summary["issue_codes"]


def test_capacity_satisfied_false_when_validation_ok_budget_fail() -> None:
    summary = build_rttp_solver_summary(
        pipeline_ok=True,
        committed_count=1,
        normal_count=127,
        commit_order=("a",),
        algorithm_steps=(),
        throughput_budget_fields={
            "throughput_budget_satisfied": False,
            "target_throughput_per_min": "1536.0000",
            "actual_committed_output_per_min": "120.0000",
        },
    )
    assert summary["validation_passed"] is True
    assert summary["capacity_satisfied"] is False
    assert summary["throughput_budget_satisfied"] is False


def test_build_rttp_solver_summary_includes_actual_committed_when_provided() -> None:
    summary = build_rttp_solver_summary(
        pipeline_ok=True,
        committed_count=2,
        normal_count=2,
        commit_order=("a", "b"),
        algorithm_steps=(),
        actual_committed_output_per_min="720.0000",
    )
    assert summary["actual_committed_output_per_min"] == "720.0000"


def test_build_rttp_solver_summary_omits_reconstruction_keys_when_none() -> None:
    summary = build_rttp_solver_summary(
        pipeline_ok=True,
        committed_count=0,
        normal_count=0,
        commit_order=(),
        algorithm_steps=(),
    )
    assert "reconstruction_capacity" not in summary
    assert "reconstruction_observability" not in summary
    assert "actual_committed_output_per_min" not in summary


def test_build_rttp_solver_summary_includes_ordered_algorithm_steps() -> None:
    steps = (
        {
            "step_id": RttpAlgorithmStepId.RTTP_ROUTE_DOMAIN.value,
            "phase": "rttp_pipeline",
            "event_type": et.EVENT_TYPE_RTTP_ROUTE_DOMAIN_SNAPSHOT,
            "title": "start",
            "summary": "domain ok",
            "metrics": {"skeleton_id": "sk-1"},
        },
    )
    summary = build_rttp_solver_summary(
        pipeline_ok=True,
        committed_count=2,
        normal_count=5,
        commit_order=("a", "b"),
        algorithm_steps=steps,
        macro_only_mode=False,
        reconstruction_step={
            "step_id": RttpAlgorithmStepId.RECONSTRUCTION.value,
            "phase": "reconstruction",
            "event_type": et.EVENT_TYPE_RECONSTRUCTION_MAP_COMPLETE,
            "title": "Reconstruction",
            "summary": "map ready",
            "metrics": {"cell_count": 10},
            "passed": True,
        },
    )
    assert summary["algorithm"] == "rttp_v0.1"
    assert summary["macro_only_mode"] is False
    assert len(summary["algorithm_steps"]) == 2
    assert summary["algorithm_steps"][0]["step_id"] == RttpAlgorithmStepId.RECONSTRUCTION.value
    assert summary["algorithm_steps"][1]["step_id"] == RttpAlgorithmStepId.RTTP_ROUTE_DOMAIN.value


def test_rttp_pipeline_algorithm_steps_match_milestone_event_types(
    greenfield_optimization_input: object,
) -> None:
    result = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    step_ids = [row["step_id"] for row in result.algorithm_steps]
    assert step_ids == [sid.value for sid in _RTTP_PIPELINE_STEP_IDS]
    _NON_MILESTONE_STEP_IDS = frozenset(
        {
            RttpAlgorithmStepId.RTTP_CATALOG_PLACEMENT_VALIDATION.value,
            RttpAlgorithmStepId.RTTP_GA_EVOLUTION_SHADOW.value,
            RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_SHADOW.value,
        }
    )
    milestone_rows = [
        row for row in result.algorithm_steps if row["step_id"] not in _NON_MILESTONE_STEP_IDS
    ]
    event_types = {row["event_type"] for row in milestone_rows}
    assert event_types == set(RTTP_MILESTONE_EVENT_TYPES)
    commit_row = next(
        row
        for row in result.algorithm_steps
        if row["step_id"] == RttpAlgorithmStepId.RTTP_COMMIT.value
    )
    audit_row = result.algorithm_steps[-1]
    assert audit_row["step_id"] == RttpAlgorithmStepId.RTTP_CATALOG_PLACEMENT_VALIDATION.value
    assert audit_row["passed"] is True
    assert commit_row["metrics"]["validation_passed"] == result.validation_passed
    assert commit_row["passed"] is result.validation_passed
    assert commit_row["summary"]


def test_reconstruction_step_from_result_uses_summary_json() -> None:
    proj = m.AsteroidProject.objects.create(name="ReconStep", slug="recon-step")
    inp = create_copy_code_map_input(proj, _minimal_valid_copy())
    _cleanup, recon = run_reconstruction_for_map_input(int(inp.pk), boundary_run_id="recon-step")
    del _cleanup
    step = reconstruction_step_from_result(recon)
    assert step["step_id"] == RttpAlgorithmStepId.RECONSTRUCTION.value
    assert step["event_type"] == et.EVENT_TYPE_RECONSTRUCTION_MAP_COMPLETE
    assert step["metrics"]["cell_count"] == len(recon.cells)
    assert step["metrics"]["quality_tier"] == recon.quality_tier


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_runtime_solver_summary_exposes_full_algorithm_steps() -> None:
    proj = m.AsteroidProject.objects.create(name="SummarySteps", slug="summary-steps")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    from tests.unit.asteroid_lab._runtime_game_data import run_solver_runtime_with_pinned_game_data

    result = run_solver_runtime_with_pinned_game_data(
        int(proj.pk),
        run_key="summary-steps",
        config={"rttp_record_replay": False},
    )
    steps = result.solver_summary.get("algorithm_steps") or []
    step_ids = [row["step_id"] for row in steps]
    assert step_ids[0] == RttpAlgorithmStepId.RECONSTRUCTION.value
    assert step_ids[1:] == [sid.value for sid in _RTTP_RUNTIME_STEP_IDS_AFTER_RECON]
    commit_step = next(
        row for row in steps if row["step_id"] == RttpAlgorithmStepId.RTTP_COMMIT.value
    )
    assert result.solver_summary.get("commit_order") == commit_step["metrics"].get("commit_order")
