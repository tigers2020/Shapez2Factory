"""Projection context resolution for Lab replay timeline."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
    resolve_replay_projection_context_for_project,
)


@pytest.mark.django_db
def test_projection_context_uses_fallback_full_cells() -> None:
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
    )

    ctx = resolve_replay_projection_context_for_project(int(p.pk))
    assert ctx.fallback_full_cells == ()
