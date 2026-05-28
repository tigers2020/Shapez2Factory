"""Queryable CANON for EVTC exterior Space Belt / Space Pipe saturated caps (S2 1.0)."""

# ruff: noqa: E501

from __future__ import annotations

from django.db import models
from django.db.models import Q


class ExteriorShapeTransportCapacity(models.Model):
    """CANON mirror of EVTC shape denominator metadata per belt speed tier."""

    class SourceKind(models.TextChoices):
        EVTC_CANON = "EVTC_CANON", "EVTC canonical"

    speed_tier = models.PositiveSmallIntegerField()
    mini_unit_output_per_min = models.DecimalField(
        max_digits=12,
        decimal_places=4,
    )
    buildings_per_regular_belt = models.PositiveSmallIntegerField()
    lanes_per_line = models.PositiveSmallIntegerField(
        help_text="Regular-belt groups per exterior line (tier-1 CANON: 12 → 720 shapes/min line).",
    )
    lines_per_space_belt = models.PositiveSmallIntegerField(
        help_text="Exterior lines per Space Belt building (tier-1 CANON: 12 → 8640 shapes/min belt).",
    )
    space_belt_full_belt_count = models.PositiveSmallIntegerField(
        help_text="Wiki saturated regular-belt equivalents per full belt (48 → 2880/min); not per-building cap.",
    )
    output_unit = models.CharField(max_length=64, default="shapes_per_min")
    source_kind = models.CharField(
        max_length=32,
        choices=SourceKind.choices,
        default=SourceKind.EVTC_CANON,
    )
    source_note = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "exterior shape transport capacity"
        verbose_name_plural = "⑧ EVTC · Shape transport capacity"
        constraints = [
            models.UniqueConstraint(
                fields=["speed_tier"],
                condition=Q(is_active=True),
                name="unique_active_exterior_shape_transport_per_tier",
            ),
        ]

    def __str__(self) -> str:
        active = "active" if self.is_active else "inactive"
        return f"shape tier {self.speed_tier} ({active})"


class ExteriorFluidTransportCapacity(models.Model):
    """CANON mirror of EVTC fluid denominator metadata per pipe speed tier."""

    class SourceKind(models.TextChoices):
        EVTC_CANON = "EVTC_CANON", "EVTC canonical"

    speed_tier = models.PositiveSmallIntegerField()
    fluid_launcher_output_per_min = models.DecimalField(
        max_digits=12,
        decimal_places=4,
    )
    space_pipe_full_fluid_launcher_count = models.PositiveSmallIntegerField()
    output_unit = models.CharField(max_length=64, default="liters_per_min")
    source_kind = models.CharField(
        max_length=32,
        choices=SourceKind.choices,
        default=SourceKind.EVTC_CANON,
    )
    source_note = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "exterior fluid transport capacity"
        verbose_name_plural = "⑧ EVTC · Fluid transport capacity"
        constraints = [
            models.UniqueConstraint(
                fields=["speed_tier"],
                condition=Q(is_active=True),
                name="unique_active_exterior_fluid_transport_per_tier",
            ),
        ]

    def __str__(self) -> str:
        active = "active" if self.is_active else "inactive"
        return f"fluid tier {self.speed_tier} ({active})"
