"""v2 preview timeline: placeholder milestones after reconstruction."""

from __future__ import annotations

import importlib

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    ReconstructionDTO,
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
