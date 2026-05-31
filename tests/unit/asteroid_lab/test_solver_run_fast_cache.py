"""Regression: SolverRun fast-cache JSON columns are NOT NULL on create."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services import experiment_service
from django_apps.asteroid_lab.services.lab_replay_persisted_cache import (
    CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION,
    persist_composed_replay_for_run_id,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
)
from django_apps.asteroid_lab.services.solver_run_fast_cache import (
    empty_solver_run_fast_cache_kwargs,
)


@pytest.mark.django_db
def test_create_solver_run_populates_fast_cache_columns() -> None:
    project = m.AsteroidProject.objects.create(name="Fast cache", slug="fast-cache-run")
    dto = experiment_service.create_solver_run(
        project.id,
        run_key="rk-fast-cache",
        algorithm_label="layer_02_exterior_transport",
        config={SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY: {"run_success": True}},
    )
    row = m.SolverRun.objects.get(pk=dto.id)
    assert isinstance(row.lab_replay_manifest_summary_json, dict)
    assert row.lab_replay_manifest_summary_json["lab_replay_cache_schema_version"] == (
        CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION
    )
    assert row.lab_replay_payload_json == {
        "composed_frames": [],
        "replay_track_metrics": {},
    }
    assert row.solver_summary_json == {"run_success": True}
    assert row.solver_runtime_replay_frames_json == []


@pytest.mark.django_db
def test_solver_run_orm_create_accepts_fast_cache_defaults() -> None:
    project = m.AsteroidProject.objects.create(name="ORM defaults", slug="orm-fast-cache")
    row = m.SolverRun.objects.create(
        project=project,
        run_key="rk-orm",
        algorithm_label="ga",
        **empty_solver_run_fast_cache_kwargs(),
    )
    assert row.lab_replay_manifest_summary_json["frame_count"] == 0
    assert row.lab_replay_payload_json == {}
    assert row.solver_summary_json == {}
    assert row.solver_runtime_replay_frames_json == []


@pytest.mark.django_db
def test_persist_composed_replay_updates_manifest_summary_column() -> None:
    project = m.AsteroidProject.objects.create(name="Persist mirror", slug="persist-mirror")
    run = m.SolverRun.objects.create(
        project=project,
        run_key="rk-mirror",
        **empty_solver_run_fast_cache_kwargs(),
    )
    frames = [{"frame_index": 0, "title": "start"}]
    metrics = {"frame_count": 1, "replay_truncated": False}
    seed_summary = {
        "validation_passed": True,
        "stack_run_status": "success",
        "completed_layer_slugs": ["layer_02_exterior_transport"],
    }
    run.solver_summary_json = dict(seed_summary)
    run.save(update_fields=["solver_summary_json"])

    persist_composed_replay_for_run_id(int(run.pk), frames=frames, metrics=metrics)
    run.refresh_from_db()
    assert run.lab_replay_manifest_summary_json["frame_count"] == 1
    assert run.lab_replay_payload_json["composed_frames"] == frames
    assert run.solver_summary_json == seed_summary
