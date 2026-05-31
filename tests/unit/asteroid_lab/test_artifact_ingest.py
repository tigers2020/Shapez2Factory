"""Artifact ingest writes DB index/cache fields only."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.layers.contracts.layer_slugs import LAYER_02_EXTERIOR_TRANSPORT
from django_apps.asteroid_lab.services.artifact_ingest import (
    ArtifactIngestError,
    ingest_artifact_for_project,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
)
from django_apps.asteroid_lab.services.solver_run_lab_summary import lab_run_summary_from_orm

pytestmark = pytest.mark.django_db


def _write_artifact(
    artifact_dir: Path,
    *,
    run_key: str = "run-1",
    lifecycle_status: str = "artifact_written",
    corrupt_hash: bool = False,
) -> dict[str, Any]:
    summary_path = artifact_dir / "output" / "solver_summary.json"
    replay_path = artifact_dir / "output" / "replay_core.jsonl"
    summary_path.parent.mkdir(parents=True)
    summary = {
        "stack_run_status": "success",
        "validation_passed": True,
        "issue_codes": [],
        "issue_details": [],
    }
    summary_path.write_text(json.dumps(summary, sort_keys=True), encoding="utf-8")
    replay_path.write_text('{"frame_index":0,"phase":"decode"}\n', encoding="utf-8")
    summary_hash = hashlib.sha256(summary_path.read_bytes()).hexdigest()
    replay_hash = hashlib.sha256(replay_path.read_bytes()).hexdigest()
    manifest = {
        "schema_version": 1,
        "run_key": run_key,
        "lifecycle_status": lifecycle_status,
        "created_at_utc": "2026-05-30T00:00:00Z",
        "core_build_id": "test",
        "content_hashes": {
            "output/solver_summary.json": "0" * 64 if corrupt_hash else summary_hash,
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
    return summary


def test_ingest_artifact_writes_index_only_solver_run(tmp_path: Path) -> None:
    project = m.AsteroidProject.objects.create(name="Artifact", slug="artifact")
    expected_summary = _write_artifact(tmp_path)

    result = ingest_artifact_for_project(project_id=int(project.pk), artifact_dir=tmp_path)

    run = m.SolverRun.objects.get(pk=int(result.solver_run.pk))
    assert run.run_key == "run-1"
    assert run.algorithm_label == "cli_artifact"
    assert run.status == m.SolverRun.RunStatus.COMPLETED
    assert run.artifact_root == str(tmp_path.resolve())
    assert run.lifecycle_status == "succeeded"
    assert run.solver_summary_json == expected_summary
    assert run.solver_runtime_replay_frames_json == []
    assert run.lab_replay_payload_json == {}
    assert run.lab_replay_manifest_summary_json["mode"] == "artifact_jsonl"
    assert run.lab_replay_manifest_summary_json["frame_count"] == 1
    assert run.lab_replay_manifest_summary_json["preview_frame"] is None
    assert run.config_json["artifact_manifest"]["lifecycle_status"] == "artifact_written"
    assert run.config_json[SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY] == expected_summary


def test_ingest_artifact_rejects_hash_mismatch_without_db_write(tmp_path: Path) -> None:
    project = m.AsteroidProject.objects.create(name="BadHash", slug="bad-hash")
    _write_artifact(tmp_path, corrupt_hash=True)

    with pytest.raises(ArtifactIngestError, match="hash mismatch"):
        ingest_artifact_for_project(project_id=int(project.pk), artifact_dir=tmp_path)

    assert not m.SolverRun.objects.filter(project=project).exists()


def test_ingest_artifact_rejects_partial_manifest_without_db_write(tmp_path: Path) -> None:
    project = m.AsteroidProject.objects.create(name="Partial", slug="partial")
    _write_artifact(tmp_path, lifecycle_status="PARTIAL")

    with pytest.raises(ArtifactIngestError, match="lifecycle_status"):
        ingest_artifact_for_project(project_id=int(project.pk), artifact_dir=tmp_path)

    assert not m.SolverRun.objects.filter(project=project).exists()


def test_ingest_artifact_rejects_existing_run_unless_replace(tmp_path: Path) -> None:
    project = m.AsteroidProject.objects.create(name="Collision", slug="collision")
    m.SolverRun.objects.create(project=project, run_key="run-1")
    _write_artifact(tmp_path)

    with pytest.raises(ArtifactIngestError, match="already exists"):
        ingest_artifact_for_project(project_id=int(project.pk), artifact_dir=tmp_path)

    result = ingest_artifact_for_project(
        project_id=int(project.pk),
        artifact_dir=tmp_path,
        replace_existing_run=True,
    )

    assert result.solver_run.status == m.SolverRun.RunStatus.COMPLETED


def _write_artifact_with_stack_summary(artifact_dir: Path) -> dict[str, Any]:
    summary = {
        "stack_run_status": "success",
        "run_success": True,
        "validation_passed": True,
        "completed_layer_slugs": [LAYER_02_EXTERIOR_TRANSPORT],
        "layer_summaries": [
            {
                "layer_slug": LAYER_02_EXTERIOR_TRANSPORT,
                "outcome": "completed",
                "metrics": {},
            }
        ],
        "reconstruction_capacity": {"shape_field_cell_count": 10},
    }
    summary_path = artifact_dir / "output" / "solver_summary.json"
    replay_path = artifact_dir / "output" / "replay_core.jsonl"
    summary_path.parent.mkdir(parents=True)
    summary_path.write_text(json.dumps(summary, sort_keys=True), encoding="utf-8")
    replay_path.write_text('{"frame_index":0,"phase":"decode"}\n', encoding="utf-8")
    summary_hash = hashlib.sha256(summary_path.read_bytes()).hexdigest()
    replay_hash = hashlib.sha256(replay_path.read_bytes()).hexdigest()
    manifest = {
        "schema_version": 1,
        "run_key": "run-warm",
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
    return summary


def test_ingest_warm_compose_preserves_solver_summary_json(tmp_path: Path) -> None:
    """Regression: replay warm persist must not wipe artifact ``solver_summary_json``."""

    project = m.AsteroidProject.objects.create(name="Warm", slug="warm-summary")
    _write_artifact_with_stack_summary(tmp_path)
    renderable_frame = {
        "frame_index": 0,
        "map_view": {
            "full_cells": [{"x": 0, "y": 0, "cell_kind": "asteroid_shape_field"}],
        },
    }
    with (
        patch(
            "django_apps.asteroid_lab.services.artifact_ingest.build_lab_replay_frames_for_project",
            return_value=([renderable_frame], {"frame_count": 1}),
        ),
        patch(
            "django_apps.asteroid_lab.services.artifact_ingest.lab_replay_frames_are_renderable",
            return_value=True,
        ),
    ):
        result = ingest_artifact_for_project(project_id=int(project.pk), artifact_dir=tmp_path)

    run = m.SolverRun.objects.get(pk=int(result.solver_run.pk))
    assert run.solver_summary_json.get("validation_passed") is True
    assert run.solver_summary_json.get("completed_layer_slugs")
    assert run.config_json[SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY]["validation_passed"] is True

    row = lab_run_summary_from_orm(run)
    assert row["validation_passed"] is True
    layers = {layer["layer_slug"]: layer for layer in row["layer_summaries"]}
    assert layers[LAYER_02_EXTERIOR_TRANSPORT]["outcome"] == "completed"
