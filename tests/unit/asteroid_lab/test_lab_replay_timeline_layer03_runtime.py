"""Artifact replay includes solver runtime L3 milestones after subprocess run."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from django.test import override_settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.lab_replay_persisted_cache import (
    load_composed_frames_for_run_id,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import run_solver_runtime_for_project

pytestmark = pytest.mark.django_db

_REPO = Path(__file__).resolve().parents[3]
_COPY_FIXTURE = _REPO / "tests" / "fixtures" / "asteroid_lab" / "reconstruction_required_.txt"
_SNAPSHOT_FIXTURE = _REPO / "tests" / "fixtures" / "asteroid_lab" / "game_data_snapshot_min.json"


@override_settings(ASTEROID_LAB_LAYER_02_SOLVER_ENABLED=True)
def test_lab_replay_timeline_includes_layer03_runtime_after_solver_run() -> None:
    proj = m.AsteroidProject.objects.create(name="L3Runtime", slug="l3-runtime-timeline")
    copy_text = next(
        line.strip()
        for line in _COPY_FIXTURE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    m.AsteroidMapInput.objects.create(project=proj, copy_code=copy_text)
    snapshot_payload = json.loads(_SNAPSHOT_FIXTURE.read_text(encoding="utf-8"))
    result = run_solver_runtime_for_project(
        int(proj.pk),
        config={"throughput_target_percent": 80},
        game_data_snapshot=snapshot_payload,
    )
    assert result.ok is True
    assert result.solver_run_id is not None

    frames = load_composed_frames_for_run_id(int(result.solver_run_id))
    assert frames is not None
    layer_slugs = [str(f.get("layer_slug") or "") for f in frames]
    assert "layer_03_rim_greedy_placement" in layer_slugs
    run = m.SolverRun.objects.get(pk=int(result.solver_run_id))
    summary = dict(run.solver_summary_json or {})
    completed = list(summary.get("completed_layer_slugs") or [])
    assert "layer_03_rim_greedy_placement" in completed
