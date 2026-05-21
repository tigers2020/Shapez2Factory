"""Canonical game_data domain models (see documents/game_data_analysis/_audit/09)."""

# ruff: noqa: E501

from __future__ import annotations

from django.db import models

from django_apps.game_data.models.import_meta import ImportBatch, SourceObject


class GameContentAsset(models.Model):
    class ContentKind(models.TextChoices):
        PREFAB = "prefab", "Prefab"
        SPRITE = "sprite", "Sprite"
        MATERIAL = "material", "Material"

    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(
        ImportBatch, on_delete=models.CASCADE, related_name="content_assets"
    )
    content_kind = models.CharField(max_length=16, choices=ContentKind.choices)
    source_stable_id = models.CharField(max_length=64)
    content_path = models.CharField(max_length=512)
    logical_path = models.CharField(max_length=512, blank=True, default="")
    display_name_key = models.CharField(max_length=512, blank=True, default="")
    dump_source_type = models.CharField(max_length=128, blank=True, default="")
    unity_source_guid = models.CharField(max_length=64, blank=True, default="")
    source_row_index = models.PositiveIntegerField()
    source_object = models.ForeignKey(
        SourceObject,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="content_assets",
    )

    class Meta:
        verbose_name = "content asset"
        verbose_name_plural = "② Assets · Content assets"
        indexes = [
            models.Index(fields=["content_kind", "content_path"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_content_kind_display()}: {self.content_path}"


class AssetMetaReference(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(
        ImportBatch, on_delete=models.CASCADE, related_name="meta_references"
    )
    meta_stable_id = models.CharField(max_length=64, unique=True)
    content_asset = models.ForeignKey(
        GameContentAsset, on_delete=models.PROTECT, related_name="meta_links"
    )
    logical_path = models.CharField(max_length=512, unique=True)
    display_name_key = models.CharField(max_length=512, blank=True, default="")
    source_row_index = models.PositiveIntegerField()

    class Meta:
        verbose_name = "asset meta reference"
        verbose_name_plural = "② Assets · Meta references"

    def __str__(self) -> str:
        return self.logical_path or self.meta_stable_id
