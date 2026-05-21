"""Canonical game_data domain models (see documents/game_data_analysis/_audit/09)."""

# ruff: noqa: E501

from __future__ import annotations

from django.db import models

from django_apps.game_data.models.assets import GameContentAsset
from django_apps.game_data.models.buildings import BuildingVariant
from django_apps.game_data.models.import_meta import ImportBatch, SourceObject
from django_apps.game_data.models.research import ResearchMechanic


class ToolbarNodeKind(models.TextChoices):
    ROOT = "root", "Root"
    FOLDER = "folder", "Folder / category"
    GROUP = "group", "Group"
    SEPARATOR = "separator", "Separator"
    ACTION = "action", "Action"


class ToolbarTreeNode(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(
        ImportBatch, on_delete=models.CASCADE, related_name="toolbar_tree_nodes"
    )
    source_stable_id = models.CharField(max_length=64, blank=True, default="")
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    child_index = models.PositiveSmallIntegerField(default=0)
    order_index = models.PositiveSmallIntegerField(default=0)
    depth = models.PositiveSmallIntegerField(default=0)
    node_kind = models.CharField(max_length=16, choices=ToolbarNodeKind.choices)
    tree_path = models.CharField(
        max_length=512,
        db_index=True,
        help_text="Flattened display_name_key from dump; debug/audit only.",
    )
    internal_name = models.CharField(max_length=255, blank=True, default="")
    localized_title_key = models.CharField(max_length=512, blank=True, default="")
    icon_identifier = models.CharField(max_length=255, blank=True, default="")
    required_mechanic = models.ForeignKey(
        ResearchMechanic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="toolbar_tree_nodes",
    )
    icon_content_asset = models.ForeignKey(
        GameContentAsset,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="toolbar_nodes_by_icon",
    )
    source_row_index = models.PositiveIntegerField()
    source_object = models.ForeignKey(
        SourceObject,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="toolbar_tree_nodes",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "child_index"],
                name="uq_toolbar_node_sibling",
            ),
        ]
        verbose_name = "toolbar tree node"
        verbose_name_plural = "⑦ Toolbar · Tree nodes"
        ordering = ["depth", "child_index"]

    def __str__(self) -> str:
        if self.internal_name:
            return self.internal_name
        if self.localized_title_key:
            return self.localized_title_key
        return self.tree_path or self.canonical_id


class ToolbarElement(models.Model):
    class ElementKind(models.TextChoices):
        BUILDING = "building", "Building placement"
        ISLAND = "island", "Island placement"
        GROUP = "group", "Group"
        CATEGORY = "category", "Category"
        SEPARATOR = "separator", "Separator"
        OTHER = "other", "Other"

    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(
        ImportBatch, on_delete=models.CASCADE, related_name="toolbar_elements"
    )
    tree_node = models.OneToOneField(
        ToolbarTreeNode, on_delete=models.CASCADE, related_name="toolbar_element"
    )
    source_stable_id = models.CharField(max_length=64, blank=True, default="")
    element_kind = models.CharField(max_length=16, choices=ElementKind.choices)
    stable_key = models.CharField(max_length=255, blank=True, default="")
    display_name = models.CharField(max_length=512, blank=True, default="")
    section_index = models.PositiveSmallIntegerField(null=True, blank=True)
    source_row_index = models.PositiveIntegerField()

    class Meta:
        verbose_name = "toolbar element"
        verbose_name_plural = "⑦ Toolbar · Elements"
        ordering = ["display_name", "source_row_index"]

    def __str__(self) -> str:
        return self.display_name or self.stable_key or self.canonical_id


class ToolbarBuildingPlacement(models.Model):
    toolbar_element = models.OneToOneField(
        ToolbarElement, on_delete=models.CASCADE, related_name="building_placement"
    )
    building_variant = models.ForeignKey(
        BuildingVariant, on_delete=models.PROTECT, related_name="toolbar_placements"
    )
    building_definition_key = models.CharField(max_length=255)
    placer_id = models.CharField(max_length=128, blank=True, default="")
    is_transport_building = models.BooleanField(default=False)
    player_buildable = models.BooleanField(default=True)
    icon_sprite_name = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        verbose_name = "toolbar building placement"
        verbose_name_plural = "⑦ Toolbar · Building placements"

    def __str__(self) -> str:
        return f"{self.toolbar_element} → {self.building_variant.internal_name}"


class ToolbarIslandPlacement(models.Model):
    toolbar_element = models.OneToOneField(
        ToolbarElement, on_delete=models.CASCADE, related_name="island_placement"
    )
    island_group_name = models.CharField(max_length=255)
    placer_id = models.CharField(max_length=128, blank=True, default="")

    class Meta:
        verbose_name = "toolbar island placement"
        verbose_name_plural = "⑦ Toolbar · Island placements"
        ordering = ["island_group_name"]

    def __str__(self) -> str:
        return f"{self.island_group_name} (placer {self.placer_id})"
