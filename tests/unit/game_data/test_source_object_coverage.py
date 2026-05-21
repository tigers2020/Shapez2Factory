"""Domain roots must link to SourceObject after import."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.game_data.importers import GameDataImporter
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

REPO_ROOT = Path(__file__).resolve().parents[3]
GAME_DATA_DIR = REPO_ROOT / "documents" / "game_data"


@pytest.fixture
def game_data_dir() -> Path:
    if not (GAME_DATA_DIR / "manifest.json").is_file():
        pytest.skip("documents/game_data not present")
    return GAME_DATA_DIR


@pytest.fixture
def imported_batch(game_data_dir: Path) -> ImportBatch:
    GameDataImporter(game_data_dir).run()
    batch = ImportBatch.objects.order_by("-imported_at").first()
    assert batch is not None
    return batch


@pytest.mark.django_db
def test_shape_recipes_have_source_object(imported_batch: ImportBatch) -> None:
    missing = ShapeRecipe.objects.filter(
        import_batch=imported_batch, source_object__isnull=True
    ).count()
    assert missing == 0


@pytest.mark.django_db
def test_building_variants_have_source_object(imported_batch: ImportBatch) -> None:
    missing = BuildingVariant.objects.filter(
        import_batch=imported_batch, source_object__isnull=True
    ).count()
    assert missing == 0


@pytest.mark.django_db
def test_building_groups_have_source_object(imported_batch: ImportBatch) -> None:
    missing = BuildingGroup.objects.filter(
        import_batch=imported_batch, source_object__isnull=True
    ).count()
    assert missing == 0


@pytest.mark.django_db
def test_content_assets_have_source_object(imported_batch: ImportBatch) -> None:
    missing = GameContentAsset.objects.filter(
        import_batch=imported_batch, source_object__isnull=True
    ).count()
    assert missing == 0


@pytest.mark.django_db
def test_simulation_systems_have_source_object(imported_batch: ImportBatch) -> None:
    missing = SimulationSystem.objects.filter(
        import_batch=imported_batch, source_object__isnull=True
    ).count()
    assert missing == 0


@pytest.mark.django_db
def test_toolbar_tree_nodes_have_source_object(imported_batch: ImportBatch) -> None:
    assert ToolbarTreeNode.objects.filter(import_batch=imported_batch).exists()
    missing = ToolbarTreeNode.objects.filter(
        import_batch=imported_batch, source_object__isnull=True
    ).count()
    assert missing == 0


@pytest.mark.django_db
def test_research_milestones_have_source_object_when_present(imported_batch: ImportBatch) -> None:
    qs = ResearchMilestone.objects.filter(import_batch=imported_batch)
    if not qs.exists():
        pytest.skip("no milestones in dump")
    assert qs.filter(source_object__isnull=True).count() == 0


@pytest.mark.django_db
def test_source_object_auxiliary_path_on_toolbar(imported_batch: ImportBatch) -> None:
    node = (
        ToolbarTreeNode.objects.filter(
            import_batch=imported_batch,
            node_kind=ToolbarNodeKind.ACTION,
            source_object__isnull=False,
        )
        .select_related("source_object")
        .first()
    )
    assert node is not None
    assert node.source_object.source_path == node.tree_path
