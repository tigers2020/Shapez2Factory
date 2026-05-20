"""Validation run provenance."""

from __future__ import annotations

from django.db import models

from django_apps.shapez_core.models.ivvd_lookups import ShapezIvvdValidationPhase
from django_apps.shapez_core.models.release import ShapezBasedataRelease


class ShapezValidationRun(models.Model):
    """One execution of a validation phase against a release."""

    release = models.ForeignKey(
        ShapezBasedataRelease,
        on_delete=models.CASCADE,
        related_name="validation_runs",
    )
    validation_phase = models.ForeignKey(
        ShapezIvvdValidationPhase,
        on_delete=models.PROTECT,
        related_name="validation_runs",
        db_index=True,
    )
    success = models.BooleanField(default=False)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    summary_json = models.JSONField(default=dict, blank=True)
    validator_version = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("release", "validation_phase", "-created_at")),
        ]

    def __str__(self) -> str:
        rel = getattr(self, "release", None)
        gv = rel.game_version if rel is not None else self.release_id
        ph = getattr(self, "validation_phase", None)
        ph_label = ""
        if ph is not None:
            ph_label = (getattr(ph, "label", None) or "").strip() or str(ph.pk)
        ok = "ok" if self.success else "fail"
        return f"v{gv} · {ph_label or '?'} · {ok} · #{self.pk}"
