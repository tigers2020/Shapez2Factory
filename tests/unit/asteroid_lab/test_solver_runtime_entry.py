"""Solver runtime entry — RTTP wire + disabled stub."""

from __future__ import annotations

import base64
import gzip
import json

import pytest
from django.test import override_settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.input_service import create_copy_code_map_input
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    SOLVER_NOT_AVAILABLE_MESSAGE,
    SolverRuntimeEntryErrorCode,
    entry_result_to_json_dict,
    run_solver_runtime_for_project,
)

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


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_solver_runtime_entry_rttp_returns_solver_run_id() -> None:
    proj = m.AsteroidProject.objects.create(name="Rttp", slug="entry-rttp")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    result = run_solver_runtime_for_project(int(proj.pk))
    assert result.solver_run_id is not None
    assert result.error_code != SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE


_SUMMARY_COMPARE_KEYS = (
    "algorithm",
    "validation_passed",
    "run_success",
    "confirmed_count",
    "target_miner_bundle_count",
    "commit_order",
    "normal_candidate_count",
)


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_rttp_runtime_solver_summary_unchanged_when_replay_persisted() -> None:
    """RTTP-RB1: DB replay frames must not change solver_summary scalars."""
    proj = m.AsteroidProject.objects.create(name="RttpRb1", slug="entry-rttp-rb1")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    project_id = int(proj.pk)

    off = run_solver_runtime_for_project(
        project_id,
        run_key="rb1-off",
        config={"rttp_record_replay": False},
    )
    on = run_solver_runtime_for_project(
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
