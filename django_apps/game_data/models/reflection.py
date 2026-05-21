"""Canonical game_data domain models (see documents/game_data_analysis/_audit/09)."""

# ruff: noqa: E501

from __future__ import annotations

from django.db import models

from django_apps.game_data.models.import_meta import ImportBatch


class ClrTypeRegistryEntry(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(
        ImportBatch, on_delete=models.CASCADE, related_name="clr_types"
    )
    type_name = models.CharField(max_length=512)
    assembly_name = models.CharField(max_length=512)
    source_stable_id = models.CharField(max_length=64, blank=True, default="")
    is_compiler_generated = models.BooleanField(default=False)
    source_row_index = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["type_name", "assembly_name"],
                name="uq_clr_type_assembly",
            ),
        ]
        verbose_name = "CLR type entry"
        verbose_name_plural = "⑨ Reflection · CLR types"

    def __str__(self) -> str:
        return f"{self.type_name} ({self.assembly_name})"
