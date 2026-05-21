"""Admin menu taxonomy only — not a substitute for relational FKs."""

# ruff: noqa: E501

from __future__ import annotations

from django.db import models


class GameDataNamespace(models.Model):
    code = models.CharField(max_length=64, unique=True)
    label = models.CharField(max_length=128)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "game data namespace"
        verbose_name_plural = "⑩ Taxonomy · Namespaces"
        ordering = ["order", "code"]

    def __str__(self) -> str:
        return self.label or self.code


class GameDataSection(models.Model):
    namespace = models.ForeignKey(
        GameDataNamespace, on_delete=models.CASCADE, related_name="sections"
    )
    code = models.CharField(max_length=128)
    label = models.CharField(max_length=128)
    order = models.PositiveIntegerField(default=0)
    django_model_label = models.CharField(max_length=128, blank=True, default="")

    class Meta:
        verbose_name = "game data section"
        verbose_name_plural = "⑩ Taxonomy · Sections"
        ordering = ["namespace__order", "order", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["namespace", "code"],
                name="uq_gamedata_section_namespace_code",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.namespace.code}.{self.code}"
