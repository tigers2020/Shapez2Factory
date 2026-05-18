"""Canonical derived artifacts (lineage stub for future semantic graph)."""

from __future__ import annotations

from django.db import models

from django_apps.shapez_core.models.documents import ShapezBasedataDocument
from django_apps.shapez_core.models.ivvd_lookups import ShapezIvvdArtifactType
from django_apps.shapez_core.models.release import ShapezBasedataRelease


class ShapezCanonicalArtifact(models.Model):
    release = models.ForeignKey(
        ShapezBasedataRelease,
        on_delete=models.CASCADE,
        related_name="canonical_artifacts",
    )
    artifact_type = models.ForeignKey(
        ShapezIvvdArtifactType,
        on_delete=models.PROTECT,
        related_name="artifacts",
        db_index=True,
    )
    source_document = models.ForeignKey(
        ShapezBasedataDocument,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="derived_artifacts",
    )
    derivation_step = models.CharField(max_length=80, blank=True)
    parent_artifact = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="child_artifacts",
    )
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        at = getattr(self, "artifact_type", None)
        at_label = ""
        if at is not None:
            at_label = (getattr(at, "label", None) or "").strip() or str(at.pk)
        step = (self.derivation_step or "").strip()
        if step and at_label:
            return f"{at_label} · {step}"
        return step or at_label or f"Artifact #{self.pk}"
