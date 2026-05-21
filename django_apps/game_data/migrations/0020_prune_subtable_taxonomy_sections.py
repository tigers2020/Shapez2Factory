# ruff: noqa: E501
"""Keep GameDataSection rows at entity/browse layer; drop pure sub-table sections."""

from django.db import migrations

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


def prune_subtable_sections(apps, schema_editor) -> None:
    Section = apps.get_model("game_data", "GameDataSection")
    Section.objects.filter(django_model_label__in=SUBTABLE_MODEL_LABELS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("game_data", "0019_simulation_runtime_audit_issue_unique"),
    ]

    operations = [
        migrations.RunPython(prune_subtable_sections, migrations.RunPython.noop),
    ]
