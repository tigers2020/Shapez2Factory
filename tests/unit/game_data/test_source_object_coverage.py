"""Domain roots must link to SourceObject after import."""

from __future__ import annotations

import pytest

from django_apps.game_data.models import (
    BuildingGroup,
    BuildingVariant,
    GameContentAsset,
    ImportBatch,
    ResearchMilestone,
    ShapeRecipe,
    SimulationSystem,
    ToolbarNodeKind,
    ToolbarTreeNode,
)
from tests.unit.game_data._assertions import assert_import_batch_has_no_missing_source_object

_SOURCE_OBJECT_MODELS: list[tuple[str, type]] = [
    ("shape_recipe", ShapeRecipe),
    ("building_variant", BuildingVariant),
    ("building_group", BuildingGroup),
    ("content_asset", GameContentAsset),
    ("simulation_system", SimulationSystem),
    ("toolbar_tree_node", ToolbarTreeNode),
]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "label,model",
    _SOURCE_OBJECT_MODELS,
    ids=[label for label, _ in _SOURCE_OBJECT_MODELS],
)
def test_domain_root_has_source_object(
    label: str,
    model: type,
    imported_batch_module: ImportBatch,
) -> None:
    if label == "toolbar_tree_node":
        assert ToolbarTreeNode.objects.filter(import_batch=imported_batch_module).exists()
    assert_import_batch_has_no_missing_source_object(model, imported_batch_module)


@pytest.mark.django_db
def test_research_milestones_have_source_object_when_present(
    imported_batch_module: ImportBatch,
) -> None:
    qs = ResearchMilestone.objects.filter(import_batch=imported_batch_module)
    if not qs.exists():
        pytest.skip("no milestones in dump")
    assert qs.filter(source_object__isnull=True).count() == 0


@pytest.mark.django_db
def test_source_object_auxiliary_path_on_toolbar(imported_batch_module: ImportBatch) -> None:
    node = (
        ToolbarTreeNode.objects.filter(
            import_batch=imported_batch_module,
            node_kind=ToolbarNodeKind.ACTION,
            source_object__isnull=False,
        )
        .select_related("source_object")
        .first()
    )
    assert node is not None
    assert node.source_object.source_path == node.tree_path
