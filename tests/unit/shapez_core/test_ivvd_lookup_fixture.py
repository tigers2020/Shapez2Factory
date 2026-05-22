"""Regression: shapez_core tests require IVVD lookup rows under xdist + --reuse-db."""

from __future__ import annotations

import pytest

from django_apps.shapez_core.models.ivvd_lookups import (
    ShapezIvvdLifecycleStatus,
    ShapezIvvdSeverity,
    ShapezIvvdValidationPhase,
)


@pytest.mark.django_db
def test_ivvd_lookup_rows_available_for_fk_targets() -> None:
    """Fails when parallel workers lose migration-seeded lookup tables."""
    assert ShapezIvvdSeverity.objects.filter(code="error").exists()
    assert ShapezIvvdValidationPhase.objects.filter(code="xref").exists()
    assert ShapezIvvdLifecycleStatus.objects.filter(code="imported").exists()
