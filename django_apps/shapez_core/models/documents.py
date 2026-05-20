"""Basedata document rows (raw + parsed payload)."""

from __future__ import annotations

from django.db import models

from django_apps.shapez_core.models.ivvd_lookups import ShapezIvvdDocumentKind
from django_apps.shapez_core.models.release import ShapezBasedataRelease


class ShapezBasedataDocument(models.Model):
    """One JSON (or text) file under a basedata root."""

    class Kind(models.TextChoices):
        IDENTIFIERS = "identifiers", "identifiers.json"
        BUILDINGS = "buildings", "buildings.json"
        TRANSLATIONS = "translations", "translations"
        SCENARIO = "scenario", "scenario"
        DIFFICULTY_PRESET = "difficulty_preset", "difficulty preset"
        SCENARIO_PARAMETER_PRESET = "scenario_parameter_preset", "scenario parameter preset"
        JSON_SCHEMA = "json_schema", "json schema"
        VERSION = "version", "version file"
        OTHER = "other", "other"

    release = models.ForeignKey(
        ShapezBasedataRelease,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    document_kind = models.ForeignKey(
        ShapezIvvdDocumentKind,
        on_delete=models.PROTECT,
        related_name="documents",
        db_index=True,
    )
    logical_key = models.CharField(max_length=200, blank=True, default="")
    source_relative_path = models.CharField(max_length=500)
    byte_size = models.BigIntegerField()
    sha256 = models.CharField(max_length=64, db_index=True)
    raw_text = models.TextField(blank=True)
    compressed_raw_blob = models.BinaryField(null=True, blank=True)
    raw_compression_codec = models.CharField(max_length=32, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    imported_at = models.DateTimeField(auto_now_add=True)
    schema_valid = models.BooleanField(null=True, blank=True)
    schema_validation_errors = models.JSONField(default=list, blank=True)
    validated_at = models.DateTimeField(null=True, blank=True)
    schema_version = models.CharField(max_length=200, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("release", "document_kind", "logical_key"),
                name="shapez_basedata_document_release_kind_logical_key_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=("release", "document_kind")),
            models.Index(fields=("release", "source_relative_path")),
        ]

    def __str__(self) -> str:
        dk = getattr(self, "document_kind", None)
        kind_label = ""
        if dk is not None:
            kind_label = (getattr(dk, "label", None) or "").strip() or str(dk.pk)
        tail = (self.logical_key or "").strip() or (self.source_relative_path or "").strip()
        if kind_label and tail:
            return f"{kind_label} · {tail}"
        return tail or kind_label or f"Document #{self.pk}"
