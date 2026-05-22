"""Toolbar flatten equivalence: pinned dump ORM invariants."""

from __future__ import annotations

import pytest

from django_apps.game_data.models import ImportBatch, ToolbarTreeNode
from django_apps.game_data.services.toolbar_node_kind import parent_path_from_tree_path
from tests.unit.game_data._dump_expectations import TOOLBAR_TREE_NODE_COUNT


def _parent_edges(paths: set[str]) -> set[tuple[str, str]]:
    edges: set[tuple[str, str]] = set()
    for path in paths:
        if path == "root":
            continue
        parent = parent_path_from_tree_path(path)
        assert parent is not None
        edges.add((parent, path))
    return edges


@pytest.mark.django_db
def test_toolbar_path_count_matches_pinned_dump(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    del imported_game_data_batch_module
    assert ToolbarTreeNode.objects.count() == TOOLBAR_TREE_NODE_COUNT


@pytest.mark.django_db
def test_toolbar_parent_child_edges(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    del imported_game_data_batch_module
    paths = set(ToolbarTreeNode.objects.values_list("tree_path", flat=True))
    expected_edges = _parent_edges(paths)
    nodes = {n.tree_path: n for n in ToolbarTreeNode.objects.select_related("parent")}
    actual_edges: set[tuple[str, str]] = set()
    for child_path, node in nodes.items():
        if node.parent_id is None:
            continue
        actual_edges.add((node.parent.tree_path, child_path))
    assert actual_edges == expected_edges


@pytest.mark.django_db
def test_toolbar_no_dangling_parent(
    imported_game_data_batch_module: ImportBatch,
) -> None:
    del imported_game_data_batch_module
    paths = set(ToolbarTreeNode.objects.values_list("tree_path", flat=True))
    for path in paths:
        if path == "root":
            continue
        parent = parent_path_from_tree_path(path)
        assert parent in paths


@pytest.mark.django_db
def test_toolbar_acyclic(imported_game_data_batch_module: ImportBatch) -> None:
    del imported_game_data_batch_module
    nodes = list(ToolbarTreeNode.objects.select_related("parent"))
    by_id = {n.id: n for n in nodes}
    for node in nodes:
        seen: set[int] = set()
        cur = node
        while cur.parent_id is not None:
            assert cur.parent_id not in seen
            seen.add(cur.id)
            cur = by_id[cur.parent_id]
