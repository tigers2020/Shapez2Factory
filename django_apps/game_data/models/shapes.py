"""Canonical game_data domain models (see documents/game_data_analysis/_audit/09)."""

# ruff: noqa: E501

from __future__ import annotations

from django.db import models

from django_apps.game_data.models.import_meta import ImportBatch, SourceObject


class FluidColor(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(
        ImportBatch, on_delete=models.CASCADE, related_name="fluid_colors"
    )
    color_name = models.CharField(max_length=64, unique=True)
    fluid_kind = models.CharField(max_length=32, default="ColorFluid")
    source_stable_id = models.CharField(max_length=64, blank=True, default="")
    source_row_index = models.PositiveIntegerField()

    class Meta:
        verbose_name = "fluid color"
        verbose_name_plural = "③ Shapes · Fluid colors"

    def __str__(self) -> str:
        return self.color_name


class ShapeComponentKind(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    component_key = models.CharField(max_length=128, unique=True)
    catalog_shape_code = models.CharField(max_length=8, blank=True, default="")
    display_label = models.CharField(max_length=128, blank=True, default="")

    class Meta:
        verbose_name = "shape component kind"
        verbose_name_plural = "③ Shapes · Component kinds"

    def __str__(self) -> str:
        return self.component_key


class ShapeRecipe(models.Model):
    """Canonical geometry row; provenance lives on ``ShapeRecipeSourceAppearance``."""

    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(
        ImportBatch, on_delete=models.CASCADE, related_name="shape_recipes"
    )
    operation_uid = models.PositiveIntegerField(unique=True)
    shape_hash = models.CharField(max_length=128, unique=True)
    quadrant_count = models.PositiveSmallIntegerField(default=4)
    layer_count = models.PositiveSmallIntegerField(default=1)
    source_stable_id = models.CharField(max_length=64, blank=True, default="")
    source_object = models.ForeignKey(
        SourceObject,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="shape_recipes",
    )

    class Meta:
        verbose_name = "shape recipe"
        verbose_name_plural = "③ Shapes · Recipes"
        ordering = ["operation_uid"]

    def __str__(self) -> str:
        return f"{self.shape_hash} (uid={self.operation_uid})"


class ShapeRecipeSourceAppearance(models.Model):
    """Per-artifact row provenance for a canonical ``ShapeRecipe`` (P1 policy)."""

    class CatalogSource(models.TextChoices):
        FULL = "full", "shapes.json"
        ITEMS = "items", "items.json subset"

    shape_recipe = models.ForeignKey(
        ShapeRecipe,
        on_delete=models.CASCADE,
        related_name="source_appearances",
    )
    source_object = models.ForeignKey(
        SourceObject,
        on_delete=models.PROTECT,
        related_name="shape_recipe_appearances",
    )
    import_batch = models.ForeignKey(
        ImportBatch,
        on_delete=models.CASCADE,
        related_name="shape_recipe_appearances",
    )
    catalog_source = models.CharField(max_length=16, choices=CatalogSource.choices)
    artifact_filename = models.CharField(max_length=64)
    source_row_index = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["import_batch", "artifact_filename", "source_row_index"],
                name="uq_shape_appearance_batch_file_row",
            ),
        ]
        verbose_name = "shape recipe source appearance"
        verbose_name_plural = "③ Shapes · Recipe appearances"
        ordering = ["artifact_filename", "source_row_index"]

    def __str__(self) -> str:
        return f"{self.shape_recipe.shape_hash} ← {self.artifact_filename}[{self.source_row_index}]"


class ShapeRecipeLayer(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    shape_recipe = models.ForeignKey(ShapeRecipe, on_delete=models.CASCADE, related_name="layers")
    layer_index = models.PositiveSmallIntegerField()
    hash_segment = models.CharField(max_length=64, blank=True, default="")
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["shape_recipe", "layer_index"],
                name="uq_shape_layer_index",
            ),
        ]
        verbose_name = "shape recipe layer"
        verbose_name_plural = "③ Shapes · Recipe layers"
        ordering = ["layer_index"]

    def __str__(self) -> str:
        return f"{self.shape_recipe.shape_hash} L{self.layer_index}"


class ShapeQuadrantSlot(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    layer = models.ForeignKey(ShapeRecipeLayer, on_delete=models.CASCADE, related_name="slots")
    quadrant_index = models.PositiveSmallIntegerField()
    shape_component_kind = models.ForeignKey(
        ShapeComponentKind, on_delete=models.SET_NULL, null=True, blank=True, related_name="slots"
    )
    fluid_color = models.ForeignKey(
        FluidColor, on_delete=models.SET_NULL, null=True, blank=True, related_name="slots"
    )
    is_empty_shape = models.BooleanField(default=False)
    is_empty_color = models.BooleanField(default=False)
    hash_token = models.CharField(max_length=8, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["layer", "quadrant_index"],
                name="uq_quadrant_slot",
            ),
        ]
        verbose_name = "shape quadrant slot"
        verbose_name_plural = "③ Shapes · Quadrant slots"
        ordering = ["quadrant_index"]

    def __str__(self) -> str:
        return f"{self.layer} Q{self.quadrant_index}"
