"""Toolbar flatten equivalence: 204 paths, parent closure, acyclic."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.game_data.importers.source_loader import load_json
from django_apps.game_data.models import ImportBatch, ToolbarTreeNode
from django_apps.game_data.services.toolbar_node_kind import parent_path_from_tree_path


def _source_paths(game_data_dir: Path) -> list[str]:
    rows = load_json(game_data_dir / "toolbar_entries.json")
    return sorted(str(r["display_name_key"]) for r in rows if r.get("display_name_key"))


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
def test_toolbar_path_closure(
    game_data_dir: Path,
    imported_game_data_batch_module: ImportBatch,
) -> None:
    del imported_game_data_batch_module
    expected = set(_source_paths(game_data_dir))
    actual = set(ToolbarTreeNode.objects.values_list("tree_path", flat=True))
    assert actual == expected


@pytest.mark.django_db
def test_toolbar_parent_child_edges(
    game_data_dir: Path,
    imported_game_data_batch_module: ImportBatch,
) -> None:
    del imported_game_data_batch_module
    paths = set(_source_paths(game_data_dir))
    expected_edges = _parent_edges(paths)
    nodes = {n.tree_path: n for n in ToolbarTreeNode.objects.select_related("parent")}
    actual_edges: set[tuple[str, str]] = set()
    for child_path, node in nodes.items():
        if node.parent_id is None:
            continue
        parent_path = node.parent.tree_path
        actual_edges.add((parent_path, child_path))
    assert actual_edges == expected_edges


@pytest.mark.django_db
def test_toolbar_no_dangling_parent(game_data_dir: Path) -> None:
    paths = set(_source_paths(game_data_dir))
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
