"""Canonical game_data domain models (see documents/game_data_analysis/_audit/09)."""

# ruff: noqa: E501

from __future__ import annotations

from django.db import models


class ImportBatch(models.Model):
    """Single manifest-scoped export bundle."""

    batch_name = models.CharField(max_length=128, blank=True, default="")
    manifest_self_hash = models.CharField(max_length=80, unique=True)
    game_version = models.CharField(max_length=128)
    unity_version = models.CharField(max_length=64)
    dump_mod_version = models.CharField(max_length=32)
    dump_schema_version = models.CharField(max_length=32)
    dump_timestamp_utc = models.DateTimeField()
    source_method = models.CharField(max_length=64)
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "import batch"
        verbose_name_plural = "① Import · Batches"
        ordering = ["-imported_at"]

    def __str__(self) -> str:
        label = self.batch_name or "batch"
        return f"{label} ({self.game_version})"


class ArtifactChecksum(models.Model):
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="checksums")
    artifact_filename = models.CharField(max_length=128)
    expected_sha256 = models.CharField(max_length=80)
    import_status = models.CharField(max_length=32, default="pending")
    is_incomplete = models.BooleanField(default=False)

    class Meta:
        verbose_name = "artifact checksum"
        verbose_name_plural = "① Import · Artifact checksums"
        constraints = [
            models.UniqueConstraint(
                fields=["import_batch", "artifact_filename"],
                name="uq_artifact_per_batch",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.artifact_filename} [{self.import_status}]"


class ExportWarning(models.Model):
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="warnings")
    warning_index = models.PositiveIntegerField()
    message = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["import_batch", "warning_index"],
                name="uq_export_warning_index",
            ),
        ]
        verbose_name = "export warning"
        verbose_name_plural = "① Import · Export warnings"
        ordering = ["warning_index"]

    def __str__(self) -> str:
        return f"#{self.warning_index}: {(self.message or '')[:48]}"


class ExportIncompleteSection(models.Model):
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="incomplete_sections")
    section_code = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["import_batch", "section_code"],
                name="uq_incomplete_section",
            ),
        ]
        verbose_name = "incomplete section"
        verbose_name_plural = "① Import · Incomplete sections"

    def __str__(self) -> str:
        return self.section_code


class LocalizationExportStatus(models.Model):
    import_batch = models.OneToOneField(
        ImportBatch, on_delete=models.CASCADE, related_name="localization_status"
    )
    is_empty = models.BooleanField(default=True)
    is_incomplete = models.BooleanField(default=False)
    failure_reason = models.TextField(blank=True, default="")
    expected_hash = models.CharField(max_length=80, blank=True, default="")

    class Meta:
        verbose_name = "localization export status"
        verbose_name_plural = "⑧ L10n · Export status"

    def __str__(self) -> str:
        state = "empty" if self.is_empty else "has rows"
        return f"{self.import_batch} · {state}"


class SourceObject(models.Model):
    """Row-level provenance for a JSON array element."""

    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="source_objects")
    source_file = models.CharField(max_length=128)
    source_row_index = models.PositiveIntegerField()
    source_stable_id = models.CharField(max_length=64, blank=True, default="")
    dump_source_type = models.CharField(max_length=128, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["import_batch", "source_file", "source_row_index"],
                name="uq_source_object_row",
            ),
        ]
        verbose_name = "source object"
        verbose_name_plural = "① Import · Source objects"

    def __str__(self) -> str:
        return f"{self.source_file}[{self.source_row_index}]"


class UnknownProperty(models.Model):
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="unknown_properties")
    owner_model = models.CharField(max_length=64)
    owner_key = models.CharField(max_length=255)
    json_path = models.TextField()
    key = models.CharField(max_length=255)
    value_type = models.CharField(max_length=32)
    value_preview = models.TextField(blank=True, default="")
    value_hash = models.CharField(max_length=64)

    class Meta:
        verbose_name = "unknown property"
        verbose_name_plural = "① Import · Unknown properties"
        indexes = [
            models.Index(fields=["import_batch", "owner_model", "owner_key"]),
        ]

    def __str__(self) -> str:
        return f"{self.owner_model}:{self.key}"


class GameContentAsset(models.Model):
    class ContentKind(models.TextChoices):
        PREFAB = "prefab", "Prefab"
        SPRITE = "sprite", "Sprite"
        MATERIAL = "material", "Material"

    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="content_assets")
    content_kind = models.CharField(max_length=16, choices=ContentKind.choices)
    source_stable_id = models.CharField(max_length=64)
    content_path = models.CharField(max_length=512)
    logical_path = models.CharField(max_length=512, blank=True, default="")
    display_name_key = models.CharField(max_length=512, blank=True, default="")
    dump_source_type = models.CharField(max_length=128, blank=True, default="")
    unity_source_guid = models.CharField(max_length=64, blank=True, default="")
    source_row_index = models.PositiveIntegerField()

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
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="meta_references")
    meta_stable_id = models.CharField(max_length=64, unique=True)
    content_asset = models.ForeignKey(GameContentAsset, on_delete=models.PROTECT, related_name="meta_links")
    logical_path = models.CharField(max_length=512, unique=True)
    display_name_key = models.CharField(max_length=512, blank=True, default="")
    source_row_index = models.PositiveIntegerField()

    class Meta:
        verbose_name = "asset meta reference"
        verbose_name_plural = "② Assets · Meta references"

    def __str__(self) -> str:
        return self.logical_path or self.meta_stable_id


class FluidColor(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="fluid_colors")
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
    class CatalogSource(models.TextChoices):
        FULL = "full", "shapes.json"
        ITEMS = "items", "items.json subset"

    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="shape_recipes")
    operation_uid = models.PositiveIntegerField(unique=True)
    shape_hash = models.CharField(max_length=128, unique=True)
    quadrant_count = models.PositiveSmallIntegerField(default=4)
    layer_count = models.PositiveSmallIntegerField(default=1)
    catalog_source = models.CharField(max_length=16, choices=CatalogSource.choices, default=CatalogSource.FULL)
    source_stable_id = models.CharField(max_length=64, blank=True, default="")
    source_object = models.ForeignKey(
        SourceObject, on_delete=models.SET_NULL, null=True, blank=True, related_name="shape_recipes"
    )

    class Meta:
        verbose_name = "shape recipe"
        verbose_name_plural = "③ Shapes · Recipes"
        ordering = ["operation_uid"]

    def __str__(self) -> str:
        return f"{self.shape_hash} (uid={self.operation_uid})"


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
    fluid_color = models.ForeignKey(FluidColor, on_delete=models.SET_NULL, null=True, blank=True, related_name="slots")
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


class LazyLocalizedTextRef(models.Model):
    """Normalized Core.Localization.LazyLocalizedText from export snapshots."""

    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(
        ImportBatch, on_delete=models.CASCADE, related_name="lazy_localized_text_refs"
    )
    message_key = models.CharField(max_length=512, blank=True, default="", db_index=True)
    lazy_text_type = models.CharField(max_length=128, blank=True, default="")
    placeholder_resolver_type = models.CharField(max_length=128, blank=True, default="")
    is_cycle_reference = models.BooleanField(default=False)
    cycle_reference = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        verbose_name = "lazy localized text"
        verbose_name_plural = "⑧ L10n · Lazy text refs"

    def __str__(self) -> str:
        if self.message_key:
            return self.message_key
        return self.cycle_reference or self.canonical_id


class LazyLocalizedPlaceholderReplacement(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    lazy_text = models.ForeignKey(
        LazyLocalizedTextRef, on_delete=models.CASCADE, related_name="placeholder_replacements"
    )
    replacement_key = models.CharField(max_length=255)
    value_kind = models.CharField(max_length=64, blank=True, default="")
    nested_message_key = models.CharField(max_length=512, blank=True, default="")
    value_preview = models.TextField(blank=True, default="")
    order_index = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "lazy localized placeholder"
        verbose_name_plural = "⑧ L10n · Placeholder replacements"
        ordering = ["order_index", "replacement_key"]
        constraints = [
            models.UniqueConstraint(
                fields=["lazy_text", "replacement_key"],
                name="uq_lazy_placeholder_key",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.replacement_key} → {self.nested_message_key or self.value_kind}"


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


class SimulationSystemEntry(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="simulation_entries")
    source_stable_id = models.CharField(max_length=64)
    simulation_kind_key = models.CharField(max_length=128, db_index=True)
    system_family = models.CharField(max_length=32, blank=True, default="")
    parameter_profile = models.CharField(max_length=32, blank=True, default="")
    clr_type_audit = models.TextField()
    display_name_key = models.CharField(max_length=512, blank=True, default="")
    source_row_index = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["import_batch", "source_row_index"],
                name="uq_sim_entry_batch_row",
            ),
        ]
        verbose_name = "simulation system entry"
        verbose_name_plural = "⑥ Simulation · System entries"

    def __str__(self) -> str:
        return f"{self.simulation_kind_key} #{self.source_row_index}"


class SimulationFactoryStub(models.Model):
    simulation_entry = models.OneToOneField(
        SimulationSystemEntry, on_delete=models.CASCADE, related_name="factory_stub"
    )
    factory_type_name = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        verbose_name = "simulation factory stub"
        verbose_name_plural = "⑥ Simulation · Factory stubs"

    def __str__(self) -> str:
        return self.factory_type_name or str(self.simulation_entry)


class GlobalBeltSpeedPolicy(models.Model):
    import_batch = models.OneToOneField(
        ImportBatch, on_delete=models.CASCADE, related_name="belt_speed_policy"
    )
    base_speed = models.CharField(max_length=64, blank=True, default="")
    research_upgrade = models.ForeignKey(
        ResearchUpgrade, on_delete=models.SET_NULL, null=True, blank=True, related_name="belt_policies"
    )
    steps_per_tick = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "global belt speed policy"
        verbose_name_plural = "⑥ Simulation · Belt speed policy"

    def __str__(self) -> str:
        return f"belt:{self.base_speed}"


class SimulationRuntimeAudit(models.Model):
    """Audit-only: heavy converter/runtime capture (JSON allowed here only)."""

    simulation_entry = models.OneToOneField(
        SimulationSystemEntry, on_delete=models.CASCADE, related_name="runtime_audit"
    )
    audit_blob = models.JSONField(default=dict)

    class Meta:
        verbose_name = "simulation runtime audit"
        verbose_name_plural = "⑥ Simulation · Runtime audit"

    def __str__(self) -> str:
        return f"audit:{self.simulation_entry}"


class ToolbarNodeKind(models.TextChoices):
    ROOT = "root", "Root"
    FOLDER = "folder", "Folder / category"
    GROUP = "group", "Group"
    SEPARATOR = "separator", "Separator"
    ACTION = "action", "Action"


class ToolbarTreeNode(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="toolbar_tree_nodes")
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
    source_row_index = models.PositiveIntegerField()

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
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="toolbar_elements")
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


class ClrTypeRegistryEntry(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="clr_types")
    type_name = models.CharField(max_length=512)
    assembly_name = models.CharField(max_length=512)
    source_stable_id = models.CharField(max_length=64, blank=True, default="")
    is_compiler_generated = models.BooleanField(default=False)
    source_row_index = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["type_name", "assembly_name"],
                name="uq_clr_type_assembly",
            ),
        ]
        verbose_name = "CLR type entry"
        verbose_name_plural = "⑨ Reflection · CLR types"

    def __str__(self) -> str:
        return f"{self.type_name} ({self.assembly_name})"


class LocalizedMessage(models.Model):
    canonical_id = models.CharField(max_length=255, unique=True)
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="localized_messages")
    message_key = models.CharField(max_length=512)
    locale_code = models.CharField(max_length=16, default="en")
    message_text = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["message_key", "locale_code"],
                name="uq_localized_message",
            ),
        ]
        verbose_name = "localized message"
        verbose_name_plural = "⑧ L10n · Messages"

    def __str__(self) -> str:
        return f"{self.message_key} [{self.locale_code}]"
