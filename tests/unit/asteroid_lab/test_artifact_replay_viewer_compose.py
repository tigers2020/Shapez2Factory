"""Viewer compose: artifact replay_core must become renderable Lab timeline frames."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.artifact_replay_viewer_compose import (
    compose_lab_replay_frames_from_artifact_run,
    lab_replay_frames_are_renderable,
)
from django_apps.asteroid_lab.services.lab_replay_persisted_cache import (
    load_composed_frames_for_run_id,
)
from shapez2_factory.adapters.asteroid_lab.complete_map_serializer import serialize_complete_map
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from tests.support.reconstruction_complete_map_fixtures import minimal_complete_map_from_cells

pytestmark = pytest.mark.django_db


def _cell(x: int, y: int) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=x,
        y=y,
        layer="layer",
        rotation=0,
        tile_type="tile",
        cell_kind="asteroid_shape_field",
        transport_kind="shape",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={},
    )


def _write_artifact(
    artifact_dir: Path,
    *,
    run_key: str,
    core_lines: list[dict[str, object]],
) -> None:
    complete_map = minimal_complete_map_from_cells(_cell(0, 0), _cell(1, 0))
    summary_path = artifact_dir / "output" / "solver_summary.json"
    map_path = artifact_dir / "output" / "layer01_complete_map.json"
    replay_path = artifact_dir / "output" / "replay_core.jsonl"
    for path in (summary_path, map_path, replay_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    map_path.write_text(
        json.dumps(serialize_complete_map(complete_map), sort_keys=True),
        encoding="utf-8",
    )
    summary_path.write_text("{}", encoding="utf-8")
    header = {"record_type": "header", "run_key": run_key, "schema_version": 1}
    replay_path.write_text(
        json.dumps(header, sort_keys=True) + "\n"
        + "".join(json.dumps(line, sort_keys=True) + "\n" for line in core_lines),
        encoding="utf-8",
    )
    entries = {
        "output/layer01_complete_map.json": map_path,
        "output/replay_core.jsonl": replay_path,
        "output/solver_summary.json": summary_path,
    }
    content_hashes = {
        relpath: hashlib.sha256(path.read_bytes()).hexdigest() for relpath, path in entries.items()
    }
    manifest = {
        "schema_version": 1,
        "run_key": run_key,
        "lifecycle_status": "artifact_written",
        "created_at_utc": "2026-05-30T00:00:00Z",
        "core_build_id": "test",
        "content_hashes": content_hashes,
        "paths": {
            "layer01_complete_map": "output/layer01_complete_map.json",
            "replay_core": "output/replay_core.jsonl",
            "solver_summary": "output/solver_summary.json",
        },
        "game_data_provenance": {"source": "test"},
        "error_code": None,
    }
    (artifact_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_compose_lab_replay_frames_from_artifact_run_adds_map_view(tmp_path: Path) -> None:
    project = m.AsteroidProject.objects.create(name="Compose", slug="artifact-compose")
    run_key = "artifact-compose-run"
    core_lines = [
        {
            "record_type": "frame",
            "frame_index": 0,
            "event": "layer_done",
            "layer_slug": "layer_02_exterior_transport",
            "outcome": "completed",
            "elapsed_ms": 0,
        }
    ]
    _write_artifact(tmp_path, run_key=run_key, core_lines=core_lines)
    run = m.SolverRun.objects.create(
        project=project,
        run_key=run_key,
        artifact_root=str(tmp_path.resolve()),
        lifecycle_status="succeeded",
    )

    composed = compose_lab_replay_frames_from_artifact_run(run)

    assert composed is not None
    assert lab_replay_frames_are_renderable(composed)
    assert composed[0]["map_view"]["full_cells"]


def test_load_composed_frames_does_not_return_raw_replay_core(tmp_path: Path) -> None:
    project = m.AsteroidProject.objects.create(name="Raw", slug="artifact-raw")
    run_key = "artifact-raw-run"
    raw_frames = [{"frame_index": 0, "phase": "artifact-decode"}]
    _write_artifact(
        tmp_path,
        run_key=run_key,
        core_lines=[
            {
                "record_type": "frame",
                "frame_index": 0,
                "event": "layer_done",
                "layer_slug": "layer_06_commit_validate",
                "outcome": "completed",
                "elapsed_ms": 0,
            }
        ],
    )
    run = m.SolverRun.objects.create(
        project=project,
        run_key=run_key,
        artifact_root=str(tmp_path.resolve()),
        lab_replay_manifest_summary_json={
            "mode": "artifact_jsonl",
            "replay_core_path": str((tmp_path / "output" / "replay_core.jsonl").resolve()),
            "frame_count": 1,
        },
        lab_replay_payload_json={"composed_frames": raw_frames},
    )

    loaded = load_composed_frames_for_run_id(int(run.pk))

    assert loaded is None
