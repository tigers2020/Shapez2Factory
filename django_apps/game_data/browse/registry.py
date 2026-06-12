"""Bounded-context browse registry: taxonomy → admin targets and aggregate roots."""

# ruff: noqa: E501

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.apps import apps
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.db.models import Model
from django.urls import reverse

if TYPE_CHECKING:
    from django.contrib.admin import ModelAdmin

    from django_apps.game_data.models.taxonomy import GameDataSection


@dataclass(frozen=True)
class RelatedChangelistSpec:
    """Sub-table reached via filtered changelist (no direct FK inline)."""

    model_label: str
    description: str


@dataclass(frozen=True)
class AggregateRootSpec:
    """Expected parent-centered admin navigation for an aggregate root model."""

    model_label: str
    inline_class_names: frozenset[str]
    related_changelists: tuple[RelatedChangelistSpec, ...] = ()


# Contract: aggregate-root ModelAdmin must expose these inlines / related changelists.
AGGREGATE_ROOT_SPECS: tuple[AggregateRootSpec, ...] = (
    AggregateRootSpec(
        model_label="game_data.BuildingGroup",
        inline_class_names=frozenset(
            {
                "BuildingGroupMemberInline",
                "BuildingPlacementRuleInline",
                "BuildingLocalizationOverlayInline",
                "BuildingSimulationSettingInline",
            }
        ),
    ),
    AggregateRootSpec(
        model_label="game_data.BuildingVariant",
        inline_class_names=frozenset(
            {
                "BuildingConnectorInline",
                "BuildingFootprintTileInline",
                "TransportBuildingRegistryInline",
            }
        ),
    ),
    AggregateRootSpec(
        model_label="game_data.SimulationSystem",
        inline_class_names=frozenset(
            {
                "SimulationSystemParameterOccurrenceInline",
                "ConnectableSimulationSystemInline",
                "SimulationRuntimeAuditIssueInline",
                "SimulationTypeInline",
                "SimulationStateTypeInline",
                "SimulationBuffableSpeedInline",
                "SimulationMultipleBeltSpeedInline",
            }
        ),
        related_changelists=(
            RelatedChangelistSpec(
                model_label="game_data.SimulationClrProvenance",
                description="CLR provenance rows matched by import batch + source_stable_id",
            ),
        ),
    ),
    AggregateRootSpec(
        model_label="game_data.ToolbarTreeNode",
        inline_class_names=frozenset(
            {
                "ToolbarTreeNodeChildInline",
                "ToolbarElementInline",
            }
        ),
        related_changelists=(
            RelatedChangelistSpec(
                model_label="game_data.ToolbarBuildingPlacement",
                description="Building placements via toolbar element",
            ),
            RelatedChangelistSpec(
                model_label="game_data.ToolbarIslandPlacement",
                description="Island placements via toolbar element",
            ),
        ),
    ),
    AggregateRootSpec(
        model_label="game_data.ResearchMilestone",
        inline_class_names=frozenset({"ResearchUnlockCostInline"}),
        related_changelists=(
            RelatedChangelistSpec(
                model_label="game_data.ResearchPrerequisite",
                description="Prerequisites filtered by parent_kind + parent_key",
            ),
        ),
    ),
)

# Sub-tables: no standalone browse section (see migration 0019 prune + aggregate inlines).
SUBTABLE_MODEL_LABELS: frozenset[str] = frozenset(
    {
        "game_data.BuildingConnector",
        "game_data.BuildingFootprintTile",
        "game_data.BuildingGroupMember",
        "game_data.BuildingLocalizationOverlay",
        "game_data.BuildingPlacementRule",
        "game_data.BuildingSimulationSetting",
        "game_data.LazyLocalizedPlaceholderReplacement",
        "game_data.ShapeQuadrantSlot",
        "game_data.ShapeRecipeLayer",
        "game_data.ShapeRecipeSourceAppearance",
        "game_data.SimulationChunkBounds",
        "game_data.SimulationConnector",
        "game_data.SimulationConnectorProperty",
        "game_data.SimulationLaneDefinition",
        "game_data.SimulationLaneRuntimeState",
        "game_data.SimulationStateType",
        "game_data.SimulationTileBounds",
        "game_data.SimulationType",
    }
)


def resolve_model(model_label: str) -> type[Model]:
    app_label, model_name = model_label.split(".", 1)
    return apps.get_model(app_label, model_name)


def admin_inline_class_names(model_admin: ModelAdmin[Model]) -> frozenset[str]:
    names: list[str] = []
    for inline in model_admin.inlines:
        if isinstance(inline, type):
            names.append(inline.__name__)
        else:
            names.append(inline.__class__.__name__)
    return frozenset(names)


def changelist_url_for_model(
    model: type[Model],
    *,
    site: AdminSite | None = None,
) -> str | None:
    site = site or admin.site
    model_admin = site._registry.get(model)
    if model_admin is None:
        return None
    return reverse(
        f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist",
        current_app=site.name,
    )


def row_count_for_model(model: type[Model]) -> int:
    return model._default_manager.count()


@dataclass(frozen=True)
class BrowseSectionEntry:
    section_id: int
    namespace_code: str
    namespace_label: str
    section_code: str
    section_label: str
    model_label: str
    changelist_url: str | None
    row_count: int
    is_aggregate_root: bool
    missing_admin: bool


@dataclass(frozen=True)
class BrowseNamespaceGroup:
    code: str
    label: str
    order: int
    sections: tuple[BrowseSectionEntry, ...]


def aggregate_root_model_labels() -> frozenset[str]:
    return frozenset(spec.model_label for spec in AGGREGATE_ROOT_SPECS)


def validate_section_admin_targets(
    *,
    site: AdminSite | None = None,
) -> list[str]:
    """Return human-readable errors when taxonomy sections lack admin browse targets."""
    from django_apps.game_data.models.taxonomy import GameDataSection

    site = site or admin.site
    errors: list[str] = []
    for section in GameDataSection.objects.select_related("namespace").order_by(
        "namespace__order", "order"
    ):
        label = section.django_model_label.strip()
        if not label:
            errors.append(f"Section {section!s} has empty django_model_label")
            continue
        if label in SUBTABLE_MODEL_LABELS:
            continue
        try:
            model = resolve_model(label)
        except LookupError:
            errors.append(f"Section {section!s}: unknown model {label!r}")
            continue
        if changelist_url_for_model(model, site=site) is None:
            errors.append(f"Section {section!s}: model {label} not registered in admin")
    return errors


def build_browse_groups(*, site: AdminSite | None = None) -> tuple[BrowseNamespaceGroup, ...]:
    from django_apps.game_data.models.taxonomy import GameDataNamespace

    site = site or admin.site
    roots = aggregate_root_model_labels()
    groups: list[BrowseNamespaceGroup] = []

    for namespace in GameDataNamespace.objects.prefetch_related("sections").order_by(
        "order", "code"
    ):
        entries: list[BrowseSectionEntry] = []
        for section in section_qs_sorted(namespace):
            label = section.django_model_label.strip()
            url: str | None = None
            count = 0
            missing = False
            if label:
                try:
                    model = resolve_model(label)
                    url = changelist_url_for_model(model, site=site)
                    count = row_count_for_model(model)
                    missing = url is None and label not in SUBTABLE_MODEL_LABELS
                except LookupError:
                    missing = True
            else:
                missing = True
            entries.append(
                BrowseSectionEntry(
                    section_id=section.pk,
                    namespace_code=namespace.code,
                    namespace_label=namespace.label,
                    section_code=section.code,
                    section_label=section.label,
                    model_label=label,
                    changelist_url=url,
                    row_count=count,
                    is_aggregate_root=label in roots,
                    missing_admin=missing,
                )
            )
        groups.append(
            BrowseNamespaceGroup(
                code=namespace.code,
                label=namespace.label,
                order=namespace.order,
                sections=tuple(entries),
            )
        )
    return tuple(groups)


def section_qs_sorted(namespace: object) -> list[GameDataSection]:
    return list(namespace.sections.order_by("order", "code"))


def related_changelist_url(spec: RelatedChangelistSpec, parent_obj: Model) -> str | None:
    """Build a filtered admin changelist URL for a sub-table without a direct parent FK inline."""
    from urllib.parse import urlencode

    model = resolve_model(spec.model_label)
    base = changelist_url_for_model(model)
    if base is None:
        return None
    params: dict[str, str] = {}
    label = spec.model_label
    if label == "game_data.SimulationClrProvenance":
        params = {
            "import_batch__id__exact": str(parent_obj.import_batch_id),
            "source_stable_id": parent_obj.source_stable_id,
        }
    elif label == "game_data.ToolbarBuildingPlacement":
        params = {"toolbar_element__tree_node__id__exact": str(parent_obj.pk)}
    elif label == "game_data.ToolbarIslandPlacement":
        params = {"toolbar_element__tree_node__id__exact": str(parent_obj.pk)}
    elif label == "game_data.ResearchPrerequisite":
        params = {
            "parent_kind__exact": "milestone",
            "parent_key__exact": parent_obj.node_key,
        }
    else:
        return base
    return f"{base}?{urlencode(params)}"


def validate_aggregate_root_inlines(
    *,
    site: AdminSite | None = None,
) -> list[str]:
    site = site or admin.site
    errors: list[str] = []
    for spec in AGGREGATE_ROOT_SPECS:
        model = resolve_model(spec.model_label)
        model_admin = site._registry.get(model)
        if model_admin is None:
            errors.append(f"{spec.model_label}: not registered in admin")
            continue
        present = admin_inline_class_names(model_admin)
        missing = spec.inline_class_names - present
        if missing:
            errors.append(f"{spec.model_label}: missing inlines {sorted(missing)}")
        extra_related = {r.model_label for r in spec.related_changelists}
        if extra_related and not hasattr(model_admin, "game_data_related_changelists"):
            errors.append(f"{spec.model_label}: missing game_data_related_changelists hook")
    return errors
