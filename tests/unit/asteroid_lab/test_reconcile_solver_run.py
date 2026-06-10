"""Artifact-first reconcile for async solver runs (PR-CLI-7)."""

from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.solver_run_reconcile import (
    RECONCILE_FAILURE_INGEST,
    RECONCILE_FAILURE_TIMEOUT,
    RECONCILE_FAILURE_VALIDATION,
    reconcile_running_solver_runs,
    reconcile_solver_run,
)
from django_apps.asteroid_lab.services.solver_run_registry import create_running_solver_run
from tests.unit.asteroid_lab.test_artifact_ingest import _write_artifact

pytestmark = pytest.mark.django_db


@pytest.fixture
def artifact_root(tmp_path: Path, settings):
    settings.ASTEROID_LAB_ARTIFACT_ROOT = tmp_path
    return tmp_path


def _running_run(
    project: m.AsteroidProject,
    artifact_root: Path,
    *,
    run_key: str = "async-run-1",
) -> m.SolverRun:
    artifact_dir = artifact_root / run_key
    artifact_dir.mkdir(parents=True, exist_ok=True)
    return create_running_solver_run(
        project_id=int(project.pk),
        run_key=run_key,
        spawn_config={
            "planned_artifact_dir": str(artifact_dir.resolve()),
            "sidecar_log_path": str(
                (artifact_root / ".subprocess_logs" / f"{run_key}.log").resolve()
            ),
        },
    )


def _write_hashed_invalid_summary_artifact(
    artifact_dir: Path,
    *,
    run_key: str,
) -> None:
    summary_path = artifact_dir / "output" / "solver_summary.json"
    replay_path = artifact_dir / "output" / "replay_core.jsonl"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("NOT-JSON", encoding="utf-8")
    replay_path.write_text('{"frame_index":0,"phase":"decode"}\n', encoding="utf-8")
    summary_hash = hashlib.sha256(summary_path.read_bytes()).hexdigest()
    replay_hash = hashlib.sha256(replay_path.read_bytes()).hexdigest()
    manifest = {
        "schema_version": 1,
        "run_key": run_key,
        "lifecycle_status": "artifact_written",
        "created_at_utc": "2026-05-30T00:00:00Z",
        "core_build_id": "test",
        "content_hashes": {
            "output/solver_summary.json": summary_hash,
            "output/replay_core.jsonl": replay_hash,
        },
        "paths": {
            "solver_summary": "output/solver_summary.json",
            "replay_core": "output/replay_core.jsonl",
        },
        "game_data_provenance": {"snapshot": "test"},
        "error_code": None,
    }
    (artifact_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_reconcile_ingests_finalized_artifact_once(artifact_root: Path) -> None:
    project = m.AsteroidProject.objects.create(name="Reconcile", slug="reconcile")
    run = _running_run(project, artifact_root)
    artifact_dir = artifact_root / run.run_key
    _write_artifact(artifact_dir, run_key=run.run_key)

    first = reconcile_solver_run(int(run.pk))
    second = reconcile_solver_run(int(run.pk))

    assert first.status == m.SolverRun.RunStatus.COMPLETED
    assert second.status == m.SolverRun.RunStatus.COMPLETED
    assert m.SolverRun.objects.filter(project=project).count() == 1
    refreshed = m.SolverRun.objects.get(pk=int(run.pk))
    assert refreshed.lifecycle_status == "succeeded"
    assert refreshed.solver_summary_json.get("validation_passed") is True


def test_reconcile_never_ingests_tmp_staging(artifact_root: Path) -> None:
    project = m.AsteroidProject.objects.create(name="Tmp", slug="tmp-staging")
    run = _running_run(project, artifact_root, run_key="staging-run")
    staging = artifact_root / ".tmp" / run.run_key
    staging.mkdir(parents=True)
    _write_artifact(staging, run_key=run.run_key)

    result = reconcile_solver_run(int(run.pk))

    assert result.status == m.SolverRun.RunStatus.RUNNING
    assert m.SolverRun.objects.get(pk=int(run.pk)).lifecycle_status == "running"


def test_reconcile_timeout_marks_failed_without_ingest(artifact_root: Path, settings) -> None:
    settings.ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS = 1
    project = m.AsteroidProject.objects.create(name="Timeout", slug="timeout")
    run = _running_run(project, artifact_root)
    m.SolverRun.objects.filter(pk=int(run.pk)).update(
        started_at=timezone.now() - timedelta(seconds=120)
    )

    result = reconcile_solver_run(int(run.pk))

    assert result.status == m.SolverRun.RunStatus.FAILED
    assert result.error_code == RECONCILE_FAILURE_TIMEOUT
    refreshed = m.SolverRun.objects.get(pk=int(run.pk))
    assert refreshed.solver_summary_json == {}


def test_reconcile_validation_failure_without_manifest_rewrite(artifact_root: Path) -> None:
    project = m.AsteroidProject.objects.create(name="Bad", slug="bad-manifest")
    run = _running_run(project, artifact_root)
    artifact_dir = artifact_root / run.run_key
    _write_artifact(artifact_dir, run_key=run.run_key, corrupt_hash=True)
    manifest_before = json.loads((artifact_dir / "manifest.json").read_text(encoding="utf-8"))

    result = reconcile_solver_run(int(run.pk))

    assert result.status == m.SolverRun.RunStatus.FAILED
    assert result.error_code == RECONCILE_FAILURE_VALIDATION
    manifest_after = json.loads((artifact_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest_after == manifest_before
    assert manifest_after["lifecycle_status"] == "artifact_written"


def test_reconcile_ingest_error_marks_failed_without_exception_leak(
    artifact_root: Path,
) -> None:
    project = m.AsteroidProject.objects.create(name="BadJson", slug="bad-json-ingest")
    run = _running_run(project, artifact_root)
    artifact_dir = artifact_root / run.run_key
    _write_hashed_invalid_summary_artifact(artifact_dir, run_key=run.run_key)
    manifest_before = json.loads((artifact_dir / "manifest.json").read_text(encoding="utf-8"))

    result = reconcile_solver_run(int(run.pk))

    assert result.status == m.SolverRun.RunStatus.FAILED
    assert result.error_code == RECONCILE_FAILURE_INGEST
    assert result.message is not None
    assert "invalid JSON" in result.message
    refreshed = m.SolverRun.objects.get(pk=int(run.pk))
    assert refreshed.lifecycle_status == "failed"
    assert refreshed.solver_summary_json == {}
    manifest_after = json.loads((artifact_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest_after == manifest_before


def test_reconcile_status_get_returns_json_on_ingest_failure(
    client,
    artifact_root: Path,
) -> None:
    project = m.AsteroidProject.objects.create(name="StatusJson", slug="status-json-ingest")
    run = _running_run(project, artifact_root)
    _write_hashed_invalid_summary_artifact(
        artifact_root / run.run_key,
        run_key=run.run_key,
    )

    response = client.get(
        reverse(
            "web:asteroid-miner-layout-project-solver-run-status",
            kwargs={"slug": project.slug, "run_id": int(run.pk)},
        )
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == m.SolverRun.RunStatus.FAILED
    assert body["error_code"] == RECONCILE_FAILURE_INGEST
    assert body["message"] is not None


def test_reconcile_status_path_does_not_warm_replay_cache(artifact_root: Path) -> None:
    project = m.AsteroidProject.objects.create(name="NoWarmReconcile", slug="no-warm-reconcile")
    run = _running_run(project, artifact_root)
    _write_artifact(artifact_root / run.run_key, run_key=run.run_key)

    with patch(
        "django_apps.asteroid_lab.services.artifact_ingest._warm_lab_replay_cache_after_artifact_ingest",
    ) as warm_mock:
        reconcile_solver_run(int(run.pk))

    warm_mock.assert_not_called()


def test_duplicate_status_polls_do_not_double_ingest(artifact_root: Path) -> None:
    project = m.AsteroidProject.objects.create(name="Race", slug="race")
    run = _running_run(project, artifact_root)
    artifact_dir = artifact_root / run.run_key
    _write_artifact(artifact_dir, run_key=run.run_key)

    first = reconcile_solver_run(int(run.pk))
    second = reconcile_solver_run(int(run.pk))

    assert first.status == m.SolverRun.RunStatus.COMPLETED
    assert second.status == m.SolverRun.RunStatus.COMPLETED
    assert m.SolverRun.objects.filter(project=project).count() == 1


def test_reconcile_running_batch(artifact_root: Path) -> None:
    project = m.AsteroidProject.objects.create(name="Reap", slug="reap-batch")
    run = _running_run(project, artifact_root)
    _write_artifact(artifact_root / run.run_key, run_key=run.run_key)

    items = reconcile_running_solver_runs()

    assert len(items) == 1
    assert items[0].status == m.SolverRun.RunStatus.COMPLETED
