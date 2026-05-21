"""Connectable key signatures must distinguish connector topology."""

from __future__ import annotations

from django_apps.game_data.services.connectable_signatures import (
    build_connectable_key,
    build_connector_signature,
)


def test_connector_signature_order_independent() -> None:
    a = {"Pivot": "(0,0,0);North", "$type": "ItemReceiverConnector", "UpdatePriority": "MeFirst"}
    b = {"Pivot": "(1,0,0);East", "$type": "ItemProviderConnector", "UpdatePriority": "MeLast"}
    assert build_connector_signature([b, a]) == build_connector_signature([a, b])


def test_connectable_key_differs_by_connector_signature() -> None:
    sig_a = build_connector_signature(
        [{"Pivot": "(0,0,0);North", "$type": "ItemReceiverConnector"}]
    )
    sig_b = build_connector_signature(
        [{"Pivot": "(0,0,0);South", "$type": "ItemReceiverConnector"}]
    )
    key_a = build_connectable_key(
        building_variant_id=1,
        num_connectors=1,
        num_occupied_tiles=6,
        connector_signature=sig_a,
        lane_signature="shape:4",
    )
    key_b = build_connectable_key(
        building_variant_id=1,
        num_connectors=1,
        num_occupied_tiles=6,
        connector_signature=sig_b,
        lane_signature="shape:4",
    )
    assert key_a != key_b
