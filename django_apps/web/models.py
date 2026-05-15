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


class AsteroidDecodedLayoutDocument(models.Model):  # type: ignore[misc]
    """One decoded asteroid / island blueprint file (root ``V`` + ``BP`` JSON)."""

    content_sha256 = models.CharField(max_length=64, unique=True, db_index=True)
    source_label = models.CharField(max_length=512, blank=True)
    root_v = models.PositiveIntegerField()
    bp_type = models.CharField(max_length=64, blank=True)
    binary_version = models.PositiveIntegerField(null=True, blank=True)
    icon_json = models.JSONField(null=True, blank=True)
    document_json = models.JSONField()
    entry_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "web_asteroid_decoded_layout_document"

    def __str__(self) -> str:
        return f"{self.bp_type or '?'} v{self.root_v} ({self.content_sha256[:8]}…)"


class AsteroidDecodedLayoutEntry(models.Model):  # type: ignore[misc]
    """Single element of ``BP.Entries`` (tile / building payload as JSON)."""

    document = models.ForeignKey(
        AsteroidDecodedLayoutDocument,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    entry_index = models.PositiveIntegerField()
    entry_json = models.JSONField()

    class Meta:
        db_table = "web_asteroid_decoded_layout_entry"
        ordering = ("entry_index",)
        constraints = [
            models.UniqueConstraint(
                fields=("document", "entry_index"),
                name="uniq_asteroid_decoded_layout_entry_index",
            ),
        ]

    def __str__(self) -> str:
        return f"#{self.entry_index} doc={self.document_id}"
