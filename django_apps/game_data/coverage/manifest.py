"""Static path disposition registry (A1 coverage manifest)."""

from __future__ import annotations

from django_apps.game_data.coverage import reason_codes as rc
from django_apps.game_data.coverage.disposition import Disposition
from django_apps.game_data.coverage.simulation_paths import manifest_entries_from_rules

MANIFEST: dict[str, tuple[Disposition, str]] = {
    "items.json:definition_snapshot.Definition.Layers": (
        Disposition.PROMOTED,
        "ShapeRecipe tree",
    ),
    "items.json:catalog": (
        Disposition.CROSS_REF,
        "ShapeRecipeSourceAppearance",
    ),
    "shapes.json:definition_snapshot.Definition": (
        Disposition.PROMOTED,
        "ShapeRecipe + FULL appearance",
    ),
    "toolbar_entries.json:display_name_key": (
        Disposition.PROMOTED,
        "ToolbarTreeNode.tree_path",
    ),
    "toolbar_entries.json:Children": (
        Disposition.CROSS_REF,
        "flattened to row paths",
    ),
    "simulation_systems.json:ISimulationSystem": (
        Disposition.IGNORE_AUDIT,
        rc.RUNTIME_DELEGATE,
    ),
    "simulation_systems.json:SimulationFactory": (
        Disposition.IGNORE_AUDIT,
        rc.SIMULATION_FACTORY_STUB,
    ),
    "buildings.json:definition_snapshot.Assembly": (
        Disposition.IGNORE_AUDIT,
        rc.REFLECTION_METADATA,
    ),
    "buildings.json:PlacementRequirements": (
        Disposition.PROMOTED,
        "BuildingPlacementRule",
    ),
    "buildings.json:Definitions": (
        Disposition.PROMOTED,
        "BuildingGroupMember",
    ),
}
MANIFEST.update(manifest_entries_from_rules())
