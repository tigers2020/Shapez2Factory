"""Island ``SpaceBelt_*`` / ``SpacePipe_*`` layout registry (game_data import)."""

from __future__ import annotations

from django.db import models

from django_apps.game_data.models.import_meta import ImportBatch


class SpaceTransportLayoutRegistry(models.Model):
    """Queryable mirror of island transport layout ids from research_unlocks + simulation_systems."""

    class TransportKind(models.TextChoices):
        SPACE_BELT = "space_belt", "Space belt"
        SPACE_PIPE = "space_pipe", "Space pipe"

    class SimulationFamily(models.TextChoices):
        CONVEYOR = "conveyor", "Conveyor"
        MERGER = "merger", "Merger"
        SPLITTER = "splitter", "Splitter"

    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(
        ImportBatch,
        on_delete=models.CASCADE,
        related_name="space_transport_layouts",
    )
    tile_id = models.CharField(max_length=128, unique=True)
    transport_kind = models.CharField(max_length=32, choices=TransportKind.choices)
    group_id = models.CharField(max_length=64)
    layout_suffix = models.CharField(max_length=64)
    simulation_system_key = models.TextField(blank=True, default="")
    simulation_family = models.CharField(
        max_length=16,
        choices=SimulationFamily.choices,
        blank=True,
        default="",
    )
    routing_allowed = models.BooleanField(default=True)
    canonical_rotation = models.PositiveSmallIntegerField(default=0)
    allowed_rotations = models.CharField(
        max_length=16,
        default="0,1,2,3",
        help_text="Comma-separated rotation indices (East=0, clockwise).",
    )
    has_io_signature = models.BooleanField(default=False)
    input_mask_eswn = models.CharField(
        max_length=4,
        blank=True,
        default="",
        help_text="ESWN mask as 4-char 0/1 string when curated IO exists.",
    )
    output_mask_eswn = models.CharField(max_length=4, blank=True, default="")
    source_row_index = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "space transport layout"
        verbose_name_plural = "⑧ EVTC · Space transport layouts"
        ordering = ["tile_id"]

    def __str__(self) -> str:
        return self.tile_id
