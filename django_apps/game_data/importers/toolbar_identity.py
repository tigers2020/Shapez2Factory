"""Extract toolbar row identity from definition_snapshot envelopes."""

from __future__ import annotations

from typing import Any

from django_apps.game_data.importers.base import dig
from django_apps.game_data.models import ToolbarElement
from django_apps.game_data.services.lazy_localized_text import parse_lazy_localized_text


def toolbar_row_identity(
    snap: dict[str, Any], kind: str
) -> tuple[str, str, str]:
    """Return (internal_name, localized_title_key, icon_identifier)."""
    title_parsed = parse_lazy_localized_text(snap.get("IPresentableToolbarElementData.Title"))
    title_key = title_parsed.message_key if title_parsed else ""
    icon_block = snap.get("IPresentableToolbarElementData.Icon") or {}
    icon_identifier = str(dig(icon_block, "name", default=""))

    if kind == ToolbarElement.ElementKind.ISLAND:
        internal_name = str(dig(snap, "IslandGroup", "Id", "Name", default=""))
    elif kind == ToolbarElement.ElementKind.BUILDING:
        bdef = snap.get("BuildingDefinition") or {}
        internal_name = str(dig(bdef, "Id", "Id", default=""))
        if not internal_name:
            for member in bdef.get("Definitions") or []:
                internal_name = str(dig(member, "Id", "Name", default=""))
                if internal_name:
                    break
    else:
        internal_name = title_key

    return internal_name, title_key, icon_identifier
