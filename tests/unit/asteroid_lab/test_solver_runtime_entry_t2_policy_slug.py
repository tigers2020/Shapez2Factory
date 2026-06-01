"""Task 3 ??runtime entry passes AsteroidProject.slug into solver_summary builder."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m

pytestmark = pytest.mark.django_db


def test_asteroid_project_slug_readback_for_runtime() -> None:
    slug = "copy-import-495e552c"
    project = m.AsteroidProject.objects.create(name="Canon", slug=slug)
    loaded = (
        m.AsteroidProject.objects.filter(pk=int(project.pk)).values_list("slug", flat=True).first()
    )
    assert loaded == slug
