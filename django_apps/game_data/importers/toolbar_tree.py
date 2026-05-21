"""Four-pass toolbar tree import: TreeNode hierarchy + ACTION elements + placements."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django_apps.game_data.importers.base import ImportContext, dig, parse_toolbar_child_index
from django_apps.game_data.importers.toolbar_identity import toolbar_row_identity
from django_apps.game_data.models import (
    GameContentAsset,
    ResearchMechanic,
    ToolbarBuildingPlacement,
    ToolbarElement,
    ToolbarIslandPlacement,
    ToolbarNodeKind,
    ToolbarTreeNode,
)
from django_apps.game_data.services import classifiers, identifiers
from django_apps.game_data.services.toolbar_node_kind import (
    build_children_by_parent,
    classify_toolbar_node_kind,
    compute_action_subtree,
    parent_path_from_tree_path,
    topological_paths,
)


@dataclass
class PendingToolbarNode:
    tree_path: str
    source_stable_id: str
    snapshot: dict[str, Any]
    source_row_index: int
    node_kind: str = ""
    child_index: int = 0
    parent_path: str | None = None
    depth: int = 0
    internal_name: str = ""
    localized_title_key: str = ""
    icon_identifier: str = ""


def _element_display_name(
    snap: dict[str, Any], element_kind: str, internal_name: str, title_key: str
) -> str:
    if element_kind == ToolbarElement.ElementKind.ISLAND:
        group = str(dig(snap, "IslandGroup", "Id", "Name", default=""))
        placer = str(dig(snap.get("IPlacementToolbarElementData.PlacerId") or {}, "Id", default=""))
        return f"{group} (placer {placer})" if placer else group
    if internal_name:
        return internal_name
    if title_key:
        return title_key
    return ""


def _element_stable_key(
    snap: dict[str, Any], element_kind: str, internal_name: str, source_stable_id: str
) -> str:
    if element_kind == ToolbarElement.ElementKind.ISLAND:
        return str(dig(snap, "IslandGroup", "Id", "Name", default="")) or source_stable_id
    if element_kind == ToolbarElement.ElementKind.BUILDING:
        bdef = snap.get("BuildingDefinition") or {}
        key = str(dig(bdef, "Id", "Id", default=""))
        if key:
            return key
        for member in bdef.get("Definitions") or []:
            key = str(dig(member, "Id", "Name", default=""))
            if key:
                return key
    return internal_name or source_stable_id


def import_toolbar_tree(ctx: ImportContext, rows: list[dict[str, Any]]) -> None:
    ToolbarTreeNode.objects.filter(import_batch=ctx.batch).delete()

    path_to_row: dict[str, dict] = {
        str(row["display_name_key"]): row for row in rows if row.get("display_name_key")
    }
    if not path_to_row:
        return

    path_to_pending: dict[str, PendingToolbarNode] = {}
    for i, row in enumerate(rows):
        tree_path = str(row.get("display_name_key", ""))
        if not tree_path:
            continue
        snap = row.get("definition_snapshot") or {}
        stype = str(row.get("source_type_name", ""))
        elem_kind = classifiers.toolbar_element_kind(stype)
        internal_name, title_key, icon = toolbar_row_identity(snap, elem_kind)
        path_to_pending[tree_path] = PendingToolbarNode(
            tree_path=tree_path,
            source_stable_id=str(row.get("stable_id") or ""),
            snapshot=snap,
            source_row_index=i,
            child_index=parse_toolbar_child_index(tree_path),
            parent_path=parent_path_from_tree_path(tree_path),
            internal_name=internal_name,
            localized_title_key=title_key,
            icon_identifier=icon,
        )

    children_by_parent = build_children_by_parent(path_to_row)
    action_subtree = compute_action_subtree(path_to_row, children_by_parent)

    for path, pending in path_to_pending.items():
        pending.node_kind = classify_toolbar_node_kind(
            tree_path=path,
            row=path_to_row[path],
            action_subtree=action_subtree,
            children_by_parent=children_by_parent,
        )
        pending.depth = 0 if pending.parent_path is None else 0  # set in pass 2

    for path in topological_paths(path_to_row):
        pending = path_to_pending[path]
        if pending.parent_path is None:
            pending.depth = 0
        else:
            parent_pending = path_to_pending.get(pending.parent_path)
            pending.depth = (parent_pending.depth + 1) if parent_pending else 0

    persisted: dict[str, ToolbarTreeNode] = {}

    for path in topological_paths(path_to_row):
        pending = path_to_pending[path]
        parent_cid = ""
        parent_db = None
        if pending.parent_path:
            parent_db = persisted.get(pending.parent_path)
            if parent_db is None:
                continue
            parent_cid = parent_db.canonical_id

        cid = identifiers.canonical_toolbar_node(
            source_stable_id=pending.source_stable_id,
            parent_canonical_id=parent_cid,
            child_index=pending.child_index,
        )
        row = path_to_row[path]
        snap = pending.snapshot
        mechanic = None
        mech_key = str(dig(snap, "MechanicRequiredToUnlock", "Id", default=""))
        if mech_key:
            mechanic = ResearchMechanic.objects.filter(mechanic_key=mech_key).first()
        icon_asset = None
        if pending.icon_identifier:
            icon_asset = (
                GameContentAsset.objects.filter(
                    import_batch=ctx.batch,
                    content_kind=GameContentAsset.ContentKind.SPRITE,
                    content_path__icontains=pending.icon_identifier,
                ).first()
                or GameContentAsset.objects.filter(
                    import_batch=ctx.batch,
                    content_kind=GameContentAsset.ContentKind.SPRITE,
                    display_name_key__icontains=pending.icon_identifier,
                ).first()
            )
        src = ctx.record_source_row(
            "toolbar_entries.json",
            pending.source_row_index,
            row,
            source_path=pending.tree_path,
            system_id=pending.source_stable_id,
            clr_type=str(row.get("source_type_name", "")),
        )
        node, _ = ToolbarTreeNode.objects.update_or_create(
            canonical_id=cid,
            defaults={
                "import_batch": ctx.batch,
                "source_stable_id": pending.source_stable_id,
                "parent": parent_db,
                "child_index": pending.child_index,
                "order_index": pending.child_index,
                "depth": pending.depth,
                "node_kind": pending.node_kind,
                "tree_path": pending.tree_path,
                "internal_name": pending.internal_name,
                "localized_title_key": pending.localized_title_key,
                "icon_identifier": pending.icon_identifier,
                "required_mechanic": mechanic,
                "icon_content_asset": icon_asset,
                "source_row_index": pending.source_row_index,
                "source_object": src,
            },
        )
        persisted[path] = node
        ctx.bump("toolbar_tree_node")

    for path in topological_paths(path_to_row):
        pending = path_to_pending[path]
        if pending.node_kind != ToolbarNodeKind.ACTION:
            continue
        node = persisted.get(path)
        if node is None:
            continue
        snap = pending.snapshot
        stype = str(path_to_row[path].get("source_type_name", ""))
        element_kind = classifiers.toolbar_element_kind(stype)
        stable_key = _element_stable_key(
            snap, element_kind, pending.internal_name, pending.source_stable_id
        )
        display_name = _element_display_name(
            snap, element_kind, pending.internal_name, pending.localized_title_key
        )
        elem_cid = identifiers.canonical_toolbar_element(
            pending.source_stable_id or stable_key or pending.tree_path
        )
        elem, _ = ToolbarElement.objects.update_or_create(
            canonical_id=elem_cid,
            defaults={
                "import_batch": ctx.batch,
                "tree_node": node,
                "source_stable_id": pending.source_stable_id,
                "element_kind": element_kind,
                "stable_key": stable_key,
                "display_name": display_name,
                "section_index": snap.get("SectionIndex"),
                "source_row_index": pending.source_row_index,
            },
        )
        ctx.bump("toolbar_element")

        if element_kind == ToolbarElement.ElementKind.BUILDING:
            from django_apps.game_data.models import BuildingVariant

            bdef = snap.get("BuildingDefinition") or {}
            group_key = str(dig(bdef, "Id", "Id", default=""))
            variant = BuildingVariant.objects.filter(internal_name=group_key).first()
            resolved_key = group_key
            if not variant:
                for member in bdef.get("Definitions") or []:
                    internal = str(dig(member, "Id", "Name", default=""))
                    variant = BuildingVariant.objects.filter(internal_name=internal).first()
                    if variant:
                        resolved_key = internal
                        break
            if variant:
                ToolbarBuildingPlacement.objects.update_or_create(
                    toolbar_element=elem,
                    defaults={
                        "building_variant": variant,
                        "building_definition_key": resolved_key,
                        "placer_id": str(
                            dig(
                                snap.get("IPlacementToolbarElementData.PlacerId") or {},
                                "Id",
                                default="",
                            )
                        ),
                        "icon_sprite_name": str(dig(bdef, "Icon", "name", default="")),
                        "is_transport_building": bool(bdef.get("IsTransportBuilding", False)),
                        "player_buildable": bool(bdef.get("PlayerBuildable", True)),
                    },
                )
        elif element_kind == ToolbarElement.ElementKind.ISLAND:
            ToolbarIslandPlacement.objects.update_or_create(
                toolbar_element=elem,
                defaults={
                    "island_group_name": str(dig(snap, "IslandGroup", "Id", "Name", default="")),
                    "placer_id": str(
                        dig(
                            snap.get("IPlacementToolbarElementData.PlacerId") or {},
                            "Id",
                            default="",
                        )
                    ),
                },
            )
