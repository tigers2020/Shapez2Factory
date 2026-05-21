"""Canonical game_data domain models (see documents/game_data_analysis/_audit/09)."""

# ruff: noqa: E501

from __future__ import annotations

from django.db import models

from django_apps.game_data.models.import_meta import ImportBatch, SourceObject
from django_apps.game_data.models.l10n import (
    LazyLocalizedTextRef,
)
from django_apps.game_data.models.shapes import ShapeRecipe


class ResearchUpgrade(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="research_upgrades")
    upgrade_key = models.CharField(max_length=255, unique=True)
    source_stable_id = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        verbose_name = "research upgrade"
        verbose_name_plural = "⑤ Research · Upgrades"

    def __str__(self) -> str:
        return self.upgrade_key


class ResearchMechanic(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="research_mechanics")
    mechanic_key = models.CharField(max_length=255, unique=True)
    source_stable_id = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        verbose_name = "research mechanic"
        verbose_name_plural = "⑤ Research · Mechanics"

    def __str__(self) -> str:
        return self.mechanic_key


class ResearchMilestone(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="research_milestones")
    node_key = models.CharField(max_length=255, unique=True)
    title_lazy = models.ForeignKey(
        LazyLocalizedTextRef,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="milestone_titles",
    )
    description_lazy = models.ForeignKey(
        LazyLocalizedTextRef,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="milestone_descriptions",
    )
    icon_id = models.CharField(max_length=128, blank=True, default="")
    source_stable_id = models.CharField(max_length=64, blank=True, default="")
    source_object = models.ForeignKey(
        SourceObject,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="research_milestones",
    )

    class Meta:
        verbose_name = "research milestone"
        verbose_name_plural = "⑤ Research · Milestones"

    def __str__(self) -> str:
        return self.node_key


class ResearchSideQuest(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="research_side_quests")
    node_key = models.CharField(max_length=255, unique=True)
    title_lazy = models.ForeignKey(
        LazyLocalizedTextRef,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="side_quest_titles",
    )
    description_lazy = models.ForeignKey(
        LazyLocalizedTextRef,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="side_quest_descriptions",
    )
    source_stable_id = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        verbose_name = "research side quest"
        verbose_name_plural = "⑤ Research · Side quests"

    def __str__(self) -> str:
        return self.node_key


class ResearchSideUpgrade(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="research_side_upgrades")
    node_key = models.CharField(max_length=255, unique=True)
    source_stable_id = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        verbose_name = "research side upgrade"
        verbose_name_plural = "⑤ Research · Side upgrades"

    def __str__(self) -> str:
        return self.node_key


class ResearchUnlockCost(models.Model):
    class ParentKind(models.TextChoices):
        MILESTONE = "milestone", "Milestone"
        SIDE_QUEST = "side_quest", "Side quest"
        LINE = "line", "Line"

    canonical_id = models.CharField(max_length=255, unique=True)
    parent_kind = models.CharField(max_length=16, choices=ParentKind.choices)
    milestone = models.ForeignKey(
        ResearchMilestone, on_delete=models.CASCADE, null=True, blank=True, related_name="costs"
    )
    side_quest = models.ForeignKey(
        ResearchSideQuest, on_delete=models.CASCADE, null=True, blank=True, related_name="costs"
    )
    shape_recipe = models.ForeignKey(ShapeRecipe, on_delete=models.PROTECT, related_name="unlock_costs")
    order_index = models.PositiveSmallIntegerField()
    amount = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "research unlock cost"
        verbose_name_plural = "⑤ Research · Unlock costs"
        ordering = ["order_index"]

    def __str__(self) -> str:
        return f"{self.shape_recipe.shape_hash} ×{self.amount}"


class ResearchPrerequisite(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    parent_kind = models.CharField(max_length=16)
    parent_key = models.CharField(max_length=255)
    required_upgrade = models.ForeignKey(
        ResearchUpgrade, on_delete=models.CASCADE, null=True, blank=True, related_name="prerequisites"
    )
    required_mechanic = models.ForeignKey(
        ResearchMechanic, on_delete=models.CASCADE, null=True, blank=True, related_name="prerequisites"
    )

    class Meta:
        verbose_name = "research prerequisite"
        verbose_name_plural = "⑤ Research · Prerequisites"

    def __str__(self) -> str:
        return f"{self.parent_kind}:{self.parent_key}"


class ResearchGlobalConfig(models.Model):
    import_batch = models.OneToOneField(ImportBatch, on_delete=models.CASCADE, related_name="research_config")
    config_key = models.CharField(max_length=64, default="default")
    config_value = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "research global config"
        verbose_name_plural = "⑤ Research · Global config"

    def __str__(self) -> str:
        return f"{self.import_batch} · {self.config_key}"
