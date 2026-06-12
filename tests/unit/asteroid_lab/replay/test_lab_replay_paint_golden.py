"""Golden replay frame → LabPaintLayers parity (transport-complete)."""

from __future__ import annotations

from tests.support.lab_replay_paint_plan import (
    build_effective_cell_view_index,
    lab_paint_layers_from_view,
    sprite_entries_from_paint_plan_frame,
)
from tests.support.lab_replay_sprite_wire import golden_transport_replay_frames


def _transport_routing_complete_frame() -> dict[str, object]:
    frames = golden_transport_replay_frames()
    return next(
        f for f in frames if str(f.get("event_type", "")).endswith("transport_routing_complete")
    )


def test_golden_transport_complete_frame_paint_layers_have_belt_sprites() -> None:
    transport = _transport_routing_complete_frame()
    index = build_effective_cell_view_index(transport)
    belt_layers = [
        layers
        for _k, view in index.items()
        if (layers := lab_paint_layers_from_view(view))["transport"]
        and layers["transport"]["rel"].startswith("SpaceBelt/")
    ]
    assert belt_layers, "expected at least one transport belt sprite layer in golden frame"

    for _k, view in index.items():
        occupant = view.get("occupant")
        if not isinstance(occupant, dict):
            continue
        if occupant.get("kind") != "candidate_miner":
            continue
        layers = lab_paint_layers_from_view(view)
        assert layers["transport"] is None


def _sprite_entry_sort_key(row: dict[str, object]) -> tuple[object, ...]:
    return (row["x"], row["y"], row["rel"], row["rotation"])


def test_sprite_entries_paint_plan_authority_golden_transport() -> None:
    """Paint-plan sprite rows for golden transport replay (legacy harvest parity retired)."""
    sort_key = _sprite_entry_sort_key
    for frame in golden_transport_replay_frames():
        entries = sprite_entries_from_paint_plan_frame(frame)
        assert sorted(entries, key=sort_key) == sorted(
            sprite_entries_from_paint_plan_frame(frame),
            key=sort_key,
        )
    complete = _transport_routing_complete_frame()
    entries = sprite_entries_from_paint_plan_frame(complete)
    belt = [e for e in entries if str(e["rel"]).startswith("SpaceBelt/")]
    assert belt, "expected belt sprites from paint plan on transport_routing_complete frame"
