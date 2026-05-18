"""Persist and load topology-reconstructed asteroid maps (ORM + blueprint adapter)."""

from __future__ import annotations

from typing import Any

from django.db import transaction

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.adapters.reconstruction_blueprint_export import (
    build_reconstructed_normalized_dto,
    encode_reconstructed_copy_string,
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
    cleanup_summary: dict[str, Any] | None = None,
    solver_run_id: int | None = None,
) -> int:
    """Write or update ``ReconstructedAsteroidMap`` for ``(map_input, run_key)``."""

    inp = m.AsteroidMapInput.objects.filter(pk=int(map_input_id)).select_related("project").first()
    if inp is None:
        msg = f"AsteroidMapInput id={map_input_id} not found"
        raise ValueError(msg)

    merged_summary = {**(cleanup_summary or {}), **dict(recon.summary_json)}
    norm = build_reconstructed_blueprint_dto(
        recon,
        source_decoded_json=dict(inp.decoded_json) if inp.decoded_json else None,
        map_input_id=int(inp.pk),
        run_key=run_key.strip(),
        summary_json=merged_summary,
    )
    root = norm.decoded_json
    copy_code = encode_reconstructed_copy_string(root)
    bp = root.get("BP")
    entries = bp.get("Entries") if isinstance(bp, dict) else []
    entry_count = len(entries) if isinstance(entries, list) else len(recon.cells)
    fp = layout_fingerprint_sha256(root)

    row, _created = m.ReconstructedAsteroidMap.objects.update_or_create(
        map_input_id=int(inp.pk),
        run_key=run_key.strip(),
        defaults={
            "project_id": int(inp.project_id),
            "solver_run_id": int(solver_run_id) if solver_run_id is not None else None,
            "copy_code": copy_code,
            "decoded_json": root,
            "summary_json": merged_summary,
            "cell_count": entry_count,
            "layout_fingerprint": fp,
        },
    )
    return int(row.pk)


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
        q = qs.filter(map_input_id=int(map_input_id)).order_by("-created_at")
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
    return load_reconstruction_cells_from_copy_code(row.copy_code)


__all__ = [
    "build_reconstructed_blueprint_dto",
    "load_reconstructed_asteroid_cells",
    "persist_reconstructed_asteroid_map",
    "run_reconstruction_for_map_input",
]
