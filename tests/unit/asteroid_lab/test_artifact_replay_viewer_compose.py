"""Viewer compose: artifact replay_core must become renderable Lab timeline frames."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_03_RIM_GREEDY_PLACEMENT,
)
from django_apps.asteroid_lab.replay.event_types import EVENT_TYPE_LAYER03_RIM_GREEDY_COMPLETE
from django_apps.asteroid_lab.services.artifact_replay_viewer_compose import (
    compose_lab_replay_frames_from_artifact_run,
    lab_replay_frames_are_renderable,
)
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.services.lab_replay_persisted_cache import (
    load_composed_frames_for_run_id,
)
from shapez2_factory.adapters.asteroid_lab.complete_map_serializer import serialize_complete_map
from tests.support.reconstruction_complete_map_fixtures import minimal_complete_map_from_cells
from tests.unit.asteroid_lab.layers.helpers.l02_complete_map_fixtures import (
    build_rect_field_with_void_shell,
)

pytestmark = pytest.mark.django_db

_REPO = Path(__file__).resolve().parents[2]
_SNAPSHOT_FIXTURE = _REPO / "fixtures" / "asteroid_lab" / "game_data_snapshot_min.json"


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
    complete_map=None,
    solver_summary: dict[str, object] | None = None,
    include_game_data_snapshot: bool = False,
) -> None:
    if complete_map is None:
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
    summary_path.write_text(
        json.dumps(solver_summary or {}, sort_keys=True),
        encoding="utf-8",
    )
    header = {"record_type": "header", "run_key": run_key, "schema_version": 1}
    replay_path.write_text(
        json.dumps(header, sort_keys=True)
        + "\n"
        + "".join(json.dumps(line, sort_keys=True) + "\n" for line in core_lines),
        encoding="utf-8",
    )
    snapshot_path = artifact_dir / "input" / "game_data_snapshot.json"
    if include_game_data_snapshot and _SNAPSHOT_FIXTURE.is_file():
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(_SNAPSHOT_FIXTURE, snapshot_path)
    entries = {
        "output/layer01_complete_map.json": map_path,
        "output/replay_core.jsonl": replay_path,
        "output/solver_summary.json": summary_path,
    }
    paths = {
        "layer01_complete_map": "output/layer01_complete_map.json",
        "replay_core": "output/replay_core.jsonl",
        "solver_summary": "output/solver_summary.json",
    }
    if include_game_data_snapshot and snapshot_path.is_file():
        entries["input/game_data_snapshot.json"] = snapshot_path
        paths["game_data_snapshot"] = "input/game_data_snapshot.json"
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
        "paths": paths,
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


def test_compose_artifact_run_includes_l3_append_overlays_when_snapshot_present(
    tmp_path: Path,
) -> None:
    project = m.AsteroidProject.objects.create(name="L3", slug="artifact-l3-append")
    run_key = "artifact-l3-append-run"
    complete_map = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    core_lines = [
        {
            "record_type": "frame",
            "frame_index": 0,
            "event": "layer_done",
            "layer_slug": "layer_02_exterior_transport",
            "outcome": "completed",
            "elapsed_ms": 1,
        },
        {
            "record_type": "frame",
            "frame_index": 1,
            "event": "layer_done",
            "layer_slug": LAYER_03_RIM_GREEDY_PLACEMENT,
            "outcome": "completed",
            "elapsed_ms": 2,
        },
    ]
    _write_artifact(
        tmp_path,
        run_key=run_key,
        core_lines=core_lines,
        complete_map=complete_map,
        include_game_data_snapshot=True,
        solver_summary={
            "throughput_target_percent": 80,
            "completed_layer_slugs": [LAYER_03_RIM_GREEDY_PLACEMENT],
            "layer_summaries": [
                {
                    "layer_slug": LAYER_03_RIM_GREEDY_PLACEMENT,
                    "outcome": "completed",
                    "metrics": {"committed_placement_count": 1},
                }
            ],
        },
    )
    run = m.SolverRun.objects.create(
        project=project,
        run_key=run_key,
        artifact_root=str(tmp_path.resolve()),
        lifecycle_status="succeeded",
    )

    composed = compose_lab_replay_frames_from_artifact_run(run)

    assert composed is not None
    assert lab_replay_frames_are_renderable(composed)
    event_types = [str(fr.get("event_type") or "") for fr in composed]
    assert EVENT_TYPE_LAYER03_RIM_GREEDY_COMPLETE in event_types
    complete = next(
        fr for fr in composed if fr.get("event_type") == EVENT_TYPE_LAYER03_RIM_GREEDY_COMPLETE
    )
    overlay = (complete.get("map_view") or {}).get("overlay_cells") or []
    assert overlay
    kinds = {row.get("kind") for row in overlay if isinstance(row, dict)}
    assert "shape_miner" in kinds or "committed_miner" in kinds


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
