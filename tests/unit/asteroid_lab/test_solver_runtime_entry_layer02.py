"""Layer 02 solver runtime entry (Run Solver button)."""

from __future__ import annotations

import pytest
from django.test import override_settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_01_RECONSTRUCTION,
    LAYER_02_EXTERIOR_TRANSPORT,
)
from django_apps.asteroid_lab.services.lab_layer02_timeline import LAYER02_EVENT_TYPE
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY,
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    SOLVER_NOT_AVAILABLE_MESSAGE,
    SolverRuntimeEntryErrorCode,
    entry_result_to_json_dict,
    run_solver_runtime_for_project,
)

pytestmark = pytest.mark.django_db


def _minimal_copy() -> str:
    return "SHAPEZ2-4-e30="


@override_settings(ASTEROID_LAB_LAYER_02_SOLVER_ENABLED=False)
def test_run_solver_stub_when_layer02_disabled() -> None:
    proj = m.AsteroidProject.objects.create(name="L2Off", slug="l2-off")
    m.AsteroidMapInput.objects.create(project=proj, copy_code=_minimal_copy())
    result = run_solver_runtime_for_project(int(proj.pk))
    assert result.ok is False
    assert result.error_code == SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE
    assert result.message == SOLVER_NOT_AVAILABLE_MESSAGE


@override_settings(ASTEROID_LAB_LAYER_02_SOLVER_ENABLED=True)
def test_run_solver_layer02_persists_plan_and_summary() -> None:
    proj = m.AsteroidProject.objects.create(name="L2On", slug="l2-on")
    m.AsteroidMapInput.objects.create(project=proj, copy_code=_minimal_copy())
    result = run_solver_runtime_for_project(int(proj.pk), config={"throughput_target_percent": 80})
    assert result.ok is True
    assert result.solver_run_id is not None
    assert result.error_code is None

    run = m.SolverRun.objects.get(pk=int(result.solver_run_id))
    config = dict(run.config_json or {})
    assert isinstance(config.get("exterior_connector_plan"), dict)
    runtime_frames = config.get(SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY)
    assert isinstance(runtime_frames, list)
    runtime_types = [str(f.get("event_type") or "") for f in runtime_frames]
    assert LAYER02_EVENT_TYPE in runtime_types
    assert "layer03_rim_greedy_begin" in runtime_types
    assert runtime_types.index("layer03_rim_greedy_begin") > runtime_types.index(
        LAYER02_EVENT_TYPE
    )
    summary = dict(config.get(SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY) or {})
    assert summary.get("stack_run_status") == "success"
    completed = list(summary.get("completed_layer_slugs") or [])
    assert LAYER_01_RECONSTRUCTION in completed
    assert LAYER_02_EXTERIOR_TRANSPORT in completed
    assert LAYER_02_EXTERIOR_TRANSPORT not in (summary.get("failed_layer_slug"),)
    assert result.validation_passed is False


@override_settings(ASTEROID_LAB_LAYER_02_SOLVER_ENABLED=True)
def test_entry_result_json_includes_run_summary_for_layer02() -> None:
    proj = m.AsteroidProject.objects.create(name="L2Json", slug="l2-json")
    m.AsteroidMapInput.objects.create(project=proj, copy_code=_minimal_copy())
    result = run_solver_runtime_for_project(int(proj.pk), config={"throughput_target_percent": 80})
    body = entry_result_to_json_dict(result, project_slug=str(proj.slug))
    run_summary = body.get("run_summary")
    assert isinstance(run_summary, dict)
    assert str(run_summary["id"]) == str(result.solver_run_id)
    l2_labels = [h["label"] for h in run_summary["layer_summaries"][1]["highlights"]]
    assert "Required connectors" in l2_labels
    assert "Planned connectors" in l2_labels


@override_settings(ASTEROID_LAB_LAYER_02_SOLVER_ENABLED=True)
def test_run_solver_invalid_throughput_percent() -> None:
    proj = m.AsteroidProject.objects.create(name="L2BadPct", slug="l2-bad-pct")
    m.AsteroidMapInput.objects.create(project=proj, copy_code=_minimal_copy())
    result = run_solver_runtime_for_project(
        int(proj.pk),
        config={"throughput_target_percent": 0},
    )
    assert result.ok is False
    assert result.error_code == SolverRuntimeEntryErrorCode.INVALID_THROUGHPUT_TARGET_PERCENT
