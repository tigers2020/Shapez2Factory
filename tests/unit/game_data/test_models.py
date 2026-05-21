"""ORM contracts for game_data app."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from django.db import IntegrityError

from django_apps.game_data.models import (
    FluidColor,
    ImportBatch,
    ShapeRecipe,
)
from django_apps.game_data.services.identifiers import (
    InvalidCanonicalIdError,
    canonical_fluid_color,
    reject_runtime_canonical,
)


@pytest.mark.django_db
def test_import_batch_unique_manifest_hash() -> None:
    ImportBatch.objects.create(
        batch_name="t",
        manifest_self_hash="sha256:abc",
        game_version="v",
        unity_version="u",
        dump_mod_version="1",
        dump_schema_version="1",
        dump_timestamp_utc=datetime(2026, 5, 20, 12, 0, 0, tzinfo=UTC),
        source_method="test",
    )
    with pytest.raises(IntegrityError):
        ImportBatch.objects.create(
            batch_name="t2",
            manifest_self_hash="sha256:abc",
            game_version="v",
            unity_version="u",
            dump_mod_version="1",
            dump_schema_version="1",
            dump_timestamp_utc=datetime(2026, 5, 20, 12, 0, 0, tzinfo=UTC),
            source_method="test",
        )


def test_reject_runtime_canonical_id() -> None:
    with pytest.raises(InvalidCanonicalIdError):
        reject_runtime_canonical("AtomicStatefulIslandSimulationSystem`2[[Game.Content")


def test_canonical_fluid_id_deterministic() -> None:
    assert canonical_fluid_color("Red") == canonical_fluid_color("Red")


@pytest.mark.django_db
def test_shape_recipe_canonical_unique() -> None:
    batch = ImportBatch.objects.create(
        batch_name="b",
        manifest_self_hash="sha256:shape1",
        game_version="v",
        unity_version="u",
        dump_mod_version="1",
        dump_schema_version="1",
        dump_timestamp_utc=datetime(2026, 5, 20, 12, 0, 0, tzinfo=UTC),
        source_method="test",
    )
    ShapeRecipe.objects.create(
        canonical_id="shape:1:AbAbAbAb",
        import_batch=batch,
        operation_uid=1,
        shape_hash="AbAbAbAb",
        quadrant_count=4,
        layer_count=1,
    )
    assert ShapeRecipe.objects.count() == 1
    FluidColor.objects.create(
        canonical_id="fluid:Red",
        import_batch=batch,
        color_name="Red",
        source_row_index=0,
    )
