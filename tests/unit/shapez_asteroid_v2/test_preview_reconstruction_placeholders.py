"""v2 preview timeline: placeholder milestones after reconstruction."""

from __future__ import annotations

import importlib

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    ReconstructionDTO,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.reconstruction.asteroid_reconstruction import (  # noqa: E501
    reconstruct_asteroid_mining_field,
)

_v2_preview_tl_mod = importlib.import_module(
    "django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.preview_reconstruction_timeline"
)


def test_empty_reconstruction_returns_only_placeholder_steps() -> None:
    decoded: dict[str, object] = {"V": 1, "BP": {"Entries": []}}
    recon = ReconstructionDTO()
    frames = _v2_preview_tl_mod.build_v2_preview_map_frames(decoded, recon, source_kind=None)
    assert len(frames) == len(_v2_preview_tl_mod.V2_PREVIEW_PLACEHOLDER_STEP_IDS)
    assert [f["id"] for f in frames] == list(_v2_preview_tl_mod.V2_PREVIEW_PLACEHOLDER_STEP_IDS)
    for fr in frames:
        assert fr["summary"].get("preview_placeholder") is True
        assert fr["mining_map"] == []


def test_v2_preview_belt_transport_over_void_exterior_only() -> None:
    """Interior-hole belt: ``transport_over_void`` false; far exterior belt: true."""

    ring = [
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
    decoded: dict[str, object] = {
        "V": 1,
        "BP": {
            "Entries": ring
            + [
                {"X": 2, "Y": 2, "T": "Layout_UndergroundBelt", "R": 0},
                {"X": 5, "Y": 2, "T": "Layout_UndergroundBelt", "R": 0},
            ]
        },
    }
    recon = reconstruct_asteroid_mining_field(decoded)
    frames = _v2_preview_tl_mod.build_v2_preview_map_frames(decoded, recon, source_kind=None)
    mm0 = frames[0]["mining_map"]
    belts = {
        (int(r["x"]), int(r["y"])): r.get("transport_over_void")
        for r in mm0
        if isinstance(r, dict) and r.get("role") == "belt"
    }
    assert belts[(2, 2)] is False
    assert belts[(5, 2)] is True
