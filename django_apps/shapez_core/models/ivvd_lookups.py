"""Global IVVD lookup tables (seeded; FK targets for enums formerly stored as strings)."""

from __future__ import annotations

from django.db import models


class ShapezIvvdSeverity(models.Model):
    """e.g. ``error``, ``warning``."""

    code = models.SlugField(max_length=32, primary_key=True)
    label = models.CharField(max_length=80)
    sort_order = models.SmallIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "code")
        verbose_name_plural = "IVVD severities"

    def __str__(self) -> str:
        return (self.label or "").strip() or str(self.code)


class ShapezIvvdValidationPhase(models.Model):
    """Pipeline phase keys (``schema``, ``xref``, ``semantic``)."""

    code = models.SlugField(max_length=40, primary_key=True)
    label = models.CharField(max_length=80, blank=True)
    sort_order = models.SmallIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "code")
        verbose_name_plural = "IVVD validation phases"

    def __str__(self) -> str:
        return (self.label or "").strip() or str(self.code)


class ShapezIvvdLifecycleStatus(models.Model):
    """Release integrity / lifecycle state."""

    code = models.SlugField(max_length=40, primary_key=True)
    label = models.CharField(max_length=80, blank=True)
    sort_order = models.SmallIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "code")
        verbose_name_plural = "IVVD lifecycle statuses"

    def __str__(self) -> str:
        return (self.label or "").strip() or str(self.code)


class ShapezIvvdDocumentKind(models.Model):
    """Document kind (matches former ``ShapezBasedataDocument.Kind`` values)."""

    code = models.SlugField(max_length=40, primary_key=True)
    label = models.CharField(max_length=120, blank=True)
    sort_order = models.SmallIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "code")
        verbose_name_plural = "IVVD document kinds"

    def __str__(self) -> str:
        return (self.label or "").strip() or str(self.code)


class ShapezIvvdArtifactType(models.Model):
    """Canonical artifact classification."""

    code = models.SlugField(max_length=80, primary_key=True)
    label = models.CharField(max_length=120, blank=True)
    sort_order = models.SmallIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "code")
        verbose_name_plural = "IVVD artifact types"

    def __str__(self) -> str:
        return (self.label or "").strip() or str(self.code)


class ShapezIntegrityIssueCode(models.Model):
    """Controlled vocabulary for integrity issue codes."""

    code = models.SlugField(max_length=80, primary_key=True)
    summary = models.CharField(max_length=240, blank=True)
    default_severity = models.ForeignKey(
        ShapezIvvdSeverity,
        on_delete=models.PROTECT,
        related_name="issue_codes_defaulting_here",
    )

    class Meta:
        ordering = ("code",)
        verbose_name_plural = "IVVD integrity issue codes"

    def __str__(self) -> str:
        code = str(self.code)
        if (self.summary or "").strip():
            return f"{code} — {(self.summary or '').strip()[:60]}"
        return code
