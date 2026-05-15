"""``experiment_service`` — solver run + replay track scaffolding."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services import experiment_service


@pytest.mark.django_db
def test_create_solver_run_dto() -> None:
    p = m.AsteroidProject.objects.create(name="E", slug="e-svc")
    dto = experiment_service.create_solver_run(
        p.id,
        run_key="run-1",
        algorithm_label="ga_hybrid",
        config={"pop": 40},
    )
    assert dto.project_id == p.id
    assert dto.run_key == "run-1"
    assert dto.config_json == {"pop": 40}
    row = m.SolverRun.objects.get(pk=dto.id)
    assert row.status == m.SolverRun.RunStatus.PENDING


@pytest.mark.django_db
def test_create_solver_run_rejects_unknown_project() -> None:
    with pytest.raises(ValueError, match="does not exist"):
        experiment_service.create_solver_run(999_999, run_key="x", algorithm_label="a", config={})


@pytest.mark.django_db
def test_ensure_default_replay_track_links_run() -> None:
    p = m.AsteroidProject.objects.create(name="E2", slug="e2-svc")
    run = m.SolverRun.objects.create(project=p, run_key="r1", algorithm_label="ga")
    ref = experiment_service.ensure_default_replay_track(p.id, run.id, track_key="main")
    assert ref.track_key == "main"
    assert ref.solver_run_id == run.id
    track = m.ReplayTrack.objects.get(pk=ref.track_id)
    assert track.solver_run_id == run.id
