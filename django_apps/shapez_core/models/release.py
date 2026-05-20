"""IVVD release root model."""

from __future__ import annotations

from django.db import models

from django_apps.shapez_core.models.ivvd_lookups import ShapezIvvdLifecycleStatus


class ShapezBasedataRelease(models.Model):
    """Immutable basedata release (one row per game bundle version)."""

    class IntegrityStatus(models.TextChoices):
        IMPORTED = "imported", "Imported"
        SCHEMA_CHECKED = "schema_checked", "Schema checked"
        XREF_CHECKED = "xref_checked", "Cross-ref checked"
        SEMANTIC_CHECKED = "semantic_checked", "Semantic checked"
        SEALED = "sealed", "Sealed"
        FAILED = "failed", "Failed"

    game_version = models.PositiveIntegerField(unique=True, db_index=True)
    imported_at = models.DateTimeField(auto_now_add=True)
    notes = models.CharField(max_length=500, blank=True)
    document_count = models.PositiveIntegerField(default=0)
    integrity_status = models.ForeignKey(
        ShapezIvvdLifecycleStatus,
        on_delete=models.PROTECT,
        related_name="releases",
    )
    sealed_at = models.DateTimeField(null=True, blank=True)
    release_integrity_hash = models.CharField(max_length=64, blank=True)
    seal_algorithm = models.CharField(max_length=64, default="shapez-ivvd-seal-v1")
    seal_input_canonical_json = models.TextField(blank=True)

    class Meta:
        ordering = ("-game_version",)

    def __str__(self) -> str:
        life = getattr(self, "integrity_status", None)
        if life is not None:
            life_label = (getattr(life, "label", None) or "").strip() or str(life.pk)
            return f"Basedata v{self.game_version} ({life_label})"
        return f"Basedata v{self.game_version}"
