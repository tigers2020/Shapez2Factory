"""Build full_map lab JSON + copy string for ``ReconstructedAsteroidMap`` persistence."""

from __future__ import annotations

import copy
from dataclasses import dataclass

from django_apps.asteroid_lab.adapters.reconstruction_blueprint_export import (
    build_reconstructed_normalized_dto,
    encode_reconstructed_copy_string,
)
from django_apps.asteroid_lab.cleanup.result import CleanupResult
from django_apps.asteroid_lab.reconstruction.confidence import reconstruction_persist_summary
from django_apps.asteroid_lab.reconstruction.display_map import (
    merged_display_cells_from_reconstruction,
)
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.snapshots.island_bbox import island_bbox_from_cells


@dataclass(frozen=True, slots=True)
class ReconstructedMapPersistPayload:
    """ORM-ready payload: original snapshot + full_map reconstruction (no replay reads)."""

    original_copy_code: str
    original_decoded_json: dict[str, object]
    copy_code: str
    decoded_json: dict[str, object]


def build_reconstructed_map_persist_payload(
    *,
    map_input_id: int,
    run_key: str,
    recon: ReconstructionResult,
    cleanup: CleanupResult | None = None,
    original_copy_code: str = "",
    original_decoded_json: dict[str, object] | None = None,
    source_decoded_json: dict[str, object] | None = None,
) -> ReconstructedMapPersistPayload:
    """Assemble full_map lab copy + JSON from reconstruction/cleanup (no replay I/O)."""

    if cleanup is None:
        msg = "build_reconstructed_map_persist_payload requires cleanup for full_map merge"
        raise ValueError(msg)

    merged = merged_display_cells_from_reconstruction(cleanup, recon)
    full_map_bbox = island_bbox_from_cells(merged)
    if full_map_bbox is None:
        msg = "full_map merge produced no cells for island bbox"
        raise ValueError(msg)

    norm = build_reconstructed_normalized_dto(
        merged,
        source_decoded_json=source_decoded_json,
        map_input_id=map_input_id,
        run_key=run_key.strip(),
        summary_json=reconstruction_persist_summary(recon),
        full_map_island_bbox=full_map_bbox,
    )
    decoded = dict(norm.decoded_json)
    copy_code = encode_reconstructed_copy_string(decoded)

    orig_json = copy.deepcopy(original_decoded_json) if original_decoded_json else {}

    return ReconstructedMapPersistPayload(
        original_copy_code=(original_copy_code or "").strip(),
        original_decoded_json=orig_json,
        copy_code=copy_code,
        decoded_json=decoded,
    )


__all__ = [
    "ReconstructedMapPersistPayload",
    "build_reconstructed_map_persist_payload",
]
