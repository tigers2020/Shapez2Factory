"""Map input rows for Asteroid Lab (decode wiring stays out of solver packages)."""

from __future__ import annotations

import hashlib
from typing import Any

from django.db import transaction

from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string
from django_apps.asteroid_lab.adapters.normalization import normalize_decoded_blueprint
from django_apps.asteroid_lab.models import AsteroidMapInput, AsteroidProject
from django_apps.asteroid_lab.observability.boundary_jsonl import emit_boundary_jsonl
from django_apps.asteroid_lab.services.dto import NormalizedBlueprintDTO
from django_apps.asteroid_lab.snapshots.layout_fingerprint import (
    absolute_layout_fingerprint_sha256,
    layout_fingerprint_sha256,
)
from django_apps.asteroid_lab.snapshots.server_coords import attach_server_coords_to_decoded_json


def _count_entries_with_server_xy(decoded_json: dict[str, Any]) -> tuple[int, int]:
    """Return ``(dict_row_count, rows_with_int_server_xy_pair)`` for ``BP.Entries``."""

    bp = decoded_json.get("BP")
    if not isinstance(bp, dict):
        return (0, 0)
    entries_raw = bp.get("Entries")
    entries: list[Any] = entries_raw if isinstance(entries_raw, list) else []
    dict_rows = 0
    with_pair = 0
    for item in entries:
        if not isinstance(item, dict):
            continue
        dict_rows += 1
        sx, sy = item.get("server_x"), item.get("server_y")
        if isinstance(sx, int) and isinstance(sy, int):
            with_pair += 1
    return (dict_rows, with_pair)


def content_sha256_for_copy_code(copy_code: str) -> str:
    """SHA-256 of UTF-8 bytes (same rule as stored ``AsteroidMapInput.content_sha256``)."""

    return hashlib.sha256(copy_code.encode("utf-8")).hexdigest()


@transaction.atomic
def create_copy_code_map_input(
    project: AsteroidProject,
    copy_code: str,
    *,
    source_label: str = "",
) -> AsteroidMapInput:
    """Persist raw copy text and decoded ``decoded_json`` with server coords attached.

    This row is UI/persistence only — **not** an algorithm input surface for the solver core.
    Decode failure rolls back the row (no copy-only orphan).
    """

    digest = content_sha256_for_copy_code(copy_code)
    inp = AsteroidMapInput.objects.create(
        project=project,
        source_kind=AsteroidMapInput.SourceKind.COPY_CODE,
        copy_code=copy_code,
        decoded_json={},
        content_sha256=digest,
    )
    normalized = copy_code.strip().removesuffix("$")
    raw = decode_copy_string(normalized)
    dto = normalize_decoded_blueprint(raw)
    return persist_decoded_snapshot_for_map_input(int(inp.pk), dto)


@transaction.atomic
def refresh_map_input_from_copy_code(
    map_input_id: int,
    copy_code: str,
) -> AsteroidMapInput:
    """Overwrite ``copy_code`` and ``decoded_json`` on an existing ``AsteroidMapInput`` row."""

    inp = AsteroidMapInput.objects.select_for_update().filter(pk=int(map_input_id)).first()
    if inp is None:
        msg = f"AsteroidMapInput id={map_input_id} not found"
        raise ValueError(msg)
    normalized = copy_code.strip().removesuffix("$")
    inp.copy_code = copy_code
    inp.content_sha256 = content_sha256_for_copy_code(copy_code)
    inp.save(update_fields=["copy_code", "content_sha256", "updated_at"])
    raw = decode_copy_string(normalized)
    dto = normalize_decoded_blueprint(raw)
    return persist_decoded_snapshot_for_map_input(int(inp.pk), dto)


@transaction.atomic
def upsert_map_input_for_project(
    project: AsteroidProject,
    copy_code: str,
    *,
    source_label: str = "",
) -> tuple[AsteroidMapInput, bool]:
    """Create or overwrite the map input row for this copy digest (``created`` flag)."""

    digest = content_sha256_for_copy_code(copy_code)
    existing = (
        AsteroidMapInput.objects.filter(project_id=int(project.pk), content_sha256=digest)
        .order_by("-updated_at")
        .first()
    )
    if existing is not None:
        return refresh_map_input_from_copy_code(int(existing.pk), copy_code), False
    return create_copy_code_map_input(project, copy_code, source_label=source_label), True


@transaction.atomic
def persist_decoded_snapshot_for_map_input(
    map_input_id: int,
    dto: NormalizedBlueprintDTO,
) -> AsteroidMapInput:
    """Write ``decoded_json`` (+ ``source_kind``) for a specific ``AsteroidMapInput`` row."""

    inp = AsteroidMapInput.objects.select_for_update().filter(pk=int(map_input_id)).first()
    if inp is None:
        msg = f"AsteroidMapInput id={map_input_id} not found"
        raise ValueError(msg)
    attach_server_coords_to_decoded_json(dto.decoded_json)
    rid = f"map_input:{int(inp.pk)}"
    drows, with_xy = _count_entries_with_server_xy(dto.decoded_json)
    meta = dto.decoded_json.get("_asteroid_lab_coord_system")
    emit_boundary_jsonl(
        run_id=rid,
        stage="decode",
        boundary="decode.server_coords_attach",
        data={
            "map_input_id": int(inp.pk),
            "project_id": int(inp.project_id),
            "bp_dict_entry_rows": drows,
            "bp_entries_with_server_xy": with_xy,
            "missing_server_xy": drows - with_xy,
            "coord_meta": meta if isinstance(meta, dict) else {},
        },
    )
    layout_fp = layout_fingerprint_sha256(dto.decoded_json)
    abs_fp = absolute_layout_fingerprint_sha256(dto.decoded_json)
    inp.decoded_json = dto.decoded_json
    inp.source_kind = AsteroidMapInput.SourceKind.DECODED_JSON
    inp.layout_fingerprint = layout_fp
    inp.absolute_layout_fingerprint = abs_fp
    inp.save(
        update_fields=[
            "decoded_json",
            "source_kind",
            "layout_fingerprint",
            "absolute_layout_fingerprint",
            "updated_at",
        ]
    )
    return inp


@transaction.atomic
def persist_decoded_snapshot(project_id: int, dto: NormalizedBlueprintDTO) -> AsteroidMapInput:
    """Write ``decoded_json`` (+ ``source_kind``) for the newest ``AsteroidMapInput`` on a project.

    Uses existing columns only; summary lives under ``decoded_json['_asteroid_lab_summary']``.
    """

    inp = (
        AsteroidMapInput.objects.filter(project_id=project_id)
        .select_for_update()
        .order_by("-created_at")
        .first()
    )
    if inp is None:
        msg = f"no AsteroidMapInput rows for project_id={project_id}"
        raise ValueError(msg)
    inp.decoded_json = dto.decoded_json
    inp.source_kind = AsteroidMapInput.SourceKind.DECODED_JSON
    attach_server_coords_to_decoded_json(inp.decoded_json)
    rid = f"map_input:{int(inp.pk)}"
    drows, with_xy = _count_entries_with_server_xy(inp.decoded_json)
    meta = inp.decoded_json.get("_asteroid_lab_coord_system")
    emit_boundary_jsonl(
        run_id=rid,
        stage="decode",
        boundary="decode.server_coords_attach",
        data={
            "map_input_id": int(inp.pk),
            "project_id": int(project_id),
            "bp_dict_entry_rows": drows,
            "bp_entries_with_server_xy": with_xy,
            "missing_server_xy": drows - with_xy,
            "coord_meta": meta if isinstance(meta, dict) else {},
        },
    )
    inp.layout_fingerprint = layout_fingerprint_sha256(inp.decoded_json)
    inp.absolute_layout_fingerprint = absolute_layout_fingerprint_sha256(inp.decoded_json)
    inp.save(
        update_fields=[
            "decoded_json",
            "source_kind",
            "layout_fingerprint",
            "absolute_layout_fingerprint",
            "updated_at",
        ]
    )
    return inp
