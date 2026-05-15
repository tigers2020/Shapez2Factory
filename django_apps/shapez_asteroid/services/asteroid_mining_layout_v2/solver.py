"""
v2 orchestration entrypoint (STEP 0 … STEP 10 wiring).

Keeps Django ORM out of the import path. Full end-to-end solve remains a separate milestone.
"""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.constants import COPY_PREVIEW_SCHEMA_VERSION
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2 import (
    preview_reconstruction_timeline as _v2_preview_timeline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.decode import (
    analyze_decoded_layout,
    analyze_to_context,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.reconstruction.asteroid_reconstruction import (  # noqa: E501
    reconstruct_asteroid_mining_field,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.serialization import (
    existing_layout_analysis_to_json,
    to_jsonable,
)
from django_apps.shapez_asteroid.services.behavior_artifact_collector import (
    BehaviorArtifactCollector,
)


def build_copy_preview_v2_sidecars(
    decoded: dict[str, Any],
    *,
    behavior_artifact: BehaviorArtifactCollector | None = None,
) -> dict[str, Any]:
    """STEP 0.5 + STEP 1 (+ timeline) for copy-preview (JSON-safe, display-only).

    Full end-to-end solve / replay are not required: this is the partial pipeline
    surfaced to the UI without reading NDJSON or prior replay as algorithm input.
    """

    analysis = analyze_decoded_layout(decoded)
    decoded_ctx = analyze_to_context(decoded)
    recon = reconstruct_asteroid_mining_field(decoded, decoded_ctx)
    sk = analysis.source_kind.value
    preview_res = _v2_preview_timeline.build_v2_preview_map_frames(
        decoded,
        recon,
        source_kind=sk,
    )
    v2_preview_map_timeline = preview_res.frames
    partial_pipeline: dict[str, Any] = {
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
    }
    reconstruction_summary = {
        "mineable_placement_count": len(recon.mineable_placement_cells),
        "interior_patch_count": len(recon.interior_patch_cells),
        "extraction_shell_count": len(recon.extraction_shell_cells),
        "full_barrier_count": len(recon.full_barrier_cells),
        "extractor_cell_count": len(recon.extractor_cells),
        "extension_cell_count": len(recon.extension_cells),
        "equipment_footprint_mineable_count": len(recon.equipment_footprint_mineable_cells),
    }
    if behavior_artifact is not None:
        behavior_artifact.record_copy_preview_pipeline(
            existing_layout_analysis=existing_layout_analysis_to_json(analysis),
            reconstruction=to_jsonable(recon),
            reconstruction_summary=reconstruction_summary,
            preview_frames=v2_preview_map_timeline,
            pass1_replay_events=list(preview_res.pass1_replay_events),
            decoded_for_diagnosis=decoded,
            reconstruction_dto=recon,
            partial_pipeline=partial_pipeline,
            preview_schema_version=COPY_PREVIEW_SCHEMA_VERSION,
        )
    return {
        "existing_layout_analysis": existing_layout_analysis_to_json(analysis),
        "mining_layout_engine": "v2",
        "reconstruction": to_jsonable(recon),
        "partial_pipeline": partial_pipeline,
        "reconstruction_summary": reconstruction_summary,
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
