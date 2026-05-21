"""Import layer uses existing models — no parallel GameData* tables."""

from __future__ import annotations

import pytest
from django.apps import apps

from django_apps.game_data.import_layer import (
    CANONICAL_IMPORT_MODELS,
    REJECTED_PARALLEL_MODELS,
    model_for_canonical,
)


@pytest.mark.django_db
@pytest.mark.parametrize("canonical,class_name", list(CANONICAL_IMPORT_MODELS.items()))
def test_canonical_maps_to_existing_model(canonical: str, class_name: str) -> None:
    model = model_for_canonical(canonical)
    assert model.__name__ == class_name


@pytest.mark.django_db
def test_rejected_parallel_models_not_registered() -> None:
    app = apps.get_app_config("game_data")
    registered = {m.__name__ for m in app.get_models()}
    assert registered.isdisjoint(REJECTED_PARALLEL_MODELS)


@pytest.mark.django_db
def test_import_batch_docstring_documents_canonical_name() -> None:
    ImportBatch = model_for_canonical("game_data_import_batch")
    assert ImportBatch.__name__ == "ImportBatch"
    assert ImportBatch._meta.verbose_name == "import run"
    assert "game_data_import_batch" in (ImportBatch.__doc__ or "")
