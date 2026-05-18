"""Persist and load topology-reconstructed asteroid maps (ORM + blueprint adapter)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from django.db import transaction

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.adapters.reconstruction_blueprint_export import (
    load_reconstruction_cells_from_copy_code,
    load_reconstruction_cells_from_decoded_json,
)
from django_apps.asteroid_lab.cleanup.result import CleanupResult
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.reconstruction.trace import ReconstructionTraceCollector
from django_apps.asteroid_lab.replay.deconstruction_frames import load_cleanup_result
from django_apps.asteroid_lab.services.cell_snapshot_service import (
    build_decoded_blueprint_snapshot_from_input,
)
from django_apps.asteroid_lab.services.dto import DecodedCellDTO, NormalizedBlueprintDTO
from django_apps.asteroid_lab.services.reconstructed_map_persist_builder import (
    build_reconstructed_map_persist_payload,
)
from django_apps.asteroid_lab.snapshots.layout_fingerprint import layout_fingerprint_sha256


def run_reconstruction_for_map_input(
    map_input_id: int,
    *,
    boundary_run_id: str | None = None,
    trace_collector: ReconstructionTraceCollector | None = None,
) -> tuple[CleanupResult, ReconstructionResult]:
    """Run cleanup + topology reconstruction for one ``AsteroidMapInput``."""

    mid = int(map_input_id)
    rid = boundary_run_id if boundary_run_id is not None else f"map_input:{mid}"
    snap = build_decoded_blueprint_snapshot_from_input(mid, boundary_run_id=rid)
    cleanup = load_cleanup_result(snap, boundary_run_id=rid)
    collector = trace_collector if trace_collector is not None else ReconstructionTraceCollector()
    recon = run_topology_reconstruction(
        cleanup,
        trace_collector=collector,
        boundary_run_id=rid,
        boundary_map_input_id=snap.map_input_id,
        boundary_project_id=snap.project_id,
    )
    return cleanup, recon


def build_reconstructed_blueprint_dto(
    recon: ReconstructionResult,
    *,
    source_decoded_json: dict[str, Any] | None,
    map_input_id: int | None,
    run_key: str,
    summary_json: dict[str, Any] | None = None,
) -> NormalizedBlueprintDTO:
    """Encode reconstruction cells to normalized blueprint JSON."""

    from django_apps.asteroid_lab.adapters.reconstruction_blueprint_export import (
        build_reconstructed_normalized_dto,
    )

    return build_reconstructed_normalized_dto(
        recon.cells,
        source_decoded_json=source_decoded_json,
        map_input_id=map_input_id,
        run_key=run_key,
        summary_json=summary_json,
    )


@transaction.atomic  # type: ignore[untyped-decorator]
def persist_reconstructed_asteroid_map(
    *,
    map_input_id: int,
    run_key: str,
    recon: ReconstructionResult,
    cleanup: CleanupResult | None = None,
    cleanup_summary: dict[str, Any] | None = None,
    solver_run_id: int | None = None,
) -> int:
    """Write or update ``ReconstructedAsteroidMap`` for ``(map_input, run_key)``."""

    inp = m.AsteroidMapInput.objects.filter(pk=int(map_input_id)).select_related("project").first()
    if inp is None:
        msg = f"AsteroidMapInput id={map_input_id} not found"
        raise ValueError(msg)

    source_decoded = dict(inp.decoded_json) if inp.decoded_json else None
    merged_summary = {**(cleanup_summary or {}), **dict(recon.summary_json)}
    fp = layout_fingerprint_sha256(
        build_reconstructed_blueprint_dto(
            recon,
            source_decoded_json=source_decoded,
            map_input_id=int(inp.pk),
            run_key=run_key.strip(),
            summary_json=merged_summary,
        ).decoded_json
    )

    payload = build_reconstructed_map_persist_payload(
        map_input_id=int(inp.pk),
        run_key=run_key.strip(),
        recon=recon,
        cleanup=cleanup,
        cleanup_summary=cleanup_summary,
        source_decoded_json=source_decoded,
        layout_fingerprint=fp,
    )

    merged_summary = {
        **payload.summary_json,
        "persisted_at": datetime.now(UTC).isoformat(),
    }
    row, created = m.ReconstructedAsteroidMap.objects.update_or_create(
        map_input_id=int(inp.pk),
        run_key=run_key.strip(),
        defaults={
            "project_id": int(inp.project_id),
            "solver_run_id": int(solver_run_id) if solver_run_id is not None else None,
            "copy_code": payload.rebuilt_copy_code,
            "original_copy_code": (inp.copy_code or "").strip(),
            "rebuilt_copy_code": payload.rebuilt_copy_code,
            "decoded_json": payload.decoded_json_lab,
            "export_json": payload.export_json,
            "reconstruction_json": payload.reconstruction_json,
            "summary_json": merged_summary,
            "cell_count": payload.cell_count,
            "layout_fingerprint": fp,
            "anchor_raw_x": payload.anchor_raw_x,
            "anchor_raw_y": payload.anchor_raw_y,
            "anchor_server_x": payload.anchor_server_x,
            "anchor_server_y": payload.anchor_server_y,
            "coord_system": payload.coord_system,
        },
    )
    if not created:
        row.save(
            update_fields=[
                "project_id",
                "solver_run_id",
                "copy_code",
                "original_copy_code",
                "rebuilt_copy_code",
                "decoded_json",
                "export_json",
                "reconstruction_json",
                "summary_json",
                "cell_count",
                "layout_fingerprint",
                "anchor_raw_x",
                "anchor_raw_y",
                "anchor_server_x",
                "anchor_server_y",
                "coord_system",
                "updated_at",
            ]
        )

    m.ReconstructedAsteroidEntry.objects.filter(map_id=int(row.pk)).delete()
    if payload.entry_instances:
        to_create = []
        for ent in payload.entry_instances:
            ent.map_id = int(row.pk)
            to_create.append(ent)
        m.ReconstructedAsteroidEntry.objects.bulk_create(to_create)

    return int(row.pk)


@transaction.atomic  # type: ignore[untyped-decorator]
def refresh_reconstructed_map_for_map_input(
    map_input_id: int,
    *,
    run_key: str,
    solver_run_id: int | None = None,
    boundary_run_id: str | None = None,
) -> int:
    """Re-run reconstruction and overwrite the persisted map row for ``run_key``."""

    rid = boundary_run_id if boundary_run_id is not None else f"map_input:{int(map_input_id)}"
    cleanup, recon = run_reconstruction_for_map_input(
        int(map_input_id),
        boundary_run_id=rid,
    )
    pk = persist_reconstructed_asteroid_map(
        map_input_id=int(map_input_id),
        run_key=run_key.strip(),
        recon=recon,
        cleanup=cleanup,
        cleanup_summary=dict(cleanup.summary_json),
        solver_run_id=solver_run_id,
    )
    return int(pk)


def load_reconstructed_asteroid_cells(
    *,
    pk: int | None = None,
    map_input_id: int | None = None,
    run_key: str | None = None,
) -> tuple[DecodedCellDTO, ...]:
    """Load cells from ORM row via reconstruction import (Extension → field kinds)."""

    qs = m.ReconstructedAsteroidMap.objects.all()
    if pk is not None:
        row = qs.filter(pk=int(pk)).first()
    elif map_input_id is not None:
        q = qs.filter(map_input_id=int(map_input_id)).order_by("-updated_at")
        if run_key:
            q = q.filter(run_key=run_key.strip())
        row = q.first()
    else:
        msg = "load_reconstructed_asteroid_cells requires pk or map_input_id"
        raise ValueError(msg)

    if row is None:
        msg = "ReconstructedAsteroidMap not found"
        raise ValueError(msg)

    if row.decoded_json:
        return load_reconstruction_cells_from_decoded_json(dict(row.decoded_json))
    code = (row.rebuilt_copy_code or row.copy_code or "").strip()
    return load_reconstruction_cells_from_copy_code(code)


__all__ = [
    "build_reconstructed_blueprint_dto",
    "load_reconstructed_asteroid_cells",
    "persist_reconstructed_asteroid_map",
    "refresh_reconstructed_map_for_map_input",
    "run_reconstruction_for_map_input",
]
