"""
v2 orchestration entrypoint (STEP 0 … STEP 10 wiring).

Keeps Django ORM out of the import path. Full end-to-end solve remains a separate milestone.
"""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2 import (
    preview_reconstruction_timeline as _v2_preview_timeline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.decode import (
    analyze_decoded_layout,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.preview_json import (
    existing_layout_analysis_to_json,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.reconstruction.asteroid_reconstruction import (  # noqa: E501
    reconstruct_asteroid_mining_field,
)


def build_copy_preview_v2_sidecars(decoded: dict[str, Any]) -> dict[str, Any]:
    """STEP 0.5 + STEP 1 outputs for copy-preview (JSON-safe, display-only)."""

    analysis = analyze_decoded_layout(decoded)
    recon = reconstruct_asteroid_mining_field(decoded)
    sk = analysis.source_kind.value
    v2_preview_map_timeline = _v2_preview_timeline.build_v2_preview_map_frames(
        decoded,
        recon,
        source_kind=sk,
    )
    return {
        "existing_layout_analysis": existing_layout_analysis_to_json(analysis),
        "mining_layout_engine": "v2",
        "reconstruction_summary": {
            "mineable_placement_count": len(recon.mineable_placement_cells),
            "extraction_shell_count": len(recon.extraction_shell_cells),
            "full_barrier_count": len(recon.full_barrier_cells),
        },
        "v2_preview_map_timeline": v2_preview_map_timeline,
    }


def solve_mining_layout_v2_stub(_request: dict[str, Any]) -> dict[str, Any]:
    """End-to-end solve (not implemented)."""
    msg = "solve_mining_layout_v2_stub is not implemented (skeleton only)"
    raise NotImplementedError(msg)


__all__ = [
    "build_copy_preview_v2_sidecars",
    "solve_mining_layout_v2_stub",
]
