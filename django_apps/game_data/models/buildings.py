"""Canonical game_data domain models (see documents/game_data_analysis/_audit/09)."""

# ruff: noqa: E501

from __future__ import annotations

from django.db import models

from django_apps.game_data.models.import_meta import ImportBatch, SourceObject


class BuildingVariant(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="building_variants")
    internal_name = models.CharField(max_length=255, unique=True)
    source_stable_id = models.CharField(max_length=64)
    display_name_key = models.CharField(max_length=512, blank=True, default="")
    is_mirrored = models.BooleanField(default=False)
    size_x = models.SmallIntegerField(default=0)
    size_y = models.SmallIntegerField(default=0)
    size_z = models.SmallIntegerField(default=0)
    connector_count = models.PositiveSmallIntegerField(default=0)
    source_row_index = models.PositiveIntegerField()
    source_object = models.ForeignKey(
        SourceObject,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="building_variants",
    )

    class Meta:
        verbose_name = "building variant"
        verbose_name_plural = "④ Buildings · Variants"
        ordering = ["internal_name"]

    def __str__(self) -> str:
        return self.internal_name


class BuildingConnector(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    building_variant = models.ForeignKey(BuildingVariant, on_delete=models.CASCADE, related_name="connectors")
    order_index = models.PositiveSmallIntegerField()
    connector_role = models.CharField(max_length=64)
    tile_direction = models.CharField(max_length=32, blank=True, default="")
    io_channel_type = models.CharField(max_length=32, blank=True, default="")
    stand_type = models.CharField(max_length=32, blank=True, default="")
    has_seperators = models.BooleanField(default=False)
    position_x = models.SmallIntegerField(default=0)
    position_y = models.SmallIntegerField(default=0)
    position_z = models.SmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["building_variant", "order_index"],
                name="uq_building_connector_order",
            ),
        ]
        verbose_name = "building connector"
        verbose_name_plural = "④ Buildings · Connectors"
        ordering = ["order_index"]

    def __str__(self) -> str:
        return f"{self.building_variant.internal_name} #{self.order_index} {self.connector_role}"


class BuildingFootprintTile(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    building_variant = models.ForeignKey(BuildingVariant, on_delete=models.CASCADE, related_name="footprint_tiles")
    order_index = models.PositiveSmallIntegerField()
    x = models.SmallIntegerField(default=0)
    y = models.SmallIntegerField(default=0)
    z = models.SmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["building_variant", "order_index"],
                name="uq_footprint_tile_order",
            ),
        ]
        verbose_name = "footprint tile"
        verbose_name_plural = "④ Buildings · Footprint tiles"
        ordering = ["order_index"]

    def __str__(self) -> str:
        return f"{self.building_variant.internal_name} tile {self.order_index}"


class BuildingGroup(models.Model):
    class DisplayProfile(models.TextChoices):
        PLAIN = "plain", "buildings.json"
        LAZY = "lazy_overlay", "building_groups.json"

    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="building_groups")
    group_key = models.CharField(max_length=255, unique=True)
    registry_stable_id = models.CharField(max_length=64, blank=True, default="")
    display_profile = models.CharField(max_length=16, choices=DisplayProfile.choices)
    display_name_key = models.CharField(max_length=512, blank=True, default="")
    is_transport_building = models.BooleanField(default=False)
    placement_mode = models.CharField(max_length=64, blank=True, default="")
    player_buildable = models.BooleanField(default=True)
    selectable = models.BooleanField(default=True)
    removable = models.BooleanField(default=True)
    auto_connect = models.BooleanField(default=False)
    source_row_index = models.PositiveIntegerField()
    source_object = models.ForeignKey(
        SourceObject,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="building_groups",
    )

    class Meta:
        verbose_name = "building group"
        verbose_name_plural = "④ Buildings · Groups"
        ordering = ["group_key"]

    def __str__(self) -> str:
        return f"{self.group_key} ({self.get_display_profile_display()})"


class BuildingLocalizationOverlay(models.Model):
    building_group = models.OneToOneField(
        BuildingGroup, on_delete=models.CASCADE, related_name="localization"
    )
    title_key = models.CharField(max_length=512, blank=True, default="")
    description_key = models.CharField(max_length=512, blank=True, default="")
    lazy_text_namespace = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        verbose_name = "building localization"
        verbose_name_plural = "④ Buildings · Localization"

    def __str__(self) -> str:
        return str(self.building_group)


class BuildingSimulationSetting(models.Model):
    building_group = models.OneToOneField(
        BuildingGroup, on_delete=models.CASCADE, related_name="simulation_setting"
    )
    is_transport_building = models.BooleanField(default=False)
    pipette_override_id = models.CharField(max_length=128, blank=True, default="")
    show_stat_belt_processing_time = models.BooleanField(default=False)
    show_stat_buildings_per_full_belt = models.BooleanField(default=False)
    show_in_speed_overview = models.BooleanField(default=False)

    class Meta:
        verbose_name = "building simulation setting"
        verbose_name_plural = "④ Buildings · Simulation settings"

    def __str__(self) -> str:
        return f"sim:{self.building_group}"


class BuildingGroupMember(models.Model):
    class MemberResolution(models.TextChoices):
        EMBEDDED = "embedded", "Embedded"
        CYCLE_REF = "cycle_ref", "Cycle reference"

    canonical_id = models.CharField(max_length=255, unique=True)
    building_group = models.ForeignKey(BuildingGroup, on_delete=models.CASCADE, related_name="members")
    building_variant = models.ForeignKey(
        BuildingVariant, on_delete=models.PROTECT, null=True, blank=True, related_name="group_memberships"
    )
    order_index = models.PositiveSmallIntegerField()
    member_resolution = models.CharField(max_length=16, choices=MemberResolution.choices)
    internal_variant_name = models.CharField(max_length=255, blank=True, default="")
    cycle_label = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["building_group", "order_index"],
                name="uq_group_member_order",
            ),
        ]
        verbose_name = "building group member"
        verbose_name_plural = "④ Buildings · Group members"
        ordering = ["order_index"]

    def __str__(self) -> str:
        variant = self.building_variant.internal_name if self.building_variant_id else self.internal_variant_name
        return f"{self.building_group.group_key} → {variant}"


class BuildingPlacementRule(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    building_group = models.ForeignKey(BuildingGroup, on_delete=models.CASCADE, related_name="placement_rules")
    order_index = models.PositiveSmallIntegerField()
    rule_kind = models.CharField(max_length=128)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["building_group", "order_index"],
                name="uq_placement_rule_order",
            ),
        ]
        verbose_name = "placement rule"
        verbose_name_plural = "④ Buildings · Placement rules"
        ordering = ["order_index"]

    def __str__(self) -> str:
        return f"{self.building_group.group_key} rule {self.rule_kind}"


class TransportBuildingRegistry(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="transport_registry")
    transport_kind = models.CharField(max_length=128, unique=True)
    transport_category = models.CharField(max_length=32, blank=True, default="")
    building_variant = models.ForeignKey(
        BuildingVariant, on_delete=models.PROTECT, related_name="transport_registrations"
    )
    display_name_key = models.CharField(max_length=512, blank=True, default="")
    source_row_index = models.PositiveIntegerField()

    class Meta:
        verbose_name = "transport registry"
        verbose_name_plural = "④ Buildings · Transport registry"

    def __str__(self) -> str:
        return self.transport_kind
