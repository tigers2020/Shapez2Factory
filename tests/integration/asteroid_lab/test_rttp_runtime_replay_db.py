"""RTTP runtime — DB replay persistence smoke (PR-B)."""

from __future__ import annotations

import base64
import gzip
import json

import pytest
from django.test import override_settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.input_service import create_copy_code_map_input
from django_apps.asteroid_lab.services.solver_runtime_entry import run_solver_runtime_for_project

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


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


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_run_solver_persists_rttp_replay_frames_when_recording_enabled() -> None:
    proj = m.AsteroidProject.objects.create(name="RttpInt", slug="rttp-int-db")
    create_copy_code_map_input(proj, _minimal_valid_copy())

    result = run_solver_runtime_for_project(
        int(proj.pk),
        run_key="rttp-int",
        config={"rttp_record_replay": True},
    )

    assert result.solver_run_id is not None
    track = m.ReplayTrack.objects.get(project_id=int(proj.pk), track_key="rttp-int")
    frame_count = m.ReplayFrame.objects.filter(replay_track_id=track.id).count()
    assert frame_count >= 4
