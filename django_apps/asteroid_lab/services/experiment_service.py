"""Orchestrate lab solver run rows and default replay scaffolding.

Creating ``ReplayTrack`` rows here is **persistence for UI only**. The solver core must keep
using in-memory DTOs — never read ``ReplayFrame`` / ``ReplayTrack`` as algorithm input.
"""

from __future__ import annotations

from typing import Any

from django.db import transaction

from django_apps.asteroid_lab.models import AsteroidProject, ReplayTrack, SolverRun
from django_apps.asteroid_lab.services.dto import ReplayTrackRefDTO, SolverRunDTO


@transaction.atomic
def create_solver_run(
    project_id: int,
    *,
    run_key: str,
    algorithm_label: str,
    config: dict[str, Any],
) -> SolverRunDTO:
    """Insert one ``SolverRun`` plus default ``ReplayTrack`` scaffolding.

    Does **not** execute solver algorithms. Persisted replay rows are UI-only — never solver
    algorithm input.
    """

    if not AsteroidProject.objects.filter(pk=project_id).exists():
        msg = f"AsteroidProject id={project_id} does not exist"
        raise ValueError(msg)

    run = SolverRun.objects.create(
        project_id=project_id,
        run_key=run_key,
        algorithm_label=algorithm_label,
        config_json=dict(config or {}),
    )
    track = ensure_default_replay_track(
        project_id,
        run.id,
        track_key=run_key,
        title="",
    )
    return _solver_run_dto(run, replay_track_id=track.track_id)


def _solver_run_dto(run: SolverRun, *, replay_track_id: int) -> SolverRunDTO:
    return SolverRunDTO(
        id=run.id,
        project_id=run.project_id,
        run_key=run.run_key,
        algorithm_label=run.algorithm_label,
        status=run.status,
        config_json=dict(run.config_json or {}),
        replay_track_id=replay_track_id,
    )


@transaction.atomic
def ensure_default_replay_track(
    project_id: int,
    solver_run_id: int,
    *,
    track_key: str = "main",
    title: str = "",
) -> ReplayTrackRefDTO:
    """Ensure a ``ReplayTrack`` exists for (project, ``track_key``), linked to ``solver_run``.

    Empty track scaffolding only — **no** ``ReplayFrame`` rows and **no** solver input.
    """

    if not AsteroidProject.objects.filter(pk=project_id).exists():
        msg = f"AsteroidProject id={project_id} does not exist"
        raise ValueError(msg)
    run = SolverRun.objects.filter(pk=solver_run_id, project_id=project_id).first()
    if run is None:
        msg = f"SolverRun id={solver_run_id} not in project id={project_id}"
        raise ValueError(msg)

    track, _created = ReplayTrack.objects.select_for_update().get_or_create(
        project_id=project_id,
        track_key=track_key,
        defaults={"solver_run": run, "title": title},
    )
    if track.solver_run_id is None:
        track.solver_run = run
        if title and not track.title:
            track.title = title
        track.save(update_fields=["solver_run", "title"])
    return ReplayTrackRefDTO(
        track_id=track.id,
        project_id=track.project_id,
        solver_run_id=track.solver_run_id,
        track_key=track.track_key,
    )
