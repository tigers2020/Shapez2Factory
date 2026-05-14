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
    analyze_to_context,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.preview_json import (
    existing_layout_analysis_to_json,
    to_jsonable,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.reconstruction.asteroid_reconstruction import (  # noqa: E501
    reconstruct_asteroid_mining_field,
)


def build_copy_preview_v2_sidecars(decoded: dict[str, Any]) -> dict[str, Any]:
    """STEP 0.5 + STEP 1 (+ timeline) for copy-preview (JSON-safe, display-only).

    Full end-to-end solve / replay are not required: this is the partial pipeline
    surfaced to the UI without reading NDJSON or prior replay as algorithm input.
    """

    analysis = analyze_decoded_layout(decoded)
    decoded_ctx = analyze_to_context(decoded)
    recon = reconstruct_asteroid_mining_field(decoded, decoded_ctx)
    sk = analysis.source_kind.value
    v2_preview_map_timeline = _v2_preview_timeline.build_v2_preview_map_frames(
        decoded,
        recon,
        source_kind=sk,
    )
    return {
        "existing_layout_analysis": existing_layout_analysis_to_json(analysis),
        "mining_layout_engine": "v2",
        "reconstruction": to_jsonable(recon),
        "partial_pipeline": {
            "phases_included": [
                "step_0_decode",
                "step_0_5_existing_layout_analysis",
                "step_1_reconstruction",
                "preview_map_timeline",
                "step_2_pass1_replay_timeline",
            ],
            "phases_not_included": [
                "step_3_pass2",
                "step_4_routing",
                "step_5_plus_reclaim_recovery",
                "step_9_final_validation",
                "step_10_replay_snapshots",
            ],
            "note": (
                "Replay/trace files are output-side evidence only; they are not read here "
                "to drive reconstruction or placement."
            ),
        },
        "reconstruction_summary": {
            "mineable_placement_count": len(recon.mineable_placement_cells),
            "extraction_shell_count": len(recon.extraction_shell_cells),
            "full_barrier_count": len(recon.full_barrier_cells),
            "extractor_cell_count": len(recon.extractor_cells),
            "extension_cell_count": len(recon.extension_cells),
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
