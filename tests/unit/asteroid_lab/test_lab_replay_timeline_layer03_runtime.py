"""Lab product timeline includes solver runtime L3 milestones after layer02 run."""

from __future__ import annotations

import pytest
from django.test import override_settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.replay.event_types import EVENT_TYPE_LAYER03_RIM_BUNDLE_SCAN_BEGIN
from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
    build_lab_replay_frames_for_project,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import run_solver_runtime_for_project

pytestmark = pytest.mark.django_db


def _minimal_copy() -> str:
    return "SHAPEZ2-4-e30="


@override_settings(ASTEROID_LAB_LAYER_02_SOLVER_ENABLED=True)
def test_lab_replay_timeline_includes_layer03_runtime_after_solver_run() -> None:
    proj = m.AsteroidProject.objects.create(name="L3Runtime", slug="l3-runtime-timeline")
    m.AsteroidMapInput.objects.create(project=proj, copy_code=_minimal_copy())
    result = run_solver_runtime_for_project(int(proj.pk), config={"throughput_target_percent": 80})
    assert result.ok is True
    assert result.solver_run_id is not None

    frames, _metrics = build_lab_replay_frames_for_project(int(proj.pk))
    event_types = [str(f.get("event_type") or "") for f in frames]
    assert EVENT_TYPE_LAYER03_RIM_BUNDLE_SCAN_BEGIN in event_types
