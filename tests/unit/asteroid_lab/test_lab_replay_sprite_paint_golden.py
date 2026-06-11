"""Golden replay wire → sprite paint-plan contracts (canvas renderer parity)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from django_apps.shapez_core.lab_sprite_path import default_lab_sprites_root
from tests.support.lab_replay_sprite_wire import (
    golden_transport_replay_frames,
    overlay_fallback_fixture_frame,
    sprite_paint_entries_for_frame,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "asteroid_lab"
    / ("replay_sprite_paint_golden.json")
)


@pytest.fixture(scope="module")
def replay_sprite_golden_fixture() -> dict[str, object]:
    frames = golden_transport_replay_frames()
    transport = next(
        f for f in frames if str(f.get("event_type", "")).endswith("transport_routing_complete")
    )
    payload = {
        "transport_complete_frame": transport,
        "overlay_fallback_frame": overlay_fallback_fixture_frame(),
    }
    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def test_golden_fixture_file_written(replay_sprite_golden_fixture: dict[str, object]) -> None:
    assert FIXTURE_PATH.is_file()
    on_disk = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert "transport_complete_frame" in on_disk
    assert "overlay_fallback_frame" in on_disk


def test_transport_complete_frame_emits_space_belt_sprite(
    replay_sprite_golden_fixture: dict[str, object],
) -> None:
    frame = replay_sprite_golden_fixture["transport_complete_frame"]
    assert isinstance(frame, dict)
    sprites = sprite_paint_entries_for_frame(frame)
    belt_rows = [s for s in sprites if s["rel"].startswith("SpaceBelt/")]
    assert belt_rows, f"expected belt sprite, got {sprites!r}"
    assert any(s["rel"] == "SpaceBelt/SpaceBelt_Forward.svg" for s in belt_rows)
    root = default_lab_sprites_root()
    for row in belt_rows:
        assert (root / str(row["rel"])).is_file(), row["rel"]


def test_transport_complete_frame_emits_asteroid_field_sprites(
    replay_sprite_golden_fixture: dict[str, object],
) -> None:
    frame = replay_sprite_golden_fixture["transport_complete_frame"]
    assert isinstance(frame, dict)
    sprites = sprite_paint_entries_for_frame(frame)
    shape_rows = [s for s in sprites if s["rel"] == "AsteroidField_Shape.svg"]
    assert shape_rows, f"expected asteroid field sprites, got {sprites!r}"
    root = default_lab_sprites_root()
    assert (root / "AsteroidField_Shape.svg").is_file()


def test_overlay_fallback_frame_includes_pipe_sprite_from_cell_overlay_json(
    replay_sprite_golden_fixture: dict[str, object],
) -> None:
    frame = replay_sprite_golden_fixture["overlay_fallback_frame"]
    assert isinstance(frame, dict)
    sprites = sprite_paint_entries_for_frame(frame)
    pipe_at_2_0 = [s for s in sprites if s["x"] == 2 and s["y"] == 0]
    assert pipe_at_2_0
    assert pipe_at_2_0[0]["rel"] == "SpacePipe/SpacePipe_Forward.svg"
    assert pipe_at_2_0[0]["rotation"] == 1
