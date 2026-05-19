"""Projection context resolution for unified optimization replay (read path)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
    resolve_replay_projection_context_for_project,
)
from django_apps.asteroid_lab.services.optimization_ui_payload import (
    SOLVER_RUN_CONFIG_SERVER_XY_PARAMS_KEY,
)


@pytest.mark.django_db
def test_projection_prefers_solver_run_server_xy_params_over_lab_track() -> None:
    p = m.AsteroidProject.objects.create(name="Proj", slug="proj-params-priority")
    t = m.ReplayTrack.objects.create(project=p, track_key="lab-tr")
    m.ReplayFrame.objects.create(
        replay_track=t,
        frame_index=0,
        frame_key="decode-0",
        phase="decode",
        title="Decode",
        description="",
        frame_payload={
            "full_map": [{"x": 5, "y": 0, "cell_kind": "asteroid", "transport_kind": "none"}],
        },
        cell_overlay_json={},
    )
    m.SolverRun.objects.create(
        project=p,
        run_key="rk",
        config_json={SOLVER_RUN_CONFIG_SERVER_XY_PARAMS_KEY: [9, 2]},
    )

    ctx = resolve_replay_projection_context_for_project(int(p.pk))
    assert ctx is not None
    assert ctx.server_xy_params == (9, 2)
