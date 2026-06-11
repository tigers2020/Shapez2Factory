"""HTTP lab-replay with solver_runtime_wires projection (Slice 6)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from django.test import Client
from django.urls import reverse

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.replay.event_types import EVENT_TYPE_LAYER03_RIM_GREEDY_COMPLETE
from django_apps.asteroid_lab.services.lab_replay_diagnostics import (
    DIAGNOSTIC_MISSING_RUNTIME_WIRES,
)
from tests.unit.asteroid_lab.test_runtime_wire_projection_compose import (
    _write_wires_artifact,
)

pytestmark = pytest.mark.django_db


def test_lab_replay_get_projects_wires_with_overlays(tmp_path: Path) -> None:
    project = m.AsteroidProject.objects.create(name="Wire", slug="wire-replay-http")
    run_key = "wire-replay-http-run"
    run = _write_wires_artifact(tmp_path, run_key=run_key)
    run.project = project
    run.save(update_fields=["project"])

    client = Client()
    url = reverse(
        "web:asteroid-miner-layout-project-solver-run-lab-replay",
        kwargs={"slug": project.slug, "run_id": int(run.pk)},
    )
    response = client.get(url)
    assert response.status_code == 200
    payload = json.loads(response.content.decode("utf-8"))
    assert payload["frame_count"] > 0
    metrics = payload.get("replay_track_metrics") or {}
    assert metrics.get("algorithm_rerun_count") == 0
    assert metrics.get("diagnostic_reason") in (None, "")
    frames = payload.get("frames") or []
    l3 = next(
        (fr for fr in frames if fr.get("event_type") == EVENT_TYPE_LAYER03_RIM_GREEDY_COMPLETE),
        None,
    )
    assert l3 is not None
    overlay = (l3.get("map_view") or {}).get("overlay_cells") or []
    assert overlay, "wire projection must emit L3 overlays on lab-replay GET"


def test_lab_replay_get_legacy_artifact_degrades_without_wires(tmp_path: Path) -> None:
    from tests.unit.asteroid_lab.test_artifact_replay_viewer_compose import _write_artifact

    project = m.AsteroidProject.objects.create(name="Legacy", slug="legacy-replay-http")
    run_key = "legacy-replay-run"
    _write_artifact(
        tmp_path,
        run_key=run_key,
        core_lines=[
            {
                "record_type": "frame",
                "frame_index": 0,
                "event": "layer_done",
                "layer_slug": "layer_02_exterior_transport",
                "outcome": "completed",
                "elapsed_ms": 0,
            }
        ],
    )
    run = m.SolverRun.objects.create(
        project=project,
        run_key=run_key,
        artifact_root=str(tmp_path.resolve()),
        lifecycle_status="succeeded",
    )

    client = Client()
    url = reverse(
        "web:asteroid-miner-layout-project-solver-run-lab-replay",
        kwargs={"slug": project.slug, "run_id": int(run.pk)},
    )
    response = client.get(url)
    assert response.status_code == 200
    payload = json.loads(response.content.decode("utf-8"))
    metrics = payload.get("replay_track_metrics") or {}
    assert metrics.get("diagnostic_reason") == DIAGNOSTIC_MISSING_RUNTIME_WIRES
    assert metrics.get("algorithm_rerun_count") == 0
