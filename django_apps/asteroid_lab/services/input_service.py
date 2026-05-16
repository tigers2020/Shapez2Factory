"""Map input rows for Asteroid Lab (decode wiring stays out of solver packages)."""

from __future__ import annotations

import hashlib

from django.db import transaction

from django_apps.asteroid_lab.models import AsteroidMapInput, AsteroidProject
from django_apps.asteroid_lab.services.dto import NormalizedBlueprintDTO


def create_copy_code_map_input(
    project: AsteroidProject,
    copy_code: str,
    *,
    source_label: str = "",
) -> AsteroidMapInput:
    """Persist raw copy text and empty ``decoded_json`` until decode is wired elsewhere.

    This row is UI/persistence only — **not** an algorithm input surface for the solver core.
    """

    digest = hashlib.sha256(copy_code.encode("utf-8")).hexdigest()
    return AsteroidMapInput.objects.create(
        project=project,
        source_kind=AsteroidMapInput.SourceKind.COPY_CODE,
        copy_code=copy_code,
        decoded_json={},
        content_sha256=digest,
    )


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
    inp.save(update_fields=["decoded_json", "source_kind"])
    return inp
