"""Orchestrate lab solver run rows and default replay scaffolding.

Creating ``ReplayTrack`` rows here is **persistence for UI only**. The solver core must keep
using in-memory DTOs — never read ``ReplayFrame`` / ``ReplayTrack`` as algorithm input.
"""

from __future__ import annotations

from django.db import transaction

from django_apps.asteroid_lab.models import AsteroidProject, ReplayTrack, SolverRun
from django_apps.asteroid_lab.services.dto import ReplayTrackRefDTO, SolverRunDTO
from django_apps.asteroid_lab.services.solver_run_fast_cache import (
    empty_solver_run_fast_cache_kwargs,
    sync_solver_run_fast_cache_from_config_json,
)


@transaction.atomic
def create_solver_run(
    project_id: int,
    *,
    run_key: str,
    algorithm_label: str,
    config: dict[str, object],
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
        **empty_solver_run_fast_cache_kwargs(),
    )
    sync_solver_run_fast_cache_from_config_json(run)
    track = ensure_default_replay_track(
        project_id,
        run.id,
        track_key=run_key,
        title="",
    )
    return _solver_run_dto(run, replay_track_id=track.track_id)


@transaction.atomic
def create_or_replace_solver_run(
    project_id: int,
    *,
    run_key: str,
    algorithm_label: str,
    config: dict[str, object],
) -> SolverRunDTO:
    """Insert a ``SolverRun``, replacing any prior row for the same ``(project, run_key)``.

    Clears replay frames on the default track, deletes the prior run (cascade metric rows),
    then creates a fresh run and re-links the track.
    """

    existing = SolverRun.objects.filter(project_id=project_id, run_key=run_key).first()
    if existing is not None:
        track = ReplayTrack.objects.filter(project_id=project_id, track_key=run_key).first()
        if track is not None:
            track.frames.all().delete()
        existing.delete()
    return create_solver_run(
        project_id,
        run_key=run_key,
        algorithm_label=algorithm_label,
        config=dict(config or {}),
    )


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


@transaction.atomic
def resolve_inspection_solver_run(
    project_id: int,
    *,
    run_key: str,
    algorithm_label: str,
    config: dict[str, object] | None = None,
    overwrite: bool = False,
) -> SolverRunDTO:
    """Create a new inspection run, or reuse and clear frames when ``overwrite`` is true."""

    if overwrite:
        run = SolverRun.objects.filter(project_id=project_id, run_key=run_key).first()
        if run is not None:
            track = ReplayTrack.objects.filter(project_id=project_id, track_key=run_key).first()
            if track is not None:
                track.frames.all().delete()
            ref = ensure_default_replay_track(project_id, run.id, track_key=run_key)
            return _solver_run_dto(run, replay_track_id=ref.track_id)
    return create_solver_run(
        project_id,
        run_key=run_key,
        algorithm_label=algorithm_label,
        config=dict(config or {}),
    )


__all__ = [
    "create_or_replace_solver_run",
    "create_solver_run",
    "ensure_default_replay_track",
    "resolve_inspection_solver_run",
]
