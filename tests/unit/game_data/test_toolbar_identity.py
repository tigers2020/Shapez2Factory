"""Toolbar element vs island placement identity boundary."""

from __future__ import annotations

import pytest

from django_apps.game_data.importers.toolbar_identity import toolbar_row_identity
from django_apps.game_data.models import (
    ImportBatch,
    ToolbarElement,
    ToolbarIslandPlacement,
    ToolbarTreeNode,
)


def test_toolbar_row_identity_island_uses_group_name() -> None:
    snap = {
        "IslandGroup": {"Id": {"Name": "TrainQuickStationsGroup"}},
        "IPresentableToolbarElementData.Title": {
            "Id": {"<Id>k__BackingField": "island-layout.TrainQuick.title"},
            "$type": "Core.Localization.LazyLocalizedText",
        },
        "IPresentableToolbarElementData.Icon": {"name": "TrainIcon"},
    }
    internal, title_key, icon = toolbar_row_identity(snap, ToolbarElement.ElementKind.ISLAND)
    assert internal == "TrainQuickStationsGroup"
    assert title_key == "island-layout.TrainQuick.title"
    assert icon == "TrainIcon"


@pytest.mark.django_db
def test_island_via_tree_node_not_path_label(imported_game_data_batch_module: ImportBatch) -> None:
    del imported_game_data_batch_module
    path = "root/Children[7]/Children[3]/Children[2]"
    node = ToolbarTreeNode.objects.get(tree_path=path)
    placement = ToolbarIslandPlacement.objects.select_related("toolbar_element").get(
        toolbar_element__tree_node=node
    )
    assert node.tree_path == path
    assert placement.island_group_name == "Layout_Classic_Regular_Tier1_YellowA_Group"
    elem = placement.toolbar_element
    assert elem.stable_key == placement.island_group_name
    assert "118" in elem.display_name
    assert "root/Children" not in elem.display_name
