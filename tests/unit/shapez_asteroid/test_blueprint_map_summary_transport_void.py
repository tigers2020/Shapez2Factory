"""``transport_over_void`` flags exterior void only (shell ∪ interior keeps transport fill)."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline


def _bp(entries: list[dict[str, object]]) -> dict[str, object]:
    return {"V": 1, "BP": {"Entries": entries}}


def test_transport_over_void_excludes_enclosed_interior() -> None:
    """Belt in enclosed interior void is not ``transport_over_void``; far belt is."""

    ring: list[dict[str, object]] = [
        {"X": x, "Y": y, "T": "Layout_ShapeMiner"}
        for x, y in [
            (1, 1),
            (2, 1),
            (3, 1),
            (1, 2),
            (3, 2),
            (1, 3),
            (2, 3),
            (3, 3),
        ]
    ]
    decoded = _bp(
        ring
        + [
            {"X": 2, "Y": 2, "T": "Layout_UndergroundBelt", "R": 0},
            {"X": 5, "Y": 2, "T": "Layout_UndergroundBelt", "R": 0},
        ]
    )
    timeline = build_map_timeline(decoded)
    step0 = timeline[0]["mining_map"]
    belts = {(c["x"], c["y"]): c["transport_over_void"] for c in step0 if c.get("role") == "belt"}
    assert belts[(2, 2)] is False
    assert belts[(5, 2)] is True
