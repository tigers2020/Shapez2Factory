"""Integrity issues (append-only; supersession for logical replacement)."""

from __future__ import annotations

from django.db import models

from django_apps.shapez_core.models.documents import ShapezBasedataDocument
from django_apps.shapez_core.models.ivvd_lookups import (
    ShapezIntegrityIssueCode,
    ShapezIvvdSeverity,
)
from django_apps.shapez_core.models.release import ShapezBasedataRelease
from django_apps.shapez_core.models.validation import ShapezValidationRun


class ShapezIntegrityIssue(models.Model):
    class Severity(models.TextChoices):
        ERROR = "error", "Error"
        WARNING = "warning", "Warning"

    release = models.ForeignKey(
        ShapezBasedataRelease,
        on_delete=models.CASCADE,
        related_name="integrity_issues",
    )
    validation_run = models.ForeignKey(
        ShapezValidationRun,
        on_delete=models.CASCADE,
        related_name="issues",
    )
    document = models.ForeignKey(
        ShapezBasedataDocument,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="integrity_issues",
    )
    severity = models.ForeignKey(
        ShapezIvvdSeverity,
        on_delete=models.PROTECT,
        related_name="integrity_issues",
    )
    issue_type = models.ForeignKey(
        ShapezIntegrityIssueCode,
        on_delete=models.PROTECT,
        related_name="integrity_issues",
        db_index=True,
    )
    json_path = models.CharField(max_length=500, blank=True)
    message = models.TextField()
    related_identifier = models.CharField(max_length=512, blank=True, db_index=True)
    is_superseded = models.BooleanField(default=False, db_index=True)
    superseded_by_run = models.ForeignKey(
        ShapezValidationRun,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        ordering = ("-validation_run_id", "id")
        indexes = [
            models.Index(fields=("release", "issue_type")),
            models.Index(fields=("release", "is_superseded")),
        ]

    def __str__(self) -> str:
        it = getattr(self, "issue_type", None)
        sev = getattr(self, "severity", None)
        code = str(getattr(it, "pk", "") or self.issue_type_id)
        sev_l = ""
        if sev is not None:
            sev_l = (getattr(sev, "label", None) or "").strip() or str(sev.pk)
        head = f"{code} [{sev_l}]" if sev_l else code
        msg = " ".join((self.message or "").split())[:50]
        if msg:
            return f"{head}: {msg}"
        return head
