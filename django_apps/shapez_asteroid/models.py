# 소행성 격자 (x, y)별 world status — 블루프린트 mining_map과 별개.

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class AsteroidCellStatusKind(models.Model):
    """표시용 status 종류 (전역 카탈로그)."""

    slug = models.SlugField(max_length=64, unique=True)
    label = models.CharField(max_length=128)

    class Meta:
        ordering = ["slug"]

    def __str__(self) -> str:
        return f"{self.slug}"


class AsteroidMapCell(models.Model):
    """전역 격자 한 칸당 하나의 status (`x != 0`)."""

    x = models.IntegerField()
    y = models.IntegerField()
    kind = models.ForeignKey(
        AsteroidCellStatusKind,
        on_delete=models.PROTECT,
        related_name="cells",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["x", "y"], name="shapez_asteroid_mapcell_xy_uniq"),
            models.CheckConstraint(condition=~Q(x=0), name="shapez_asteroid_mapcell_x_nonzero"),
        ]
        indexes = [
            models.Index(fields=["x", "y"]),
        ]

    def clean(self) -> None:
        if self.x == 0:
            raise ValidationError({"x": "x must be non-zero (no game column at x=0)."})

    def __str__(self) -> str:
        return f"({self.x},{self.y})→{self.kind.slug}"
