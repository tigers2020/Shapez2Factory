"""Domain models must not use forbidden JSONField storage."""

from __future__ import annotations

import pytest
from django.apps import apps
from django.db import models

FORBIDDEN_JSON_NAMES = frozenset({"raw_json", "payload", "data", "source_dump"})
ALLOWED_JSON_MODELS: frozenset[str] = frozenset()


@pytest.mark.parametrize("model", list(apps.get_app_config("game_data").get_models()))
def test_domain_models_avoid_jsonfield(model: type[models.Model]) -> None:
    if model.__name__ in ALLOWED_JSON_MODELS:
        return
    for field in model._meta.fields:
        if isinstance(field, models.JSONField):
            assert model.__name__ in ALLOWED_JSON_MODELS, (
                f"{model.__name__}.{field.name} must not use JSONField"
            )
        if field.name in FORBIDDEN_JSON_NAMES:
            pytest.fail(f"{model.__name__}.{field.name} is forbidden")
