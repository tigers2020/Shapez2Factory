"""Django admin for game_data (browse-first import domain)."""

# ruff: noqa: E501

from __future__ import annotations

from typing import Any, ClassVar

from django.contrib import admin
from django.http import HttpRequest
from django.utils.html import format_html

from django_apps.game_data import models as m
from django_apps.game_data.browse.registry import (
    AGGREGATE_ROOT_SPECS,
    AggregateRootSpec,
    RelatedChangelistSpec,
    related_changelist_url,
)


class GameDataReadOnlyAdminMixin:
    """Rows come from import_game_data; admin is browse-first."""

    def has_add_permission(self, _request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, _obj: Any | None = None) -> bool:
        return bool(request.user.is_staff)

    def has_delete_permission(self, request: HttpRequest, _obj: Any | None = None) -> bool:
        return bool(request.user.is_superuser)


class GameDataAggregateAdminMixin:
    """Aggregate roots expose child inlines plus filtered changelist links for loose FKs."""

    game_data_related_changelists: ClassVar[tuple[RelatedChangelistSpec, ...]] = ()

    @admin.display(description="Related sub-tables")
    def related_subtable_links(self, obj: Any) -> str:
        if obj is None or not self.game_data_related_changelists:
            return "—"
        links = []
        for spec in self.game_data_related_changelists:
            url = related_changelist_url(spec, obj)
            if url:
                links.append(format_html('<a href="{}">{}</a>', url, spec.description))
        if not links:
            return "—"
        sep = format_html("<br>")
        combined = sep.join(links)
        return combined


def _aggregate_spec(model_label: str) -> AggregateRootSpec | None:
    for spec in AGGREGATE_ROOT_SPECS:
        if spec.model_label == model_label:
            return spec
    return None


class ImportBatchFilter(admin.SimpleListFilter):
    title = "import run"
    parameter_name = "import_batch"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> list[tuple[str, str]]:
        batches = m.ImportBatch.objects.order_by("-imported_at")[:20]
        return [(str(b.pk), str(b)) for b in batches]

    def queryset(self, request: HttpRequest, queryset: Any) -> Any:
        if self.value():
            return queryset.filter(import_batch_id=self.value())
        return queryset


# --- Inlines ---


class ArtifactChecksumInline(admin.TabularInline):
    model = m.ArtifactChecksum
    extra = 0
    can_delete = False
    fields = ("artifact_filename", "expected_sha256", "import_status", "is_incomplete")
    readonly_fields = fields
    ordering = ("artifact_filename",)


class ExportWarningInline(admin.TabularInline):
    model = m.ExportWarning
    extra = 0
    can_delete = False
    fields = ("warning_index", "message")
    readonly_fields = fields
    ordering = ("warning_index",)


class ExportIncompleteSectionInline(admin.TabularInline):
    model = m.ExportIncompleteSection
    extra = 0
    can_delete = False
    fields = ("section_code",)
    readonly_fields = fields


class BuildingConnectorInline(admin.TabularInline):
    model = m.BuildingConnector
    extra = 0
    can_delete = False
    fields = (
        "order_index",
        "connector_role",
        "tile_direction",
        "io_channel_type",
        "position_x",
        "position_y",
        "position_z",
    )
    readonly_fields = fields
    ordering = ("order_index",)


class BuildingFootprintTileInline(admin.TabularInline):
    model = m.BuildingFootprintTile
    extra = 0
    can_delete = False
    fields = ("order_index", "x", "y", "z")
    readonly_fields = fields
    ordering = ("order_index",)


class BuildingGroupMemberInline(admin.TabularInline):
    model = m.BuildingGroupMember
    extra = 0
    can_delete = False
    fields = ("order_index", "building_variant", "member_resolution", "internal_variant_name")
    readonly_fields = ("order_index", "member_resolution", "internal_variant_name")
    raw_id_fields = ("building_variant",)
    ordering = ("order_index",)


class ShapeRecipeLayerInline(admin.TabularInline):
    model = m.ShapeRecipeLayer
    extra = 0
    can_delete = False
    fields = ("layer_index", "hash_segment", "sort_order")
    readonly_fields = fields
    ordering = ("layer_index",)


class ShapeRecipeSourceAppearanceInline(admin.TabularInline):
    model = m.ShapeRecipeSourceAppearance
    extra = 0
    can_delete = False
    fields = ("catalog_source", "artifact_filename", "source_row_index", "source_object")
    readonly_fields = fields
    raw_id_fields = ("source_object",)
    ordering = ("artifact_filename", "source_row_index")


class ResearchUnlockCostInline(admin.TabularInline):
    model = m.ResearchUnlockCost
    extra = 0
    can_delete = False
    fields = ("order_index", "shape_recipe", "amount", "parent_kind")
    readonly_fields = fields
    raw_id_fields = ("shape_recipe",)
    ordering = ("order_index",)
    fk_name = "milestone"


class BuildingPlacementRuleInline(admin.TabularInline):
    model = m.BuildingPlacementRule
    extra = 0
    can_delete = False
    fields = ("order_index", "rule_kind")
    readonly_fields = fields
    ordering = ("order_index",)


class BuildingLocalizationOverlayInline(admin.StackedInline):
    model = m.BuildingLocalizationOverlay
    extra = 0
    max_num = 1
    can_delete = False
    fields = ("title_key", "description_key", "lazy_text_namespace")
    readonly_fields = fields


class BuildingSimulationSettingInline(admin.StackedInline):
    model = m.BuildingSimulationSetting
    extra = 0
    max_num = 1
    can_delete = False
    fields = (
        "is_transport_building",
        "pipette_override_id",
        "show_stat_belt_processing_time",
        "show_stat_buildings_per_full_belt",
        "show_in_speed_overview",
    )
    readonly_fields = fields


class TransportBuildingRegistryInline(admin.TabularInline):
    model = m.TransportBuildingRegistry
    extra = 0
    can_delete = False
    fields = ("transport_kind", "transport_category", "display_name_key")
    readonly_fields = fields


class SimulationSystemParameterOccurrenceInline(admin.TabularInline):
    model = m.SimulationSystemParameterOccurrence
    extra = 0
    can_delete = False
    fields = ("parameter_key", "source_path")
    readonly_fields = fields
    raw_id_fields = ("parameter_key",)


class ConnectableSimulationSystemInline(admin.TabularInline):
    model = m.ConnectableSimulation
    extra = 0
    can_delete = False
    fields = (
        "connectable_key",
        "attachment_index",
        "building_variant",
        "num_connectors",
        "num_occupied_tiles",
    )
    readonly_fields = fields
    raw_id_fields = ("building_variant",)


class SimulationRuntimeAuditIssueInline(admin.TabularInline):
    model = m.SimulationRuntimeAuditIssue
    extra = 0
    can_delete = False
    fields = ("issue_code", "severity", "message", "source_path")
    readonly_fields = fields


class SimulationTypeInline(admin.StackedInline):
    model = m.SimulationType
    extra = 0
    max_num = 1
    can_delete = False
    fields = ("simulation_class", "assembly_name")
    readonly_fields = fields


class SimulationStateTypeInline(admin.StackedInline):
    model = m.SimulationStateType
    extra = 0
    max_num = 1
    can_delete = False
    fields = ("state_class", "assembly_name")
    readonly_fields = fields


class SimulationBuffableSpeedInline(admin.TabularInline):
    model = m.SimulationBuffableSpeed
    extra = 0
    can_delete = False
    fields = ("parameter_name", "base_speed", "steps_per_tick", "dump_type")
    readonly_fields = fields


class SimulationMultipleBeltSpeedInline(admin.TabularInline):
    model = m.SimulationMultipleBeltSpeed
    extra = 0
    can_delete = False
    fields = ("parameter_name", "multiplier", "steps_per_tick", "cycle_ref_type")
    readonly_fields = fields


class ToolbarTreeNodeChildInline(admin.TabularInline):
    model = m.ToolbarTreeNode
    fk_name = "parent"
    extra = 0
    can_delete = False
    fields = ("child_index", "order_index", "node_kind", "internal_name", "localized_title_key")
    readonly_fields = fields
    ordering = ("child_index",)


class ToolbarElementInline(admin.StackedInline):
    model = m.ToolbarElement
    extra = 0
    max_num = 1
    can_delete = False
    fields = ("element_kind", "stable_key", "display_name", "section_index")
    readonly_fields = fields


def _related_for(model_label: str) -> tuple[RelatedChangelistSpec, ...]:
    spec = _aggregate_spec(model_label)
    return spec.related_changelists if spec else ()


# --- Import ---


@admin.register(m.ImportBatch)
class ImportBatchAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("batch_name", "game_version", "dump_mod_version", "imported_at", "hash_short")
    list_filter = ("source_method", "dump_schema_version")
    search_fields = ("batch_name", "manifest_self_hash", "game_version")
    readonly_fields = (
        "batch_name",
        "manifest_self_hash",
        "game_version",
        "unity_version",
        "dump_mod_version",
        "dump_schema_version",
        "dump_timestamp_utc",
        "source_method",
        "imported_at",
    )
    inlines = (ArtifactChecksumInline, ExportWarningInline, ExportIncompleteSectionInline)

    @staticmethod
    def hash_short(obj: m.ImportBatch) -> str:
        h = obj.manifest_self_hash or ""
        return h[:20] + "…" if len(h) > 20 else h

    hash_short.short_description = "Manifest hash"


@admin.register(m.ArtifactChecksum)
class ArtifactChecksumAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("artifact_filename", "import_batch", "import_status", "is_incomplete")
    list_filter = (ImportBatchFilter, "import_status", "is_incomplete")
    search_fields = ("artifact_filename", "expected_sha256")
    raw_id_fields = ("import_batch",)


@admin.register(m.ExportWarning)
class ExportWarningAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("import_batch", "warning_index", "message_preview")
    list_filter = (ImportBatchFilter,)
    raw_id_fields = ("import_batch",)

    @staticmethod
    def message_preview(obj: m.ExportWarning) -> str:
        msg = obj.message or ""
        return msg[:80] + "…" if len(msg) > 80 else msg

    message_preview.short_description = "Message"


@admin.register(m.ExportIncompleteSection)
class ExportIncompleteSectionAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("import_batch", "section_code")
    list_filter = (ImportBatchFilter, "section_code")
    raw_id_fields = ("import_batch",)


@admin.register(m.LocalizationExportStatus)
class LocalizationExportStatusAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("import_batch", "is_empty", "is_incomplete", "expected_hash")
    list_filter = ("is_empty", "is_incomplete")
    raw_id_fields = ("import_batch",)


@admin.register(m.SourceObject)
class SourceObjectAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("source_file", "source_row_index", "import_batch", "dump_source_type")
    list_filter = (ImportBatchFilter, "source_file")
    search_fields = ("source_stable_id", "dump_source_type")
    raw_id_fields = ("import_batch",)


@admin.register(m.UnknownProperty)
class UnknownPropertyAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "owner_model",
        "key",
        "reason_code",
        "classification",
        "value_type",
        "import_batch",
        "owner_key",
    )
    list_filter = (ImportBatchFilter, "owner_model", "reason_code", "classification", "value_type")
    search_fields = ("owner_key", "key", "json_path")
    raw_id_fields = ("import_batch",)


# --- Assets ---


@admin.register(m.GameContentAsset)
class GameContentAssetAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("content_path", "content_kind", "import_batch", "canonical_id_short")
    list_filter = (ImportBatchFilter, "content_kind")
    search_fields = ("content_path", "canonical_id", "display_name_key", "source_stable_id")
    raw_id_fields = ("import_batch",)

    @staticmethod
    def canonical_id_short(obj: m.GameContentAsset) -> str:
        cid = obj.canonical_id or ""
        return cid[:40] + "…" if len(cid) > 40 else cid

    canonical_id_short.short_description = "Canonical ID"


@admin.register(m.AssetMetaReference)
class AssetMetaReferenceAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("logical_path", "content_asset", "meta_stable_id", "import_batch")
    list_filter = (ImportBatchFilter,)
    search_fields = ("logical_path", "meta_stable_id", "canonical_id")
    raw_id_fields = ("import_batch", "content_asset")


# --- Shapes & fluids ---


@admin.register(m.FluidColor)
class FluidColorAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("color_name", "fluid_kind", "import_batch")
    list_filter = (ImportBatchFilter, "fluid_kind")
    search_fields = ("color_name", "canonical_id")
    raw_id_fields = ("import_batch",)


@admin.register(m.ShapeComponentKind)
class ShapeComponentKindAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("component_key", "catalog_shape_code", "display_label")
    search_fields = ("component_key", "canonical_id")


@admin.register(m.ShapeRecipe)
class ShapeRecipeAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "shape_hash",
        "operation_uid",
        "layer_count",
        "catalog_appearances_summary",
        "import_batch",
    )
    list_filter = (ImportBatchFilter, "source_appearances__catalog_source", "layer_count")
    search_fields = ("shape_hash", "canonical_id", "operation_uid")
    raw_id_fields = ("import_batch", "source_object")
    inlines = (ShapeRecipeSourceAppearanceInline, ShapeRecipeLayerInline)

    @admin.display(description="Catalog appearances")
    def catalog_appearances_summary(self, obj: m.ShapeRecipe) -> str:
        labels = sorted(obj.source_appearances.values_list("catalog_source", flat=True).distinct())
        return ",".join(labels) if labels else "—"


@admin.register(m.ShapeRecipeLayer)
class ShapeRecipeLayerAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("shape_recipe", "layer_index", "hash_segment")
    list_filter = ("layer_index",)
    raw_id_fields = ("shape_recipe",)
    search_fields = ("hash_segment", "canonical_id")


@admin.register(m.ShapeQuadrantSlot)
class ShapeQuadrantSlotAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "layer",
        "quadrant_index",
        "shape_component_kind",
        "fluid_color",
        "is_empty_shape",
    )
    raw_id_fields = ("layer", "shape_component_kind", "fluid_color")


# --- Buildings ---


@admin.register(m.BuildingVariant)
class BuildingVariantAdmin(
    GameDataAggregateAdminMixin, GameDataReadOnlyAdminMixin, admin.ModelAdmin
):
    list_display = (
        "internal_name",
        "connector_count",
        "size_x",
        "size_y",
        "is_mirrored",
        "import_batch",
    )
    list_filter = (ImportBatchFilter, "is_mirrored")
    search_fields = ("internal_name", "canonical_id", "display_name_key")
    raw_id_fields = ("import_batch",)
    inlines = (
        BuildingConnectorInline,
        BuildingFootprintTileInline,
        TransportBuildingRegistryInline,
    )


@admin.register(m.BuildingConnector)
class BuildingConnectorAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("building_variant", "order_index", "connector_role", "io_channel_type")
    list_filter = ("connector_role", "io_channel_type")
    raw_id_fields = ("building_variant",)
    search_fields = ("canonical_id",)


@admin.register(m.BuildingFootprintTile)
class BuildingFootprintTileAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("building_variant", "order_index", "x", "y", "z")
    raw_id_fields = ("building_variant",)


@admin.register(m.BuildingGroup)
class BuildingGroupAdmin(GameDataAggregateAdminMixin, GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "group_key",
        "display_profile",
        "is_transport_building",
        "player_buildable",
        "import_batch",
    )
    list_filter = (
        ImportBatchFilter,
        "display_profile",
        "is_transport_building",
        "player_buildable",
    )
    search_fields = ("group_key", "canonical_id", "display_name_key")
    raw_id_fields = ("import_batch",)
    inlines = (
        BuildingGroupMemberInline,
        BuildingPlacementRuleInline,
        BuildingLocalizationOverlayInline,
        BuildingSimulationSettingInline,
    )


@admin.register(m.BuildingLocalizationOverlay)
class BuildingLocalizationOverlayAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("building_group", "title_key", "lazy_text_namespace")
    raw_id_fields = ("building_group",)
    search_fields = ("title_key", "description_key")


@admin.register(m.BuildingSimulationSetting)
class BuildingSimulationSettingAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("building_group", "is_transport_building", "show_in_speed_overview")
    list_filter = ("is_transport_building", "show_in_speed_overview")
    raw_id_fields = ("building_group",)


@admin.register(m.BuildingGroupMember)
class BuildingGroupMemberAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("building_group", "order_index", "building_variant", "member_resolution")
    list_filter = ("member_resolution",)
    raw_id_fields = ("building_group", "building_variant")


@admin.register(m.BuildingPlacementRule)
class BuildingPlacementRuleAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("building_group", "order_index", "rule_kind")
    list_filter = ("rule_kind",)
    raw_id_fields = ("building_group",)


@admin.register(m.TransportBuildingRegistry)
class TransportBuildingRegistryAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("transport_kind", "transport_category", "building_variant", "import_batch")
    list_filter = (ImportBatchFilter, "transport_category")
    search_fields = ("transport_kind", "canonical_id")
    raw_id_fields = ("import_batch", "building_variant")


# --- Research ---


@admin.register(m.ResearchUpgrade)
class ResearchUpgradeAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("upgrade_key", "import_batch")
    list_filter = (ImportBatchFilter,)
    search_fields = ("upgrade_key", "canonical_id")
    raw_id_fields = ("import_batch",)


@admin.register(m.ResearchMechanic)
class ResearchMechanicAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("mechanic_key", "import_batch")
    list_filter = (ImportBatchFilter,)
    search_fields = ("mechanic_key",)
    raw_id_fields = ("import_batch",)


class LazyLocalizedPlaceholderReplacementInline(admin.TabularInline):
    model = m.LazyLocalizedPlaceholderReplacement
    extra = 0
    readonly_fields = (
        "replacement_key",
        "value_kind",
        "nested_message_key",
        "value_preview",
        "order_index",
    )
    can_delete = False

    def has_add_permission(self, request, obj=None):  # noqa: ANN001, ARG002
        return False


@admin.register(m.LazyLocalizedTextRef)
class LazyLocalizedTextRefAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "message_key",
        "lazy_text_type",
        "is_cycle_reference",
        "import_batch",
    )
    list_filter = (ImportBatchFilter, "is_cycle_reference")
    search_fields = ("message_key", "cycle_reference", "canonical_id")
    raw_id_fields = ("import_batch",)
    inlines = (LazyLocalizedPlaceholderReplacementInline,)


@admin.register(m.ResearchMilestone)
class ResearchMilestoneAdmin(
    GameDataAggregateAdminMixin, GameDataReadOnlyAdminMixin, admin.ModelAdmin
):
    list_display = ("node_key", "title_message_key", "import_batch")
    list_filter = (ImportBatchFilter,)
    search_fields = ("node_key", "canonical_id", "title_lazy__message_key")
    raw_id_fields = ("import_batch", "title_lazy", "description_lazy")
    readonly_fields = ("related_subtable_links",)
    inlines = (ResearchUnlockCostInline,)
    game_data_related_changelists = _related_for("game_data.ResearchMilestone")

    @admin.display(description="Title key")
    def title_message_key(self, obj: m.ResearchMilestone) -> str:
        if obj.title_lazy_id is None:
            return ""
        return obj.title_lazy.message_key


@admin.register(m.ResearchSideQuest)
class ResearchSideQuestAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("node_key", "title_message_key", "description_message_key", "import_batch")
    list_filter = (ImportBatchFilter,)
    search_fields = ("node_key", "title_lazy__message_key", "description_lazy__message_key")
    raw_id_fields = ("import_batch", "title_lazy", "description_lazy")

    @admin.display(description="Title key")
    def title_message_key(self, obj: m.ResearchSideQuest) -> str:
        if obj.title_lazy_id is None:
            return ""
        return obj.title_lazy.message_key

    @admin.display(description="Description key")
    def description_message_key(self, obj: m.ResearchSideQuest) -> str:
        if obj.description_lazy_id is None:
            return ""
        return obj.description_lazy.message_key


@admin.register(m.ResearchSideUpgrade)
class ResearchSideUpgradeAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("node_key", "import_batch")
    list_filter = (ImportBatchFilter,)
    search_fields = ("node_key",)
    raw_id_fields = ("import_batch",)


@admin.register(m.ResearchUnlockCost)
class ResearchUnlockCostAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "parent_kind",
        "shape_recipe",
        "amount",
        "order_index",
        "milestone",
        "side_quest",
    )
    list_filter = ("parent_kind",)
    raw_id_fields = ("shape_recipe", "milestone", "side_quest")


@admin.register(m.ResearchPrerequisite)
class ResearchPrerequisiteAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("parent_kind", "parent_key", "required_upgrade", "required_mechanic")
    list_filter = ("parent_kind",)
    raw_id_fields = ("required_upgrade", "required_mechanic")


@admin.register(m.ResearchGlobalConfig)
class ResearchGlobalConfigAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("import_batch", "config_key")
    raw_id_fields = ("import_batch",)


# --- Simulation ---


class SimulationConnectorInline(admin.TabularInline):
    model = m.SimulationConnector
    extra = 0


class SimulationLaneDefinitionInline(admin.TabularInline):
    model = m.SimulationLaneDefinition
    extra = 0


@admin.register(m.SimulationProfile)
class SimulationProfileAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("profile_key", "profile_name")
    search_fields = ("profile_key", "profile_name")


@admin.register(m.SimulationSystem)
class SimulationSystemAdmin(
    GameDataAggregateAdminMixin, GameDataReadOnlyAdminMixin, admin.ModelAdmin
):
    list_display = (
        "system_family",
        "source_row_index",
        "source_stable_id",
        "profile",
        "canonical_id",
        "import_batch",
    )
    list_filter = (ImportBatchFilter, "profile", "system_family")
    search_fields = ("system_family", "canonical_id", "source_stable_id", "display_name_key")
    raw_id_fields = ("import_batch", "profile")
    readonly_fields = ("related_subtable_links",)
    inlines = (
        SimulationSystemParameterOccurrenceInline,
        ConnectableSimulationSystemInline,
        SimulationRuntimeAuditIssueInline,
        SimulationTypeInline,
        SimulationStateTypeInline,
        SimulationBuffableSpeedInline,
        SimulationMultipleBeltSpeedInline,
    )
    game_data_related_changelists = _related_for("game_data.SimulationSystem")


@admin.register(m.ConnectableSimulation)
class ConnectableSimulationAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "connectable_key",
        "attachment_index",
        "building_variant",
        "num_connectors",
        "simulation_system",
    )
    list_filter = (ImportBatchFilter,)
    inlines = (SimulationConnectorInline, SimulationLaneDefinitionInline)
    raw_id_fields = ("simulation_system", "building_variant")


@admin.register(m.SimulationSystemParameterKey)
class SimulationSystemParameterKeyAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("name", "classification", "occurrence_count")
    list_filter = ("classification",)
    search_fields = ("name",)


@admin.register(m.SimulationSystemParameterOccurrence)
class SimulationSystemParameterOccurrenceAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("simulation_system", "parameter_key", "source_path")
    list_filter = ("parameter_key__classification",)
    raw_id_fields = ("simulation_system", "parameter_key")


@admin.register(m.SimulationClrProvenance)
class SimulationClrProvenanceAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("source_row_index", "source_stable_id", "profile_signature", "import_batch")
    list_filter = (ImportBatchFilter, "profile_signature")
    search_fields = ("source_stable_id", "clr_type_string")
    raw_id_fields = ("import_batch",)


@admin.register(m.SimulationBuffableSpeed)
class SimulationBuffableSpeedAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "parameter_name",
        "base_speed",
        "steps_per_tick",
        "dump_type",
        "research_upgrade",
        "simulation_system",
    )
    list_filter = ("parameter_name", "dump_type")
    raw_id_fields = ("simulation_system", "research_upgrade")


@admin.register(m.SimulationMultipleBeltSpeed)
class SimulationMultipleBeltSpeedAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "parameter_name",
        "cycle_ref_type",
        "multiplier",
        "steps_per_tick",
        "buffable_base",
        "simulation_system",
    )
    list_filter = ("dump_type",)
    raw_id_fields = ("simulation_system", "buffable_base")


@admin.register(m.GlobalBeltSpeedPolicy)
class GlobalBeltSpeedPolicyAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "import_batch",
        "base_speed",
        "research_upgrade",
        "steps_per_tick",
        "simulation_system",
    )
    raw_id_fields = ("import_batch", "research_upgrade", "simulation_system")


@admin.register(m.SimulationRuntimeAuditIssue)
class SimulationRuntimeAuditIssueAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("simulation_system", "issue_code", "severity", "source_path")
    list_filter = ("issue_code", "severity")
    raw_id_fields = ("simulation_system",)


@admin.register(m.GameDataNamespace)
class GameDataNamespaceAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "label", "order")
    ordering = ("order", "code")


@admin.register(m.GameDataSection)
class GameDataSectionAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("namespace", "code", "label", "django_model_label", "order")
    list_filter = ("namespace",)
    ordering = ("namespace__order", "order")


@admin.register(m.GameDataReference)
class GameDataReferenceAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("import_batch", "ref_kind", "ref_value", "resolved", "from_source", "to_source")
    list_filter = ("ref_kind", "resolved", ImportBatchFilter)
    raw_id_fields = ("import_batch", "from_source", "to_source")


# --- Toolbar ---


@admin.register(m.ToolbarTreeNode)
class ToolbarTreeNodeAdmin(
    GameDataAggregateAdminMixin, GameDataReadOnlyAdminMixin, admin.ModelAdmin
):
    list_display = (
        "canonical_id_short",
        "source_stable_id_short",
        "parent_tree_path",
        "depth",
        "child_index",
        "order_index",
        "node_kind",
        "internal_name",
        "localized_title_key",
        "required_mechanic",
        "icon_content_asset",
        "tree_path_audit",
    )
    list_display_links = ("canonical_id_short",)
    list_filter = (ImportBatchFilter, "node_kind", "depth")
    search_fields = (
        "canonical_id",
        "source_stable_id",
        "internal_name",
        "localized_title_key",
        "tree_path",
    )
    raw_id_fields = ("import_batch", "parent")
    inlines = (ToolbarTreeNodeChildInline, ToolbarElementInline)
    game_data_related_changelists = _related_for("game_data.ToolbarTreeNode")
    readonly_fields = (
        "canonical_id",
        "source_stable_id",
        "parent",
        "depth",
        "child_index",
        "order_index",
        "node_kind",
        "internal_name",
        "localized_title_key",
        "icon_identifier",
        "tree_path",
        "import_batch",
        "source_row_index",
        "related_subtable_links",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "canonical_id",
                    "source_stable_id",
                    "parent",
                    "depth",
                    "child_index",
                    "order_index",
                    "node_kind",
                ),
            },
        ),
        (
            "Presentation",
            {
                "fields": (
                    "internal_name",
                    "localized_title_key",
                    "icon_identifier",
                ),
            },
        ),
        (
            "Audit",
            {
                "fields": ("tree_path", "import_batch", "source_row_index"),
                "description": "tree_path is flattened dump path; not unique identity.",
            },
        ),
    )

    @admin.display(description="Canonical ID", ordering="canonical_id")
    def canonical_id_short(self, obj: m.ToolbarTreeNode) -> str:
        cid = obj.canonical_id or ""
        return cid[:48] + "…" if len(cid) > 48 else cid

    @admin.display(description="Parent path", ordering="parent__tree_path")
    def parent_tree_path(self, obj: m.ToolbarTreeNode) -> str:
        if obj.parent_id is None:
            return "—"
        return obj.parent.tree_path or "—"

    @admin.display(description="Source stable ID", ordering="source_stable_id")
    def source_stable_id_short(self, obj: m.ToolbarTreeNode) -> str:
        sid = obj.source_stable_id or ""
        if len(sid) <= 16:
            return sid or "—"
        return sid[:8] + "…" + sid[-4:]

    @admin.display(description="Tree path (audit)", ordering="tree_path")
    def tree_path_audit(self, obj: m.ToolbarTreeNode) -> str:
        return obj.tree_path or "—"


@admin.register(m.ToolbarElement)
class ToolbarElementAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "canonical_id_short",
        "display_name",
        "element_kind",
        "stable_key",
        "section_index",
        "tree_path_audit",
        "import_batch",
    )
    list_display_links = ("canonical_id_short",)
    list_filter = (ImportBatchFilter, "element_kind")
    search_fields = (
        "canonical_id",
        "source_stable_id",
        "display_name",
        "stable_key",
        "tree_node__tree_path",
    )
    raw_id_fields = ("import_batch", "tree_node")

    @admin.display(description="Canonical ID", ordering="canonical_id")
    def canonical_id_short(self, obj: m.ToolbarElement) -> str:
        cid = obj.canonical_id or ""
        return cid[:48] + "…" if len(cid) > 48 else cid

    @admin.display(description="Tree path (audit)", ordering="tree_node__tree_path")
    def tree_path_audit(self, obj: m.ToolbarElement) -> str:
        return obj.tree_node.tree_path if obj.tree_node_id else "—"


@admin.register(m.ToolbarBuildingPlacement)
class ToolbarBuildingPlacementAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "toolbar_element",
        "building_variant",
        "building_definition_key",
        "icon_sprite_name",
    )
    list_filter = ("is_transport_building", "player_buildable")
    raw_id_fields = ("toolbar_element", "building_variant")
    search_fields = ("building_definition_key", "icon_sprite_name")


@admin.register(m.ToolbarIslandPlacement)
class ToolbarIslandPlacementAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "element_canonical_id",
        "island_group_name",
        "placer_id",
        "tree_path_audit",
        "toolbar_element",
    )
    list_display_links = ("element_canonical_id",)
    search_fields = (
        "island_group_name",
        "placer_id",
        "toolbar_element__canonical_id",
        "toolbar_element__tree_node__tree_path",
    )
    raw_id_fields = ("toolbar_element",)

    @admin.display(description="Element canonical ID", ordering="toolbar_element__canonical_id")
    def element_canonical_id(self, obj: m.ToolbarIslandPlacement) -> str:
        cid = obj.toolbar_element.canonical_id if obj.toolbar_element_id else ""
        return cid[:48] + "…" if len(cid) > 48 else (cid or "—")

    @admin.display(
        description="Tree path (audit)", ordering="toolbar_element__tree_node__tree_path"
    )
    def tree_path_audit(self, obj: m.ToolbarIslandPlacement) -> str:
        elem = obj.toolbar_element
        if elem is None or elem.tree_node_id is None:
            return "—"
        return elem.tree_node.tree_path


# --- Reflection & l10n ---


@admin.register(m.ClrTypeRegistryEntry)
class ClrTypeRegistryEntryAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("type_name", "assembly_name", "is_compiler_generated", "import_batch")
    list_filter = (ImportBatchFilter, "is_compiler_generated", "assembly_name")
    search_fields = ("type_name", "assembly_name", "canonical_id")
    raw_id_fields = ("import_batch",)


@admin.register(m.LocalizedMessage)
class LocalizedMessageAdmin(GameDataReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("message_key", "locale_code", "message_preview", "import_batch")
    list_filter = (ImportBatchFilter, "locale_code")
    search_fields = ("message_key", "message_text")
    raw_id_fields = ("import_batch",)

    @staticmethod
    def message_preview(obj: m.LocalizedMessage) -> str:
        text = obj.message_text or ""
        return text[:60] + "…" if len(text) > 60 else text

    message_preview.short_description = "Text"
