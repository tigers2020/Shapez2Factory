"""Reset Lab project map to inspection-only DB state (decode + cleanup/reconstruction)."""

from __future__ import annotations

from enum import StrEnum

from django.db import transaction

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.dto import InitialReplayPipelineResultDTO
from django_apps.asteroid_lab.services.input_service import content_sha256_for_copy_code
from django_apps.asteroid_lab.services.replay_pipeline_service import (
    _default_run_key,
    build_initial_replay_for_map_input,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY,
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
)

INSPECTION_ALGORITHM_LABEL = "inspection_only"


class LabMapResetErrorCode(StrEnum):
    """Structured reset failure codes (no free-form strings)."""

    PROJECT_NOT_FOUND = "project_not_found"
    NO_MAP_INPUT = "no_map_input"
    RESET_FAILED = "reset_failed"


def _inspection_run_key_for_map_input(inp: m.AsteroidMapInput) -> str:
    digest = (inp.content_sha256 or "").strip() or content_sha256_for_copy_code(inp.copy_code)
    return _default_run_key(int(inp.pk), digest)


@transaction.atomic  # type: ignore[untyped-decorator]
def reset_project_map_to_inspection_clean(project_id: int) -> InitialReplayPipelineResultDTO:
    """Drop runtime solver artifacts; rebuild inspection replay (map clean through recon)."""

    project = m.AsteroidProject.objects.filter(pk=int(project_id)).first()
    if project is None:
        return InitialReplayPipelineResultDTO(
            project_id=int(project_id),
            map_input_id=0,
            solver_run_id=None,
            replay_track_id=None,
            replay_frame_count=0,
            decoded_snapshot_id=None,
            existing_layout_snapshot_id=None,
            reconstructed_asteroid_map_id=None,
            status="failed",
            error_message=LabMapResetErrorCode.PROJECT_NOT_FOUND.value,
            run_key="",
        )

    inp = (
        m.AsteroidMapInput.objects.filter(project_id=int(project.pk))
        .order_by("-created_at", "-id")
        .first()
    )
    if inp is None:
        return InitialReplayPipelineResultDTO(
            project_id=int(project.pk),
            map_input_id=0,
            solver_run_id=None,
            replay_track_id=None,
            replay_frame_count=0,
            decoded_snapshot_id=None,
            existing_layout_snapshot_id=None,
            reconstructed_asteroid_map_id=None,
            status="failed",
            error_message=LabMapResetErrorCode.NO_MAP_INPUT.value,
            run_key="",
        )

    inspection_run_key = _inspection_run_key_for_map_input(inp)

    runtime_run_ids = list(
        m.SolverRun.objects.filter(project_id=int(project.pk))
        .exclude(algorithm_label=INSPECTION_ALGORITHM_LABEL)
        .values_list("pk", flat=True)
    )
    if runtime_run_ids:
        m.ReplayTrack.objects.filter(solver_run_id__in=runtime_run_ids).delete()
        m.SolverRun.objects.filter(pk__in=runtime_run_ids).delete()

    m.ReplayTrack.objects.filter(project_id=int(project.pk)).exclude(
        track_key=inspection_run_key
    ).delete()

    m.ReconstructedAsteroidMap.objects.filter(map_input_id=int(inp.pk)).delete()
    m.AsteroidCellSnapshot.objects.filter(map_input_id=int(inp.pk)).delete()

    inspection_run = m.SolverRun.objects.filter(
        project_id=int(project.pk),
        run_key=inspection_run_key,
        algorithm_label=INSPECTION_ALGORITHM_LABEL,
    ).first()
    if inspection_run is not None:
        config = dict(inspection_run.config_json or {})
        config.pop(SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY, None)
        config.pop(SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY, None)
        m.SolverRun.objects.filter(pk=int(inspection_run.pk)).update(config_json=config)

    result = build_initial_replay_for_map_input(int(inp.pk), overwrite=True)
    if result.status != "ok":
        return InitialReplayPipelineResultDTO(
            project_id=int(project.pk),
            map_input_id=int(inp.pk),
            solver_run_id=result.solver_run_id,
            replay_track_id=result.replay_track_id,
            replay_frame_count=result.replay_frame_count,
            decoded_snapshot_id=result.decoded_snapshot_id,
            existing_layout_snapshot_id=result.existing_layout_snapshot_id,
            reconstructed_asteroid_map_id=result.reconstructed_asteroid_map_id,
            status="failed",
            error_message=result.error_message or LabMapResetErrorCode.RESET_FAILED.value,
            run_key=result.run_key,
        )
    return result


__all__ = [
    "INSPECTION_ALGORITHM_LABEL",
    "LabMapResetErrorCode",
    "reset_project_map_to_inspection_clean",
]
