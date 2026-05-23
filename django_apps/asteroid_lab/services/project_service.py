"""Project lifecycle for Asteroid Lab."""

from __future__ import annotations

import secrets

from django.db import transaction
from django.utils.text import slugify

from django_apps.asteroid_lab.models import AsteroidMapInput, AsteroidProject
from django_apps.asteroid_lab.services.dto import CreateProjectFromCopyCodeResultDTO
from django_apps.asteroid_lab.services.input_service import (
    content_sha256_for_copy_code,
    upsert_map_input_for_project,
)


def _unique_slug_from_label(label: str) -> str:
    base = slugify(label)[:72] or "import"
    for _ in range(32):
        candidate = f"{base}-{secrets.token_hex(4)}"
        if not AsteroidProject.objects.filter(slug=candidate).exists():
            return candidate
    return f"{base}-{secrets.token_hex(8)}"


@transaction.atomic
def create_project_from_copy_code(
    copy_code: str,
    *,
    source_label: str = "",
) -> CreateProjectFromCopyCodeResultDTO:
    """Create ``AsteroidProject`` + ``AsteroidMapInput`` with decoded snapshot.

    :func:`create_copy_code_map_input` decodes copy text with island-local coords.
    Does **not** import asteroid mining v1/v2 solver internals.

    Persisted rows are for UI/cache/inspection — **not** solver algorithm input.
    """

    label = (source_label or "").strip()
    name = label if label else "Copy import"
    slug = _unique_slug_from_label(label or "copy-import")
    project = AsteroidProject.objects.create(name=name[:200], slug=slug)
    inp, _created = upsert_map_input_for_project(project, copy_code, source_label=source_label)
    return CreateProjectFromCopyCodeResultDTO(
        project_id=project.id,
        slug=project.slug,
        name=project.name,
        map_input_id=inp.id,
        copy_code_sha256=inp.content_sha256,
        source_label=source_label,
    )


def resolve_or_create_project_slug_for_copy_code(
    copy_code: str,
    *,
    source_label: str = "",
) -> str:
    """Return ``AsteroidProject.slug`` for this copy text, reusing a row with matching digest."""

    normalized = copy_code.strip()
    if not normalized:
        msg = "copy code is empty"
        raise ValueError(msg)

    digest = content_sha256_for_copy_code(normalized)
    existing = (
        AsteroidMapInput.objects.filter(content_sha256=digest)
        .select_related("project")
        .order_by("-created_at")
        .first()
    )
    if existing is not None:
        return str(existing.project.slug)

    dto = create_project_from_copy_code(normalized, source_label=source_label)
    return str(dto.slug)
