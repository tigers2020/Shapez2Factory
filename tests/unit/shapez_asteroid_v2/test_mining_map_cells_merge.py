"""``mining_map_cells`` helpers used by ``blueprint_map_summary`` merge."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.blueprint_map_summary import (
    merge_with_transport_and_final_mining_map,
)


def test_merge_preserves_with_transport_over_asteroid_field_on_overlap() -> None:
    with_t = [
        {"x": 1, "y": 0, "role": "occupied", "surface": "shape", "layout_kind": "miner", "t": "X"},
    ]
    final = [
        {"x": 1, "y": 0, "role": "occupied", "surface": "shape", "layout_kind": "asteroid_field"},
        {"x": 2, "y": 0, "role": "inferred", "surface": "shape"},
    ]
    merged = merge_with_transport_and_final_mining_map(with_t, final)
    by = {(c["x"], c["y"]): c for c in merged}
    assert by[(1, 0)]["layout_kind"] == "miner"
    assert by[(2, 0)]["role"] == "inferred"
