"""Map input rows for Asteroid Lab (decode wiring stays out of solver packages)."""

from __future__ import annotations

import hashlib

from django.db import transaction

from django_apps.asteroid_lab.models import AsteroidMapInput, AsteroidProject
from django_apps.asteroid_lab.services.dto import NormalizedBlueprintDTO
from django_apps.asteroid_lab.snapshots.layout_fingerprint import (
    absolute_layout_fingerprint_sha256,
    layout_fingerprint_sha256,
)
from django_apps.asteroid_lab.snapshots.server_coords import attach_server_coords_to_decoded_json


def content_sha256_for_copy_code(copy_code: str) -> str:
    """SHA-256 of UTF-8 bytes (same rule as stored ``AsteroidMapInput.content_sha256``)."""

    return hashlib.sha256(copy_code.encode("utf-8")).hexdigest()


def create_copy_code_map_input(
    project: AsteroidProject,
    copy_code: str,
    *,
    source_label: str = "",
) -> AsteroidMapInput:
    """Persist raw copy text and empty ``decoded_json`` until decode is wired elsewhere.

    This row is UI/persistence only — **not** an algorithm input surface for the solver core.
    """

    digest = content_sha256_for_copy_code(copy_code)
    return AsteroidMapInput.objects.create(
        project=project,
        source_kind=AsteroidMapInput.SourceKind.COPY_CODE,
        copy_code=copy_code,
        decoded_json={},
        content_sha256=digest,
    )


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
    inp.layout_fingerprint = layout_fingerprint_sha256(inp.decoded_json)
    inp.absolute_layout_fingerprint = absolute_layout_fingerprint_sha256(inp.decoded_json)
    inp.save(
        update_fields=[
            "decoded_json",
            "source_kind",
            "layout_fingerprint",
            "absolute_layout_fingerprint",
        ]
    )
    return inp
