"""A6.2 replay pipeline orchestration (decode + inspection frames only)."""

from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services import project_service
from django_apps.asteroid_lab.services.replay_pipeline_service import (
    build_initial_replay_for_map_input,
)


def _encode_v4_copy(root: dict) -> str:
    text = json.dumps(root, separators=(",", ":")).encode("utf-8")
    gz = gzip.compress(text)
    b64 = base64.b64encode(gz).decode("ascii")
    return f"SHAPEZ2-4-{b64}"


def _minimal_root(*, version: int = 42) -> dict:
    return {
        "V": version,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_ProMiner"},
                {"X": 2, "Y": 0, "T": "SpaceBelt_Left"},
            ],
        },
    }


@pytest.mark.slow
@pytest.mark.django_db
def test_build_initial_replay_creates_run_track_frames_and_snapshots() -> None:
    code = _encode_v4_copy(_minimal_root(version=7))
    dto = project_service.create_project_from_copy_code(code, source_label="pipe")
    result = build_initial_replay_for_map_input(dto.map_input_id)

    assert result.status == "ok"
    assert result.solver_run_id is not None
    assert result.replay_track_id is not None
    assert result.replay_frame_count >= 6
    assert result.decoded_snapshot_id is not None
    assert result.existing_layout_snapshot_id is not None

    inp = m.AsteroidMapInput.objects.get(pk=dto.map_input_id)
    assert inp.decoded_json.get("_asteroid_lab_summary") is not None
    assert m.ReplayFrame.objects.filter(replay_track_id=result.replay_track_id).count() >= 6
    assert m.AsteroidCellSnapshot.objects.filter(
        map_input=inp, layer="decoded_blueprint_top"
    ).exists()
    assert m.AsteroidCellSnapshot.objects.filter(
        map_input=inp, layer="existing_layout_inspection"
    ).exists()

    types = [
        str(f.frame_payload.get("event_type") or "")
        for f in m.ReplayFrame.objects.filter(replay_track_id=result.replay_track_id).order_by(
            "frame_index", "id"
        )
    ]
    assert types[0] == et.EVENT_TYPE_DECODE_RAW_LOADED
    assert types[1] == et.EVENT_TYPE_DECODE_NORMALIZED
    assert et.EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_TRANSPORT in types
    assert et.EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_EXTRACTOR in types
    assert et.EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_EXTENSION in types
    recon_phase_types = frozenset(
        {
            et.EVENT_TYPE_RECONSTRUCTION_BEGIN,
            et.EVENT_TYPE_RECONSTRUCTION_SHELL_DETECTED,
            et.EVENT_TYPE_RECONSTRUCTION_EXTERNAL_FLOOD_FILL,
            et.EVENT_TYPE_RECONSTRUCTION_INTERNAL_VOID_DETECTED,
            et.EVENT_TYPE_RECONSTRUCTION_INTERIOR_PATCH_MARKED,
            et.EVENT_TYPE_RECONSTRUCTION_MINEABLE_FINALIZED,
        }
    )
    assert any(t in recon_phase_types for t in types)
    assert et.EVENT_TYPE_REPLAY_SNAPSHOT_RECONSTRUCTION not in types


@pytest.mark.slow
@pytest.mark.django_db
def test_build_initial_replay_idempotent_without_force() -> None:
    code = _encode_v4_copy(_minimal_root(version=11))
    dto = project_service.create_project_from_copy_code(code, source_label="idem")
    r1 = build_initial_replay_for_map_input(dto.map_input_id)
    r2 = build_initial_replay_for_map_input(dto.map_input_id)
    assert r1.status == "ok" and r2.status == "ok"
    assert r1.replay_track_id == r2.replay_track_id
    assert r1.solver_run_id == r2.solver_run_id
    assert m.SolverRun.objects.filter(project_id=dto.project_id).count() == 1
    assert m.ReplayFrame.objects.filter(replay_track_id=r1.replay_track_id).count() >= 6


@pytest.mark.slow
@pytest.mark.django_db
def test_build_initial_replay_invalid_copy_no_run() -> None:
    dto = project_service.create_project_from_copy_code(
        "not-a-valid-shapez-copy", source_label="bad"
    )
    result = build_initial_replay_for_map_input(dto.map_input_id)

    assert result.status == "failed"
    assert result.solver_run_id is None
    assert result.replay_track_id is None
    assert result.replay_frame_count == 0
    assert m.SolverRun.objects.filter(project_id=dto.project_id).count() == 0


@pytest.mark.slow
@pytest.mark.django_db
def test_build_initial_replay_force_uses_new_run_key() -> None:
    code = _encode_v4_copy(_minimal_root(version=99))
    dto = project_service.create_project_from_copy_code(code, source_label="force")
    r1 = build_initial_replay_for_map_input(dto.map_input_id)
    r2 = build_initial_replay_for_map_input(dto.map_input_id, force=True)
    assert r1.status == "ok" and r2.status == "ok"
    assert r1.run_key != r2.run_key
    assert m.SolverRun.objects.filter(project_id=dto.project_id).count() == 2


def test_replay_pipeline_service_has_no_forbidden_imports() -> None:
    lab_root = Path(__file__).resolve().parents[3] / "django_apps" / "asteroid_lab" / "services"
    path = lab_root / "replay_pipeline_service.py"
    text = path.read_text(encoding="utf-8")
    forbidden = (
        "django_apps.shapez_asteroid",
        "django_apps.shapez_solver",
        "django_apps.shapez_core",
        "asteroid_mining_layout_v2",
        "asteroid_mining_layout_v1",
    )
    for bad in forbidden:
        assert bad not in text, f"{path.name} must not mention {bad!r}"
