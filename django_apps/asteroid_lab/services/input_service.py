"""Map input rows for Asteroid Lab (decode wiring stays out of solver packages)."""

from __future__ import annotations

import hashlib

from django_apps.asteroid_lab.models import AsteroidMapInput, AsteroidProject


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
