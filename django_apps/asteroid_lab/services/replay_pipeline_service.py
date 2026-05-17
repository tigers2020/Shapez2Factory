"""A6.2 — Wire copy import to decode + inspection replay frames (UI-only artifacts).

Optimization replay persistence (12C) lives in ``optimization_replay_persist`` so this module
stays free of shapez_asteroid optimization imports (see unit import guard test).
"""

from __future__ import annotations

import secrets
from typing import Any

from django.db import transaction

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.adapters.decode_adapter import (
    AsteroidLabCopyDecodeError,
    decode_copy_string,
)
from django_apps.asteroid_lab.adapters.normalization import normalize_decoded_blueprint
from django_apps.asteroid_lab.services.cell_snapshot_service import (
    build_decoded_blueprint_snapshot_from_input,
    persist_decoded_cell_snapshot,
    record_decoded_snapshot_frames,
)
from django_apps.asteroid_lab.services.dto import InitialReplayPipelineResultDTO
from django_apps.asteroid_lab.services.existing_layout_service import (
    build_existing_layout_inspection_from_input,
    persist_existing_layout_inspection_snapshot,
    record_existing_layout_inspection_frames,
)
from django_apps.asteroid_lab.services.experiment_service import create_solver_run
from django_apps.asteroid_lab.services.input_service import (
    content_sha256_for_copy_code,
    persist_decoded_snapshot_for_map_input,
)

# decode (1) + cleanup/reconstruction (4); see cell_snapshot_service / existing_layout_service.
_INSPECTION_EXPECTED_FRAMES = 5


def _default_run_key(map_input_id: int, digest_hex: str) -> str:
    base = f"inspection-{map_input_id}-{digest_hex[:12]}"
    return base[:120]


def _latest_cell_snapshot_pk(map_input_id: int, layer: str) -> int | None:
    row = (
        m.AsteroidCellSnapshot.objects.filter(map_input_id=int(map_input_id), layer=layer)
        .order_by("-id")
        .first()
    )
    return int(row.pk) if row else None


def _result_from_completed_track(
    inp: m.AsteroidMapInput,
    *,
    run_key: str,
    solver_run: m.SolverRun,
    track: m.ReplayTrack,
) -> InitialReplayPipelineResultDTO:
    n = int(track.frames.count())
    return InitialReplayPipelineResultDTO(
        project_id=int(inp.project_id),
        map_input_id=int(inp.pk),
        solver_run_id=int(solver_run.pk),
        replay_track_id=int(track.pk),
        replay_frame_count=n,
        decoded_snapshot_id=_latest_cell_snapshot_pk(inp.pk, "decoded_blueprint_top"),
        existing_layout_snapshot_id=_latest_cell_snapshot_pk(inp.pk, "existing_layout_inspection"),
        status="ok",
        error_message="",
        run_key=run_key,
    )


@transaction.atomic  # type: ignore[untyped-decorator]
def build_initial_replay_for_map_input(
    map_input_id: int,
    *,
    run_key: str | None = None,
    algorithm_label: str = "inspection_only",
    config: dict[str, Any] | None = None,
    force: bool = False,
) -> InitialReplayPipelineResultDTO:
    """Decode copy text, persist JSON, scaffold SolverRun/ReplayTrack, record inspection frames."""

    inp = m.AsteroidMapInput.objects.filter(pk=int(map_input_id)).select_related("project").first()
    if inp is None:
        return InitialReplayPipelineResultDTO(
            project_id=0,
            map_input_id=int(map_input_id),
            solver_run_id=None,
            replay_track_id=None,
            replay_frame_count=0,
            decoded_snapshot_id=None,
            existing_layout_snapshot_id=None,
            status="failed",
            error_message=f"AsteroidMapInput id={map_input_id} not found",
            run_key="",
        )

    digest = (inp.content_sha256 or "").strip() or content_sha256_for_copy_code(inp.copy_code)
    rk = (run_key or _default_run_key(int(inp.pk), digest)).strip() or _default_run_key(
        int(inp.pk), digest
    )
    if force:
        rk = f"{rk}-{secrets.token_hex(4)}"[:120]

    if not force:
        existing_run = m.SolverRun.objects.filter(
            project_id=inp.project_id,
            run_key=rk,
        ).first()
        if existing_run is not None:
            track = m.ReplayTrack.objects.filter(
                project_id=inp.project_id,
                track_key=rk,
            ).first()
            n = int(track.frames.count()) if track is not None else 0
            if n >= _INSPECTION_EXPECTED_FRAMES and track is not None:
                return _result_from_completed_track(
                    inp, run_key=rk, solver_run=existing_run, track=track
                )
            msg = (
                "Incomplete inspection replay; pass force=True to rebuild."
                if n > 0
                else "SolverRun exists without replay frames; pass force=True to rebuild."
            )
            return InitialReplayPipelineResultDTO(
                project_id=int(inp.project_id),
                map_input_id=int(inp.pk),
                solver_run_id=int(existing_run.pk),
                replay_track_id=int(track.pk) if track is not None else None,
                replay_frame_count=n,
                decoded_snapshot_id=_latest_cell_snapshot_pk(inp.pk, "decoded_blueprint_top"),
                existing_layout_snapshot_id=_latest_cell_snapshot_pk(
                    inp.pk, "existing_layout_inspection"
                ),
                status="failed",
                error_message=msg,
                run_key=rk,
            )

    try:
        raw = decode_copy_string(inp.copy_code)
        norm = normalize_decoded_blueprint(raw)
    except AsteroidLabCopyDecodeError as exc:
        return InitialReplayPipelineResultDTO(
            project_id=int(inp.project_id),
            map_input_id=int(inp.pk),
            solver_run_id=None,
            replay_track_id=None,
            replay_frame_count=0,
            decoded_snapshot_id=None,
            existing_layout_snapshot_id=None,
            status="failed",
            error_message=str(exc),
            run_key=rk,
        )

    persist_decoded_snapshot_for_map_input(int(inp.pk), norm)

    run_dto = create_solver_run(
        int(inp.project_id),
        run_key=rk,
        algorithm_label=algorithm_label,
        config=dict(config or {}),
    )
    track_id = int(run_dto.replay_track_id)

    snapshot = build_decoded_blueprint_snapshot_from_input(int(inp.pk))
    decoded_frames = record_decoded_snapshot_frames(track_id, snapshot)
    dec_snap_pk = persist_decoded_cell_snapshot(int(inp.project_id), int(inp.pk), snapshot)

    inspection = build_existing_layout_inspection_from_input(int(inp.pk))
    layout_frames = record_existing_layout_inspection_frames(track_id, inspection)
    layout_snap_pk = persist_existing_layout_inspection_snapshot(
        int(inp.project_id), int(inp.pk), inspection
    )

    total_frames = len(decoded_frames) + len(layout_frames)
    return InitialReplayPipelineResultDTO(
        project_id=int(inp.project_id),
        map_input_id=int(inp.pk),
        solver_run_id=int(run_dto.id),
        replay_track_id=track_id,
        replay_frame_count=total_frames,
        decoded_snapshot_id=int(dec_snap_pk),
        existing_layout_snapshot_id=int(layout_snap_pk),
        status="ok",
        error_message="",
        run_key=rk,
    )


__all__ = ["build_initial_replay_for_map_input"]
