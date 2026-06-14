"""Verify on-disk game_data bundle matches the latest imported batch (read-only)."""

from __future__ import annotations

from pathlib import Path

from django_apps.game_data.models import ArtifactChecksum, ImportBatch
from django_apps.game_data.services.bundle_gate import validate_game_data_bundle


class GameDataVerifyError(RuntimeError):
    """Raised when --verify preconditions fail."""


def verify_game_data_source(source_dir: Path | None = None) -> ImportBatch:
    """Disk validate via bundle gate, then reconcile manifest hash with latest ImportBatch."""

    bundle = validate_game_data_bundle(source=source_dir)

    batch = ImportBatch.objects.order_by("-imported_at", "-id").first()
    if batch is None:
        raise GameDataVerifyError("no import batch in database; run import_game_data first")

    if batch.manifest_self_hash != bundle.manifest_hash:
        raise GameDataVerifyError(
            "manifest on disk does not match latest ImportBatch "
            f"(db={batch.manifest_self_hash!r}, disk={bundle.manifest_hash!r})"
        )

    mismatched = ArtifactChecksum.objects.filter(
        import_batch=batch,
        import_status="mismatch",
    ).count()
    if mismatched:
        raise GameDataVerifyError(
            f"artifact checksum mismatch count={mismatched} for import batch id={batch.pk}"
        )

    return batch
