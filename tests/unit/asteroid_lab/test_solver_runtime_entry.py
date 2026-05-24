"""Solver runtime entry — RTTP wire + disabled stub."""

from __future__ import annotations

import base64
import gzip
import json
from dataclasses import replace

import pytest
from django.test import override_settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization import pipeline as rttp_pipeline
from django_apps.asteroid_lab.services.input_service import create_copy_code_map_input
from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    RTTP_MILESTONE_EVENT_TYPES,
)
from django_apps.asteroid_lab.services.replay_pipeline_service import (
    build_initial_replay_for_map_input,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot_provenance import (
    parse_provenance_config,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_PROVENANCE_KEY,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    SOLVER_NOT_AVAILABLE_MESSAGE,
    SolverRuntimeEntryErrorCode,
    entry_result_to_json_dict,
    run_solver_runtime_for_project,
)
from django_apps.web.services.asteroid_game_data_snapshot import (
    build_asteroid_game_data_snapshot_with_provenance,
)
from tests.unit.asteroid_lab._runtime_game_data import run_solver_runtime_with_pinned_game_data

pytestmark = pytest.mark.django_db


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


def test_solver_runtime_entry_requires_map_input() -> None:
    proj = m.AsteroidProject.objects.create(name="Empty", slug="entry-no-inp")
    result = run_solver_runtime_for_project(int(proj.pk))
    assert result.ok is False
    assert result.error_code == SolverRuntimeEntryErrorCode.NO_MAP_INPUT


@override_settings(ASTEROID_LAB_RTTP_ENABLED=False)
def test_solver_runtime_entry_returns_solver_not_available_when_rttp_disabled() -> None:
    proj = m.AsteroidProject.objects.create(name="Lab", slug="entry-stub")
    m.AsteroidMapInput.objects.create(project=proj, copy_code="SHAPEZ2-4-e30=")
    result = run_solver_runtime_for_project(int(proj.pk))
    assert result.ok is False
    assert result.error_code == SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE
    assert result.message == SOLVER_NOT_AVAILABLE_MESSAGE


@override_settings(ASTEROID_LAB_RTTP_ENABLED=False)
def test_entry_result_to_json_dict_includes_error_code_and_message() -> None:
    proj = m.AsteroidProject.objects.create(name="Lab2", slug="entry-stub-json")
    m.AsteroidMapInput.objects.create(project=proj, copy_code="SHAPEZ2-4-e30=")
    result = run_solver_runtime_for_project(int(proj.pk), config={"rttp_enabled": False})
    body = entry_result_to_json_dict(result)
    assert body["ok"] is False
    assert body["lab_replay_frame_count"] == 0
    assert body["error_code"] == SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE.value
    assert body["message"] == SOLVER_NOT_AVAILABLE_MESSAGE
    mile_metrics = body["lab_optimization_milestone_track_metrics"]
    assert mile_metrics["frame_count"] == 0
    assert mile_metrics["event_types"] == []
    assert "track_key" in mile_metrics
    assert "source_solver_run_id" in mile_metrics


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_solver_runtime_entry_rttp_returns_solver_run_id() -> None:
    proj = m.AsteroidProject.objects.create(name="Rttp", slug="entry-rttp")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    result = run_solver_runtime_with_pinned_game_data(int(proj.pk))
    assert result.solver_run_id is not None
    assert result.error_code != SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE


_SUMMARY_COMPARE_KEYS = (
    "algorithm",
    "macro_only_mode",
    "validation_passed",
    "run_success",
    "confirmed_count",
    "target_miner_bundle_count",
    "commit_order",
    "normal_candidate_count",
    "algorithm_steps",
)


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_rttp_runtime_solver_summary_unchanged_when_replay_persisted() -> None:
    """RTTP-RB1: DB replay frames must not change solver_summary scalars."""
    proj = m.AsteroidProject.objects.create(name="RttpRb1", slug="entry-rttp-rb1")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    project_id = int(proj.pk)

    off = run_solver_runtime_with_pinned_game_data(
        project_id,
        run_key="rb1-off",
        config={"rttp_record_replay": False},
    )
    on = run_solver_runtime_with_pinned_game_data(
        project_id,
        run_key="rb1-on",
        config={"rttp_record_replay": True},
    )

    assert off.solver_summary
    assert on.solver_summary
    for key in _SUMMARY_COMPARE_KEYS:
        assert off.solver_summary[key] == on.solver_summary[key]

    run = m.SolverRun.objects.get(pk=int(on.solver_run_id))
    track = m.ReplayTrack.objects.get(project_id=project_id, track_key="rb1-on:rttp")
    assert track.solver_run_id == run.id
    assert m.ReplayFrame.objects.filter(replay_track_id=track.id).count() >= 4
    lab_track = m.ReplayTrack.objects.get(project_id=project_id, track_key="rb1-on")
    assert m.ReplayFrame.objects.filter(replay_track_id=lab_track.id).count() == 0


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_entry_result_json_includes_optimization_milestone_section() -> None:
    proj = m.AsteroidProject.objects.create(name="MileJson", slug="mile-json")
    inp = create_copy_code_map_input(proj, _minimal_valid_copy())
    build_initial_replay_for_map_input(int(inp.pk), overwrite=True)
    result = run_solver_runtime_with_pinned_game_data(
        int(proj.pk),
        run_key="mile-json",
        config={"rttp_record_replay": True},
    )
    body = entry_result_to_json_dict(result)
    assert "lab_optimization_milestone_frames_json" in body
    assert "lab_optimization_milestone_frame_count" in body
    assert "lab_optimization_milestone_track_metrics" in body
    mile_types = {fr.get("event_type") for fr in body["lab_optimization_milestone_frames_json"]}
    assert RTTP_MILESTONE_EVENT_TYPES <= mile_types
    frames = body["lab_replay_frames_json"]
    assert body["lab_replay_frame_count"] == len(frames)
    assert not any(fr.get("render_mode") == "inherited_snapshot" for fr in frames)
    rttp_frames = [fr for fr in frames if fr.get("event_type") in RTTP_MILESTONE_EVENT_TYPES]
    assert len(rttp_frames) >= 4
    for fr in rttp_frames:
        assert len((fr.get("map_view") or {}).get("full_cells") or []) >= 1
    first_rttp_idx = frames.index(rttp_frames[0])
    map_prefix = frames[:first_rttp_idx]
    map_types = {fr.get("event_type") for fr in map_prefix}
    assert map_types.isdisjoint(RTTP_MILESTONE_EVENT_TYPES)


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_rttp_validation_failure_still_returns_optimization_milestones_section(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_run = rttp_pipeline.run_rttp_pipeline

    def _run_with_failed_validation(
        *args: object, **kwargs: object
    ) -> rttp_pipeline.PipelineResult:
        result = real_run(*args, **kwargs)
        return replace(result, validation_passed=False)

    monkeypatch.setattr(rttp_pipeline, "run_rttp_pipeline", _run_with_failed_validation)

    proj = m.AsteroidProject.objects.create(name="MileFail", slug="mile-fail")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    result = run_solver_runtime_with_pinned_game_data(
        int(proj.pk),
        run_key="mile-fail",
        config={"rttp_record_replay": True},
    )
    assert result.ok is False
    assert result.validation_passed is False
    assert result.error_code == SolverRuntimeEntryErrorCode.RTTP_VALIDATION_FAILED
    assert len(result.lab_optimization_milestone_frames_json) >= 4
    body = entry_result_to_json_dict(result)
    assert body["lab_optimization_milestone_frame_count"] == len(
        body["lab_optimization_milestone_frames_json"]
    )
    assert RTTP_MILESTONE_EVENT_TYPES <= {
        fr.get("event_type") for fr in body["lab_optimization_milestone_frames_json"]
    }


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_rttp_run_persists_game_data_snapshot_provenance() -> None:
    build = build_asteroid_game_data_snapshot_with_provenance()
    proj = m.AsteroidProject.objects.create(name="Prov", slug="prov-gate")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    result = run_solver_runtime_for_project(
        int(proj.pk),
        game_data_snapshot=build.snapshot,
        game_data_provenance=build.provenance,
        catalog_slice=build.catalog_slice,
    )
    assert result.solver_run_id is not None
    run = m.SolverRun.objects.get(pk=int(result.solver_run_id))
    parsed = parse_provenance_config(
        run.config_json[SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_PROVENANCE_KEY]
    )
    assert parsed == build.provenance


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_rttp_run_without_provenance_returns_provenance_incomplete() -> None:
    build = build_asteroid_game_data_snapshot_with_provenance()
    proj = m.AsteroidProject.objects.create(name="NoProv", slug="no-prov-gate")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    result = run_solver_runtime_for_project(
        int(proj.pk),
        game_data_snapshot=build.snapshot,
        game_data_provenance=None,
        catalog_slice=None,
    )
    assert result.ok is False
    assert result.error_code == SolverRuntimeEntryErrorCode.PROVENANCE_INCOMPLETE
    assert result.solver_run_id is None


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_rttp_run_without_catalog_slice_returns_catalog_slice_required() -> None:
    build = build_asteroid_game_data_snapshot_with_provenance()
    proj = m.AsteroidProject.objects.create(name="NoSlice", slug="no-slice-gate")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    result = run_solver_runtime_for_project(
        int(proj.pk),
        game_data_snapshot=build.snapshot,
        game_data_provenance=build.provenance,
        catalog_slice=None,
    )
    assert result.ok is False
    assert result.error_code == SolverRuntimeEntryErrorCode.CATALOG_SLICE_REQUIRED
    assert result.solver_run_id is None


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_rttp_run_catalog_slice_hash_mismatch() -> None:
    from dataclasses import replace

    from django_apps.asteroid_lab.contracts.building_catalog_slice_hash import (
        catalog_slice_hash,
    )

    build = build_asteroid_game_data_snapshot_with_provenance()
    bad_prov = replace(build.provenance, catalog_slice_hash="b" * 64)
    proj = m.AsteroidProject.objects.create(name="Hash", slug="hash-mismatch")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    result = run_solver_runtime_for_project(
        int(proj.pk),
        game_data_snapshot=build.snapshot,
        game_data_provenance=bad_prov,
        catalog_slice=build.catalog_slice,
    )
    assert result.ok is False
    assert result.error_code == SolverRuntimeEntryErrorCode.CATALOG_SLICE_HASH_MISMATCH
    assert catalog_slice_hash(build.catalog_slice) != bad_prov.catalog_slice_hash
