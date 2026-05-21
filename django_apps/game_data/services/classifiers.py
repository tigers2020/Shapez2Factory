"""Map dump source_type_name strings to domain element kinds."""

from __future__ import annotations

from django_apps.game_data.models import ToolbarElement


def toolbar_element_kind(source_type_name: str) -> str:
    name = source_type_name or ""
    if "BuildingBased" in name:
        return ToolbarElement.ElementKind.BUILDING
    if "IslandBased" in name:
        return ToolbarElement.ElementKind.ISLAND
    if "Separator" in name:
        return ToolbarElement.ElementKind.SEPARATOR
    if "Category" in name:
        return ToolbarElement.ElementKind.CATEGORY
    if "Group" in name:
        return ToolbarElement.ElementKind.GROUP
    return ToolbarElement.ElementKind.OTHER


def simulation_kind_key(source_type_name: str) -> str:
    """Extract short kind from CLR generic string without using it as canonical_id."""
    name = source_type_name or ""
    if "`" in name:
        name = name.split("`", maxsplit=1)[0]
    if "." in name:
        name = name.rsplit(".", maxsplit=1)[-1]
    return name[:128] or "unknown"


def transport_category(transport_kind: str) -> str:
    kind = (transport_kind or "").lower()
    if "belt" in kind:
        return "belt"
    if "pipe" in kind:
        return "pipe"
    if "wire" in kind:
        return "wire"
    if "port" in kind:
        return "port"
    return "other"
