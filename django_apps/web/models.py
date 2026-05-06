"""Web-layer persistence (preview thumbnails, etc.)."""

from __future__ import annotations

from django.db import models


class GraphPreviewImage(models.Model):
    """PNG bytes for macro graph node previews (survives ephemeral PaaS filesystem)."""

    cache_key = models.CharField(max_length=24, primary_key=True)
    png = models.BinaryField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "web_graph_preview_image"
