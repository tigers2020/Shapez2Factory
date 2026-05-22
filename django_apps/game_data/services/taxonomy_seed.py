"""Rebuild admin browse taxonomy from model verbose_name_plural metadata."""

from __future__ import annotations

import re

from django.apps import apps

from django_apps.game_data.models.taxonomy import GameDataNamespace, GameDataSection

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
        "game_data.ShapeRecipeSourceAppearance",  # 0023: inline under ShapeRecipe browse
        "game_data.ShapeRecipeLayer",
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

_SECTION_RE = re.compile(r"^[①②③④⑤⑥⑦⑧⑨⑩⑪]+\s+([^·]+)\s*·\s*(.+)$")


def _slugify(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_") or "misc"


def seed_game_data_taxonomy() -> tuple[int, int]:
    """Create or update namespace/section rows for admin browse navigation."""

    ns_order = 0
    seen_ns: dict[str, GameDataNamespace] = {}
    sections_upserted = 0

    for model in apps.get_app_config("game_data").get_models():
        plural = str(model._meta.verbose_name_plural or "")
        match = _SECTION_RE.match(plural)
        if not match:
            continue
        ns_label, sec_label = match.group(1).strip(), match.group(2).strip()
        ns_code = _slugify(ns_label)
        sec_code = _slugify(sec_label)
        if ns_code not in seen_ns:
            ns_order += 1
            namespace, _ = GameDataNamespace.objects.update_or_create(
                code=ns_code,
                defaults={"label": ns_label, "order": ns_order},
            )
            seen_ns[ns_code] = namespace
        namespace = seen_ns[ns_code]
        order = GameDataSection.objects.filter(namespace=namespace).count()
        _, created = GameDataSection.objects.update_or_create(
            namespace=namespace,
            code=sec_code,
            defaults={
                "label": sec_label,
                "order": order,
                "django_model_label": f"game_data.{model.__name__}",
            },
        )
        if created:
            sections_upserted += 1

    return len(seen_ns), sections_upserted


def prune_subtable_taxonomy_sections() -> int:
    """Drop browse sections for sub-tables (migrations 0020 + 0023 prune parity)."""

    deleted, _ = GameDataSection.objects.filter(
        django_model_label__in=SUBTABLE_MODEL_LABELS,
    ).delete()
    return deleted


def rebuild_game_data_taxonomy() -> dict[str, int]:
    """Seed namespaces/sections, then prune sub-table section rows."""

    namespace_count, sections_upserted = seed_game_data_taxonomy()
    pruned = prune_subtable_taxonomy_sections()
    return {
        "namespaces": namespace_count,
        "sections_new": sections_upserted,
        "sections_pruned": pruned,
        "sections_remaining": GameDataSection.objects.count(),
    }
