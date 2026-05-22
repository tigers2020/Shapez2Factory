"""Toolbar tree hierarchy: TreeNode + ACTION elements + placements."""

from __future__ import annotations

import pytest

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
from tests.unit.game_data._dump_expectations import (
    TOOLBAR_ACTION_KIND_NODE_COUNT,
    TOOLBAR_ELEMENT_COUNT,
    TOOLBAR_TREE_NODE_COUNT,
)


@pytest.mark.django_db
def test_tree_node_count_matches_pinned_dump(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    del imported_game_data_batch_module
    assert ToolbarTreeNode.objects.count() == TOOLBAR_TREE_NODE_COUNT


@pytest.mark.django_db
def test_actionable_count_matches_pinned_dump(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    del imported_game_data_batch_module
    assert ToolbarElement.objects.count() == TOOLBAR_ELEMENT_COUNT
    assert (
        ToolbarTreeNode.objects.filter(node_kind=ToolbarNodeKind.ACTION).count()
        == TOOLBAR_ACTION_KIND_NODE_COUNT
    )


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
def test_island_placer_id_matches_pinned_dump(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    del imported_game_data_batch_module
    node = ToolbarTreeNode.objects.get(tree_path="root/Children[6]/Children[7]/Children[0]")
    placement = ToolbarIslandPlacement.objects.get(toolbar_element__tree_node=node)
    assert placement.island_group_name == "TrainQuickStationsGroup"
    assert placement.placer_id == "95"


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
