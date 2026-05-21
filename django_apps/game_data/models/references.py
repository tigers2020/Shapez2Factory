"""Unresolved cross-references during import (staging only)."""

# ruff: noqa: E501

from __future__ import annotations

from django.db import models

from django_apps.game_data.enums import GameDataRefKind
from django_apps.game_data.models.import_meta import ImportBatch, SourceObject


class GameDataReference(models.Model):
    import_batch = models.ForeignKey(
        ImportBatch, on_delete=models.CASCADE, related_name="data_references"
    )
    from_source = models.ForeignKey(
        SourceObject,
        on_delete=models.CASCADE,
        related_name="outgoing_references",
    )
    to_source = models.ForeignKey(
        SourceObject,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="incoming_references",
    )
    ref_kind = models.CharField(max_length=128, choices=GameDataRefKind.choices)
    ref_value = models.CharField(max_length=512)
    resolved = models.BooleanField(default=False)

    class Meta:
        verbose_name = "unresolved reference"
        verbose_name_plural = "⑪ References · Unresolved"
        indexes = [
            models.Index(fields=["import_batch", "ref_kind", "resolved"]),
        ]

    def __str__(self) -> str:
        state = "resolved" if self.resolved else "open"
        return f"{self.ref_kind}:{self.ref_value} ({state})"
