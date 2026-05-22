"""Shared fixtures for ``tests/unit/shapez_core``."""

from __future__ import annotations

import pytest

from django_apps.shapez_core.models.ivvd_lookups import (
    ShapezIvvdArtifactType,
    ShapezIvvdDocumentKind,
    ShapezIvvdLifecycleStatus,
    ShapezIvvdSeverity,
    ShapezIvvdValidationPhase,
)


def _ensure_ivvd_lookups() -> None:
    """Idempotent seed matching migration ``0002_ivvd_lookups_and_fks``."""
    for code, label, so in (
        ("error", "Error", 0),
        ("warning", "Warning", 1),
    ):
        ShapezIvvdSeverity.objects.update_or_create(
            code=code, defaults={"label": label, "sort_order": so}
        )

    for so, code in enumerate(("schema", "xref", "semantic")):
        ShapezIvvdValidationPhase.objects.update_or_create(
            code=code, defaults={"label": code, "sort_order": so}
        )

    for so, (code, label) in enumerate(
        (
            ("imported", "Imported"),
            ("schema_checked", "Schema checked"),
            ("xref_checked", "Cross-ref checked"),
            ("semantic_checked", "Semantic checked"),
            ("sealed", "Sealed"),
            ("failed", "Failed"),
        )
    ):
        ShapezIvvdLifecycleStatus.objects.update_or_create(
            code=code, defaults={"label": label, "sort_order": so}
        )

    kinds = (
        ("identifiers", "identifiers.json"),
        ("buildings", "buildings.json"),
        ("translations", "translations"),
        ("scenario", "scenario"),
        ("difficulty_preset", "difficulty preset"),
        ("scenario_parameter_preset", "scenario parameter preset"),
        ("json_schema", "json schema"),
        ("version", "version file"),
        ("other", "other"),
    )
    for so, (code, label) in enumerate(kinds):
        ShapezIvvdDocumentKind.objects.update_or_create(
            code=code, defaults={"label": label, "sort_order": so}
        )

    ShapezIvvdArtifactType.objects.update_or_create(
        code="ivvd_import_bundle",
        defaults={"label": "IVVD import bundle", "sort_order": 0},
    )


@pytest.fixture(autouse=True)
def ivvd_lookup_rows(db: None) -> None:
    _ensure_ivvd_lookups()
