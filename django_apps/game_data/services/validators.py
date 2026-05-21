"""Post-import invariant checks."""

from __future__ import annotations

from django.apps import apps
from django.db import models

FORBIDDEN_JSON_FIELD_NAMES = frozenset({"raw_json", "payload", "data", "source_dump"})

ALLOWED_JSON_MODELS: frozenset[str] = frozenset()


def assert_no_domain_json_fields() -> None:
    for model in apps.get_app_config("game_data").get_models():
        if model.__name__ in ALLOWED_JSON_MODELS:
            continue
        for field in model._meta.fields:
            if isinstance(field, models.JSONField):
                if model.__name__ not in ALLOWED_JSON_MODELS:
                    raise AssertionError(
                        f"{model.__name__}.{field.name} JSONField not allowed on domain model"
                    )
                if field.name in FORBIDDEN_JSON_FIELD_NAMES:
                    raise AssertionError(
                        f"{model.__name__}.{field.name} forbidden JSONField name"
                    )


def assert_canonical_ids_unique(model_label: str) -> int:
    model = apps.get_model("game_data", model_label)
    if not hasattr(model, "canonical_id"):
        return 0
    total = model.objects.count()
    distinct = model.objects.values("canonical_id").distinct().count()
    if total != distinct:
        raise AssertionError(f"{model_label}: duplicate canonical_id ({total} vs {distinct})")
    return total
