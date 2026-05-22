from __future__ import annotations

from django_apps.game_data.models import ImportBatch
from django_apps.game_data.snapshots.errors import SnapshotBuildError, SnapshotBuildErrorCode

GAME_DATA_READ_ALIAS = "default"


def pin_latest_import_batch(*, db_alias: str = GAME_DATA_READ_ALIAS) -> ImportBatch:
    batch = ImportBatch.objects.using(db_alias).order_by("-imported_at", "-id").first()
    if batch is None:
        raise SnapshotBuildError(
            SnapshotBuildErrorCode.NO_IMPORT_BATCH,
            "No import batch found",
        )
    return batch
