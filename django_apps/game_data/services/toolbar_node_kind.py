"""Structure-based toolbar tree node classification (no CLR wildcard matching)."""

from __future__ import annotations

from collections import defaultdict

from django_apps.game_data.models import ToolbarNodeKind


def has_placer_id(snapshot: dict[str]) -> bool:
    block = snapshot.get("IPlacementToolbarElementData.PlacerId") or {}
    if not isinstance(block, dict):
        return False
    pid = block.get("Id")
    return pid is not None and str(pid) != ""


def row_is_action(snapshot: dict[str]) -> bool:
    return has_placer_id(snapshot)


def is_separator_row(row: dict[str]) -> bool:
    stype = str(row.get("source_type_name", ""))
    if stype == "ToolbarSlotSeparator":
        return True
    snap = row.get("definition_snapshot") or {}
    return str(snap.get("$type", "")) == "ToolbarSlotSeparator"


def parent_path_from_tree_path(tree_path: str) -> str | None:
    if tree_path == "root" or "/" not in tree_path:
        return None
    return "/".join(tree_path.split("/")[:-1])


def depth_from_tree_path(tree_path: str) -> int:
    if tree_path == "root":
        return 0
    return tree_path.count("Children[")


def classify_toolbar_node_kind(
    *,
    tree_path: str,
    row: dict[str],
    action_subtree: dict[str, bool],
    children_by_parent: dict[str | None, list[str]],
) -> str:
    if tree_path == "root":
        return ToolbarNodeKind.ROOT
    if is_separator_row(row):
        return ToolbarNodeKind.SEPARATOR
    snap = row.get("definition_snapshot") or {}
    if row_is_action(snap):
        return ToolbarNodeKind.ACTION
    if action_subtree.get(tree_path, False):
        return ToolbarNodeKind.GROUP
    if children_by_parent.get(tree_path):
        return ToolbarNodeKind.FOLDER
    return ToolbarNodeKind.FOLDER


def build_children_by_parent(path_to_row: dict[str, dict]) -> dict[str | None, list[str]]:
    children: dict[str | None, list[str]] = defaultdict(list)
    for path in path_to_row:
        parent = parent_path_from_tree_path(path)
        children[parent].append(path)
    return children


def depth_sorted_paths(path_to_row: dict[str, dict]) -> list[str]:
    return sorted(path_to_row.keys(), key=depth_from_tree_path, reverse=True)


def compute_action_subtree(
    path_to_row: dict[str, dict],
    children_by_parent: dict[str | None, list[str]],
) -> dict[str, bool]:
    action_subtree: dict[str, bool] = {}
    for path in depth_sorted_paths(path_to_row):
        snap = path_to_row[path].get("definition_snapshot") or {}
        action_subtree[path] = row_is_action(snap) or any(
            action_subtree[child] for child in children_by_parent.get(path, [])
        )
    return action_subtree


def topological_paths(path_to_row: dict[str, dict]) -> list[str]:
    return sorted(path_to_row.keys(), key=depth_from_tree_path)
