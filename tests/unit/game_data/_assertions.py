from __future__ import annotations

from django.db.models import Model, QuerySet

from django_apps.game_data.models import ImportBatch


def assert_import_batch_has_no_missing_source_object(
    model: type[Model],
    batch: ImportBatch,
    *,
    extra_filter: dict[str, object] | None = None,
) -> None:
    qs: QuerySet[Model] = model.objects.filter(import_batch=batch)
    if extra_filter:
        qs = qs.filter(**extra_filter)
    assert qs.filter(source_object__isnull=True).count() == 0
