"""Canonical game_data domain models (see documents/game_data_analysis/_audit/09)."""

# ruff: noqa: E501

from __future__ import annotations

from django.db import models


class ImportBatch(models.Model):
    """Import run for one manifest-scoped export bundle (canonical: ``game_data_import_batch``).

    Not a generic audit log table. Child tables: ``ArtifactChecksum`` (per file),
    ``SourceObject`` (per JSON row), ``UnknownProperty`` (ignored fields).
    """

    batch_name = models.CharField(max_length=128, blank=True, default="")
    manifest_self_hash = models.CharField(max_length=80, unique=True)
    game_version = models.CharField(max_length=128)
    unity_version = models.CharField(max_length=64)
    dump_mod_version = models.CharField(max_length=32)
    dump_schema_version = models.CharField(max_length=32)
    dump_timestamp_utc = models.DateTimeField()
    source_method = models.CharField(max_length=64)
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "import run"
        verbose_name_plural = "① Import · Runs"
        ordering = ["-imported_at"]

    def __str__(self) -> str:
        label = self.batch_name or "batch"
        return f"{label} ({self.game_version})"


class ArtifactChecksum(models.Model):
    """Per source JSON file in the bundle (canonical: ``game_data_artifact_checksum``).

    Maps manifest ``file_hashes`` — not the same as ``SourceObject`` (row index).
    """

    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="checksums")
    artifact_filename = models.CharField(max_length=128)
    expected_sha256 = models.CharField(max_length=80)
    import_status = models.CharField(max_length=32, default="pending")
    is_incomplete = models.BooleanField(default=False)

    class Meta:
        verbose_name = "source file checksum"
        verbose_name_plural = "① Import · Source file checksums"
        constraints = [
            models.UniqueConstraint(
                fields=["import_batch", "artifact_filename"],
                name="uq_artifact_per_batch",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.artifact_filename} [{self.import_status}]"


class ExportWarning(models.Model):
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="warnings")
    warning_index = models.PositiveIntegerField()
    message = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["import_batch", "warning_index"],
                name="uq_export_warning_index",
            ),
        ]
        verbose_name = "export warning"
        verbose_name_plural = "① Import · Export warnings"
        ordering = ["warning_index"]

    def __str__(self) -> str:
        return f"#{self.warning_index}: {(self.message or '')[:48]}"


class ExportIncompleteSection(models.Model):
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="incomplete_sections")
    section_code = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["import_batch", "section_code"],
                name="uq_incomplete_section",
            ),
        ]
        verbose_name = "incomplete section"
        verbose_name_plural = "① Import · Incomplete sections"

    def __str__(self) -> str:
        return self.section_code


class LocalizationExportStatus(models.Model):
    import_batch = models.OneToOneField(
        ImportBatch, on_delete=models.CASCADE, related_name="localization_status"
    )
    is_empty = models.BooleanField(default=True)
    is_incomplete = models.BooleanField(default=False)
    failure_reason = models.TextField(blank=True, default="")
    expected_hash = models.CharField(max_length=80, blank=True, default="")

    class Meta:
        verbose_name = "localization export status"
        verbose_name_plural = "⑧ L10n · Export status"

    def __str__(self) -> str:
        state = "empty" if self.is_empty else "has rows"
        return f"{self.import_batch} · {state}"


class SourceObject(models.Model):
    """Row-level provenance for a JSON array element (canonical: ``source_object_record``)."""

    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="source_objects")
    source_file = models.CharField(max_length=128)
    source_row_index = models.PositiveIntegerField()
    source_stable_id = models.CharField(max_length=64, blank=True, default="")
    dump_source_type = models.CharField(max_length=128, blank=True, default="")
    source_path = models.CharField(
        max_length=512,
        blank=True,
        default="",
        help_text="Auxiliary nested path (e.g. toolbar Children[]); not primary identity.",
    )
    system_id = models.CharField(max_length=255, blank=True, default="")
    clr_type = models.CharField(max_length=512, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["import_batch", "source_file", "source_row_index"],
                name="uq_source_object_row",
            ),
        ]
        verbose_name = "source object"
        verbose_name_plural = "① Import · Source objects"

    def __str__(self) -> str:
        return f"{self.source_file}[{self.source_row_index}]"


class UnknownProperty(models.Model):
    """Ignored or unmapped import field (canonical: ``unknown_property``; not ``GameDataIgnoredField``).

    Stores ``reason_code`` + ``classification`` + value preview/hash only — never full JSON blobs.
    """

    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="unknown_properties")
    owner_model = models.CharField(max_length=64)
    owner_key = models.CharField(max_length=255)
    json_path = models.TextField()
    key = models.CharField(max_length=255)
    value_type = models.CharField(max_length=32)
    value_preview = models.TextField(blank=True, default="")
    value_hash = models.CharField(max_length=64)
    reason_code = models.CharField(max_length=80, blank=True, default="")
    classification = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        verbose_name = "ignored field"
        verbose_name_plural = "① Import · Ignored fields"
        indexes = [
            models.Index(fields=["import_batch", "owner_model", "owner_key"]),
            models.Index(
                fields=["import_batch", "reason_code"],
                name="gd_unknownprop_batch_reason",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["import_batch", "owner_model", "owner_key", "json_path"],
                name="uq_unknown_property_batch_owner_path",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.owner_model}:{self.key}"
