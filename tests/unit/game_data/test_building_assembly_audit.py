"""Building Assembly paths classified as reflection metadata."""

from __future__ import annotations

import pytest

from django_apps.game_data.coverage.reason_codes import REFLECTION_METADATA
from django_apps.game_data.models import ImportBatch, UnknownProperty


@pytest.mark.django_db
def test_building_assembly_classified_as_reflection(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    batch = imported_game_data_batch_module
    qs = UnknownProperty.objects.filter(
        import_batch=batch,
        reason_code=REFLECTION_METADATA,
        classification="assembly_reflection",
        owner_model="building_group",
    )
    assert qs.exists()
    assert qs.filter(json_path__contains="Assembly").exists()
