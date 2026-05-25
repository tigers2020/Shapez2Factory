"""Queryable CANON extraction rates (L1b mirror). No import_batch FK."""

# ruff: noqa: E501

from __future__ import annotations

from django.db import models
from django.db.models import Q


class MiningExtractionRule(models.Model):
    """CANON_MANUAL mirror of L1 asteroid extraction rates (shape/fluid)."""

    class ResourceKind(models.TextChoices):
        SHAPE = "shape", "Shape"
        FLUID = "fluid", "Fluid"

    class SourceKind(models.TextChoices):
        CANON_MANUAL = "CANON_MANUAL", "CANON manual"

    resource_kind = models.CharField(
        max_length=16,
        choices=ResourceKind.choices,
    )
    transport_kind = models.CharField(max_length=64)
    mini_unit_output_per_min = models.DecimalField(
        max_digits=12,
        decimal_places=4,
    )
    output_unit = models.CharField(max_length=64)
    base_mini_units_per_miner = models.PositiveSmallIntegerField(default=4)
    mini_units_per_extension = models.PositiveSmallIntegerField(default=4)
    max_extension_count = models.PositiveSmallIntegerField(default=3)
    source_kind = models.CharField(
        max_length=32,
        choices=SourceKind.choices,
        default=SourceKind.CANON_MANUAL,
    )
    source_note = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "mining extraction rule"
        verbose_name_plural = "⑦ Mining · Extraction rules"
        constraints = [
            models.UniqueConstraint(
                fields=["resource_kind"],
                condition=Q(is_active=True),
                name="unique_active_mining_extraction_rule_per_resource",
            ),
        ]

    def __str__(self) -> str:
        active = "active" if self.is_active else "inactive"
        return f"{self.resource_kind} ({active})"
