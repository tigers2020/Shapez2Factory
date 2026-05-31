"""Persist and load topology-reconstructed asteroid maps (ORM + blueprint adapter)."""

from __future__ import annotations

from typing import Any

from django.db import transaction

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.adapters.reconstruction_blueprint_export import (
    load_reconstruction_cells_from_copy_code,
    load_reconstruction_cells_from_decoded_json,
)
from django_apps.asteroid_lab.cleanup.result import CleanupResult
from django_apps.asteroid_lab.observability.boundary_jsonl import DJANGO_BOUNDARY_SINK
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.reconstruction.trace import ReconstructionTraceCollector
from django_apps.asteroid_lab.replay.deconstruction_frames import load_cleanup_result
from django_apps.asteroid_lab.services.cell_snapshot_service import (
    build_decoded_blueprint_snapshot_from_input,
)
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.services.reconstructed_map_persist_builder import (
    build_reconstructed_map_persist_payload,
)
from django_apps.asteroid_lab.services.reconstructed_map_thumbnail_service import (
    sync_admin_list_thumbnail,
)


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
        boundary_sink=DJANGO_BOUNDARY_SINK,
    )
    return cleanup, recon


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

    del cleanup_summary  # unused; full_map persist does not store summary_json

    inp = m.AsteroidMapInput.objects.filter(pk=int(map_input_id)).select_related("project").first()
    if inp is None:
        msg = f"AsteroidMapInput id={map_input_id} not found"
        raise ValueError(msg)

    if cleanup is None:
        msg = "persist_reconstructed_asteroid_map requires cleanup for full_map merge"
        raise ValueError(msg)

    source_decoded = dict(inp.decoded_json) if inp.decoded_json else None

    payload = build_reconstructed_map_persist_payload(
        map_input_id=int(inp.pk),
        run_key=run_key.strip(),
        recon=recon,
        cleanup=cleanup,
        original_copy_code=(inp.copy_code or "").strip(),
        original_decoded_json=source_decoded,
        source_decoded_json=source_decoded,
    )

    row, created = m.ReconstructedAsteroidMap.objects.update_or_create(
        map_input_id=int(inp.pk),
        run_key=run_key.strip(),
        defaults={
            "project_id": int(inp.project_id),
            "solver_run_id": int(solver_run_id) if solver_run_id is not None else None,
            "original_copy_code": payload.original_copy_code,
            "original_decoded_json": payload.original_decoded_json,
            "copy_code": payload.copy_code,
            "decoded_json": payload.decoded_json,
        },
    )
    if not created:
        row.save(
            update_fields=[
                "project_id",
                "solver_run_id",
                "original_copy_code",
                "original_decoded_json",
                "copy_code",
                "decoded_json",
                "updated_at",
            ]
        )

    row = m.ReconstructedAsteroidMap.objects.get(pk=int(row.pk))
    sync_admin_list_thumbnail(row)
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
        solver_run_id=solver_run_id,
    )
    return int(pk)


def load_reconstructed_asteroid_cells(
    *,
    pk: int | None = None,
    map_input_id: int | None = None,
    run_key: str | None = None,
) -> tuple[DecodedCellDTO, ...]:
    """Load cells from ORM row via reconstruction import (full_map ``decoded_json``)."""

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
    code = (row.copy_code or "").strip()
    return load_reconstruction_cells_from_copy_code(code)


__all__ = [
    "load_reconstructed_asteroid_cells",
    "persist_reconstructed_asteroid_map",
    "refresh_reconstructed_map_for_map_input",
    "run_reconstruction_for_map_input",
]
