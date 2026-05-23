"""RTTP runtime — DB replay persistence smoke (PR-B) + H1-R unified lab replay.

PR-B smoke (required):
  - ``ReplayTrack`` at ``rttp_optimization_track_key(run_key)`` with >= 4 frames
  - RTTP milestone ``event_type`` values on that track

H1-R (unified ``lab_replay_frames_json``):
  - Map-prefix frames exclude RTTP milestone event types
  - Tail frames use ``render_mode == inherited_snapshot`` and carry RTTP milestones
  - Section B ``lab_optimization_milestone_frames_json`` remains diagnostic (no map payload)
"""

from __future__ import annotations

import base64
import gzip
import json

import pytest
from django.test import override_settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.replay_track_keys import rttp_optimization_track_key
from django_apps.asteroid_lab.services.input_service import create_copy_code_map_input
from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    RTTP_MILESTONE_EVENT_TYPES,
)
from django_apps.asteroid_lab.services.replay_pipeline_service import (
    build_initial_replay_for_map_input,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    entry_result_to_json_dict,
    run_solver_runtime_for_project,
)

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
    track = m.ReplayTrack.objects.get(
        project_id=int(proj.pk),
        track_key=rttp_optimization_track_key("rttp-int"),
    )
    frame_count = m.ReplayFrame.objects.filter(replay_track_id=track.id).count()
    assert frame_count >= 4


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_run_solver_lab_json_unified_replay_includes_rttp_at_tail() -> None:
    """H1-R: lab JSON has inherited-snapshot RTTP tail; ``:rttp`` track still persisted."""

    proj = m.AsteroidProject.objects.create(name="RttpLabSplit", slug="rttp-lab-split")
    inp = create_copy_code_map_input(proj, _minimal_valid_copy())
    build_initial_replay_for_map_input(int(inp.pk), overwrite=True)

    result = run_solver_runtime_for_project(
        int(proj.pk),
        run_key="rttp-lab",
        config={"rttp_record_replay": True},
    )
    body = entry_result_to_json_dict(result)
    frames = body["lab_replay_frames_json"]

    assert body["lab_replay_frame_count"] == len(frames)
    assert body["lab_replay_frame_count"] > 0

    first_inherited = next(
        (i for i, fr in enumerate(frames) if fr.get("render_mode") == "inherited_snapshot"),
        None,
    )
    if first_inherited is None:
        map_prefix = frames
    else:
        map_prefix = frames[:first_inherited]
    map_types = {fr.get("event_type") for fr in map_prefix}
    assert map_types.isdisjoint(RTTP_MILESTONE_EVENT_TYPES)

    tail = [fr for fr in frames if fr.get("render_mode") == "inherited_snapshot"]
    assert len(tail) >= 4
    assert RTTP_MILESTONE_EVENT_TYPES <= {fr["event_type"] for fr in tail}
    for fr in tail:
        assert fr.get("base_frame_index") is not None
        assert "full_map" not in fr
        map_view = fr.get("map_view") or {}
        assert not map_view.get("full_cells")

    milestones = body["lab_optimization_milestone_frames_json"]
    assert body["lab_optimization_milestone_frame_count"] == len(milestones)
    assert len(milestones) >= 4
    mile_types = {fr.get("event_type") for fr in milestones}
    assert RTTP_MILESTONE_EVENT_TYPES <= mile_types
    for fr in milestones:
        assert "map_view" not in fr
        assert "full_map" not in fr

    rttp_track = m.ReplayTrack.objects.get(
        project_id=int(proj.pk),
        track_key=rttp_optimization_track_key("rttp-lab"),
    )
    assert m.ReplayFrame.objects.filter(replay_track_id=rttp_track.id).count() >= 4
    rttp_types = set(
        m.ReplayFrame.objects.filter(replay_track_id=rttp_track.id).values_list(
            "frame_payload__event_type",
            flat=True,
        )
    )
    assert RTTP_MILESTONE_EVENT_TYPES <= rttp_types
