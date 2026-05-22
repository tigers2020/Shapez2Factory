"""Management command: seed_game_data_taxonomy after flush/import."""

from __future__ import annotations

import pytest
from django.core.management import call_command

from django_apps.game_data.models.taxonomy import GameDataNamespace, GameDataSection
from django_apps.game_data.services.taxonomy_seed import SUBTABLE_MODEL_LABELS

_SHAPE_RECIPE_APPEARANCE_LABEL = "game_data.ShapeRecipeSourceAppearance"


@pytest.mark.django_db
def test_seed_game_data_taxonomy_populates_namespaces_after_empty() -> None:
    GameDataNamespace.objects.all().delete()
    GameDataSection.objects.all().delete()
    assert not GameDataNamespace.objects.exists()

    call_command("seed_game_data_taxonomy")

    assert GameDataNamespace.objects.exists()
    assert GameDataSection.objects.exists()
    assert not GameDataSection.objects.filter(
        django_model_label__in=SUBTABLE_MODEL_LABELS,
    ).exists()
    assert not GameDataSection.objects.filter(
        django_model_label=_SHAPE_RECIPE_APPEARANCE_LABEL,
    ).exists()


@pytest.mark.django_db
def test_seed_game_data_taxonomy_idempotent() -> None:
    GameDataNamespace.objects.all().delete()
    GameDataSection.objects.all().delete()

    call_command("seed_game_data_taxonomy")
    ns_count = GameDataNamespace.objects.count()
    section_count = GameDataSection.objects.count()
    assert ns_count > 0
    assert section_count > 0

    call_command("seed_game_data_taxonomy")

    assert GameDataNamespace.objects.count() == ns_count
    assert GameDataSection.objects.count() == section_count
    assert not GameDataSection.objects.filter(
        django_model_label=_SHAPE_RECIPE_APPEARANCE_LABEL,
    ).exists()
