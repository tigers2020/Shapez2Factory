"""Toolbar tree hierarchy: TreeNode + ACTION elements + placements."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.game_data.importers import GameDataImporter
from django_apps.game_data.importers.source_loader import load_json
from django_apps.game_data.models import (
    ImportBatch,
    ToolbarElement,
    ToolbarIslandPlacement,
    ToolbarNodeKind,
    ToolbarTreeNode,
)
from django_apps.game_data.services.toolbar_node_kind import (
    build_children_by_parent,
    classify_toolbar_node_kind,
    compute_action_subtree,
    is_separator_row,
)
from tests.unit.game_data._stratified import (
    TOOLBAR_CANONICAL_ID_ANCHOR_PATHS,
    merge_unique_paths,
    pick_stratified_by_key,
)


def _source_rows(game_data_dir: Path) -> list[dict]:
    return load_json(game_data_dir / "toolbar_entries.json")


def _expected_node_count(rows: list[dict]) -> int:
    return sum(1 for row in rows if row.get("display_name_key"))


def _expected_action_count(rows: list[dict]) -> int:
    path_to_row = {str(r["display_name_key"]): r for r in rows if r.get("display_name_key")}
    children = build_children_by_parent(path_to_row)
    action_subtree = compute_action_subtree(path_to_row, children)
    return sum(
        1
        for path, row in path_to_row.items()
        if classify_toolbar_node_kind(
            tree_path=path,
            row=row,
            action_subtree=action_subtree,
            children_by_parent=children,
        )
        == ToolbarNodeKind.ACTION
    )


@pytest.mark.django_db
def test_tree_node_count_matches_source(
    game_data_dir: Path,
    imported_game_data_batch_module: ImportBatch,
) -> None:
    del imported_game_data_batch_module
    rows = _source_rows(game_data_dir)
    assert ToolbarTreeNode.objects.count() == _expected_node_count(rows)


@pytest.mark.django_db
def test_actionable_count_matches_source(
    game_data_dir: Path,
    imported_game_data_batch_module: ImportBatch,
) -> None:
    del imported_game_data_batch_module
    rows = _source_rows(game_data_dir)
    expected = _expected_action_count(rows)
    assert ToolbarElement.objects.count() == expected
    assert ToolbarTreeNode.objects.filter(node_kind=ToolbarNodeKind.ACTION).count() == expected


@pytest.mark.django_db
def test_separator_nodes_have_no_toolbar_element(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    del imported_game_data_batch_module
    separators = ToolbarTreeNode.objects.filter(node_kind=ToolbarNodeKind.SEPARATOR)
    assert separators.exists()
    for node in separators:
        assert not ToolbarElement.objects.filter(tree_node=node).exists()


@pytest.mark.django_db
def test_ancestor_chain_children_5_8_4(imported_game_data_batch_module: ImportBatch) -> None:
    del imported_game_data_batch_module
    paths = [
        "root",
        "root/Children[5]",
        "root/Children[5]/Children[8]",
        "root/Children[5]/Children[8]/Children[4]",
    ]
    nodes = {n.tree_path: n for n in ToolbarTreeNode.objects.filter(tree_path__in=paths)}
    assert set(nodes) == set(paths)
    assert nodes["root"].depth == 0
    assert nodes["root/Children[5]"].parent_id == nodes["root"].id
    assert nodes["root/Children[5]/Children[8]"].parent_id == nodes["root/Children[5]"].id
    assert (
        nodes["root/Children[5]/Children[8]/Children[4]"].parent_id
        == nodes["root/Children[5]/Children[8]"].id
    )
    assert nodes["root/Children[5]/Children[8]/Children[4]"].node_kind == ToolbarNodeKind.ACTION


@pytest.mark.django_db
def test_sibling_child_index_unique(imported_game_data_batch_module: ImportBatch) -> None:
    del imported_game_data_batch_module
    parent = ToolbarTreeNode.objects.get(tree_path="root/Children[6]/Children[7]")
    indices = list(
        ToolbarTreeNode.objects.filter(parent=parent).values_list("child_index", flat=True)
    )
    assert len(indices) == len(set(indices))


@pytest.mark.django_db
def test_folder_nodes_no_placement(imported_game_data_batch_module: ImportBatch) -> None:
    del imported_game_data_batch_module
    structural = ToolbarTreeNode.objects.filter(
        node_kind__in=[
            ToolbarNodeKind.ROOT,
            ToolbarNodeKind.FOLDER,
            ToolbarNodeKind.GROUP,
            ToolbarNodeKind.SEPARATOR,
        ]
    )
    for node in structural:
        assert not ToolbarElement.objects.filter(tree_node=node).exists()


@pytest.mark.django_db
def test_no_element_display_from_tree_path(imported_game_data_batch_module: ImportBatch) -> None:
    del imported_game_data_batch_module
    for elem in ToolbarElement.objects.all():
        assert "root/Children" not in (elem.display_name or "")
        assert "Island placement:" not in str(elem)


@pytest.mark.django_db
def test_island_placer_id_matches_json(imported_game_data_batch_module: ImportBatch) -> None:
    del imported_game_data_batch_module
    node = ToolbarTreeNode.objects.get(tree_path="root/Children[6]/Children[7]/Children[0]")
    placement = ToolbarIslandPlacement.objects.get(toolbar_element__tree_node=node)
    assert placement.island_group_name == "TrainQuickStationsGroup"
    assert placement.placer_id == "95"


def _canonical_id_by_tree_path(batch: ImportBatch, paths: list[str]) -> dict[str, str]:
    rows = ToolbarTreeNode.objects.filter(import_batch=batch, tree_path__in=paths).values_list(
        "tree_path",
        "canonical_id",
    )
    return dict(rows)


@pytest.mark.django_db
def test_canonical_id_fast_stability_stratified_toolbar_sample(
    game_data_dir: Path,
    imported_game_data_batch_module: ImportBatch,
) -> None:
    """Stratified sample: canonical_id per tree_path stable after re-import.

    Module fixture = first snapshot; one in-test re-import (not full-tree set compare).
    """

    batch = imported_game_data_batch_module
    nodes = list(ToolbarTreeNode.objects.filter(import_batch=batch).order_by("tree_path"))
    assert len(nodes) >= 15
    available = {n.tree_path for n in nodes}
    stratified_nodes = pick_stratified_by_key(nodes, n=5, key=lambda node: node.tree_path)
    stratified_paths = [node.tree_path for node in stratified_nodes]
    paths = merge_unique_paths(
        stratified_paths,
        TOOLBAR_CANONICAL_ID_ANCHOR_PATHS,
        available=available,
    )
    assert len(paths) >= 10
    first = _canonical_id_by_tree_path(batch, paths)
    assert set(first) == set(paths)

    GameDataImporter(game_data_dir, batch_name="pytest-module").run()
    batch_after = ImportBatch.objects.get(pk=batch.pk)
    second = _canonical_id_by_tree_path(batch_after, paths)
    assert second == first


@pytest.mark.django_db
@pytest.mark.slow
def test_canonical_id_stable_across_reimport_full_toolbar_tree(game_data_dir: Path) -> None:
    GameDataImporter(game_data_dir, batch_name="tree-a").run()
    first = set(ToolbarTreeNode.objects.values_list("canonical_id", flat=True))
    GameDataImporter(game_data_dir, batch_name="tree-a").run()
    second = set(ToolbarTreeNode.objects.values_list("canonical_id", flat=True))
    assert first == second


def test_separator_row_classified() -> None:
    row = {
        "source_type_name": "ToolbarSlotSeparator",
        "definition_snapshot": {"$type": "ToolbarSlotSeparator"},
        "display_name_key": "root/Children[0]/Children[1]",
    }
    path_to_row = {"root/Children[0]/Children[1]": row}
    children = build_children_by_parent(path_to_row)
    action_subtree = compute_action_subtree(path_to_row, children)
    assert is_separator_row(row)
    kind = classify_toolbar_node_kind(
        tree_path="root/Children[0]/Children[1]",
        row=row,
        action_subtree=action_subtree,
        children_by_parent=children,
    )
    assert kind == ToolbarNodeKind.SEPARATOR
