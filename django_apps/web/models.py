"""Web-layer persistence (preview thumbnails, etc.)."""

from __future__ import annotations

from django.db import models

from django_apps.web.shape_part_sprite_storage import shape_part_sprite_storage


class ShapePartSprite(models.Model):  # type: ignore[misc]
    """Single-quadrant atomic shape PNG for Canvas2D tile composition."""

    sprite_key = models.CharField(max_length=192, unique=True)
    mesh_key = models.CharField(max_length=64)
    color_code = models.CharField(max_length=16, blank=True)
    material_key = models.CharField(max_length=64, blank=True)
    quadrant_index = models.PositiveSmallIntegerField()
    image = models.ImageField(
        upload_to="assets/shape_part_sprites/",
        storage=shape_part_sprite_storage,
    )
    image_width = models.PositiveSmallIntegerField()
    image_height = models.PositiveSmallIntegerField()
    renderer_version = models.CharField(max_length=32, default="v1")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "web_shape_part_sprite"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "mesh_key",
                    "color_code",
                    "material_key",
                    "quadrant_index",
                    "renderer_version",
                ],
                name="uniq_shape_part_sprite_variant",
            ),
        ]

    def __str__(self) -> str:
        return str(self.sprite_key)


class GraphPreviewImage(models.Model):  # type: ignore[misc]
    """PNG bytes for macro graph node previews (survives ephemeral PaaS filesystem)."""

    cache_key = models.CharField(max_length=24, primary_key=True)
    png = models.BinaryField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "web_graph_preview_image"
