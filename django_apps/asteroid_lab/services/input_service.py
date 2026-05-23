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
from django_apps.asteroid_lab.snapshots.island_coord_meta import (
    attach_island_coord_meta_to_decoded_json,
)
from django_apps.asteroid_lab.snapshots.layout_fingerprint import (
    absolute_layout_fingerprint_sha256,
    layout_fingerprint_sha256,
)


def _count_bp_dict_entries(decoded_json: dict[str, Any]) -> int:
    bp = decoded_json.get("BP")
    if not isinstance(bp, dict):
        return 0
    entries_raw = bp.get("Entries")
    entries: list[Any] = entries_raw if isinstance(entries_raw, list) else []
    return sum(1 for item in entries if isinstance(item, dict))


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
    """Persist raw copy text and decoded ``decoded_json`` with island coord metadata.

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
    attach_island_coord_meta_to_decoded_json(dto.decoded_json)
    rid = f"map_input:{int(inp.pk)}"
    drows = _count_bp_dict_entries(dto.decoded_json)
    meta = dto.decoded_json.get("_asteroid_lab_coord_system")
    emit_boundary_jsonl(
        run_id=rid,
        stage="decode",
        boundary="decode.island_coord_meta_attach",
        data={
            "map_input_id": int(inp.pk),
            "project_id": int(inp.project_id),
            "bp_dict_entry_rows": drows,
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
    attach_island_coord_meta_to_decoded_json(inp.decoded_json)
    rid = f"map_input:{int(inp.pk)}"
    drows = _count_bp_dict_entries(inp.decoded_json)
    meta = inp.decoded_json.get("_asteroid_lab_coord_system")
    emit_boundary_jsonl(
        run_id=rid,
        stage="decode",
        boundary="decode.island_coord_meta_attach",
        data={
            "map_input_id": int(inp.pk),
            "project_id": int(project_id),
            "bp_dict_entry_rows": drows,
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
