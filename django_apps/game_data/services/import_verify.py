"""Verify on-disk game_data bundle matches the latest imported batch (read-only)."""

from __future__ import annotations

from pathlib import Path

from django_apps.game_data.importers.source_loader import sha256_file
from django_apps.game_data.models import ArtifactChecksum, ImportBatch


class GameDataVerifyError(RuntimeError):
    """Raised when --verify preconditions fail."""


def verify_game_data_source(source_dir: Path) -> ImportBatch:
    """Ensure ``manifest.json`` hash matches the latest ``ImportBatch`` and artifacts are ok."""

    manifest_path = source_dir.resolve() / "manifest.json"
    if not manifest_path.is_file():
        msg = f"manifest.json not found in {source_dir}"
        raise GameDataVerifyError(msg)

    disk_hash = sha256_file(manifest_path)
    batch = ImportBatch.objects.order_by("-imported_at", "-id").first()
    if batch is None:
        raise GameDataVerifyError("no import batch in database; run import_game_data first")

    if batch.manifest_self_hash != disk_hash:
        raise GameDataVerifyError(
            "manifest on disk does not match latest ImportBatch "
            f"(db={batch.manifest_self_hash!r}, disk={disk_hash!r})"
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
