"""Reconstruction-complete display map: structural cleanup rows merged with recon overlay.

Viewer / persist side (Django). The pure cell-level merge + synthetic-field transforms now live in
``shapez2_factory.domain.asteroid_lab.reconstruction.complete_map_merge`` (PR-CLI-2c) and are
re-exported here for back-compat. Row-dict shaping (``rows_from_cells`` etc.) stays replay-side.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from django_apps.asteroid_lab.replay.snapshot_map_replay import (
    cell_key_xy_layer,
    decoded_cell_to_full_map_row,
    rows_from_cells,
)
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from shapez2_factory.domain.asteroid_lab.cleanup.result import CleanupResult
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map_merge import (
    merge_reconstruction_display_cells,
    merged_display_cells_from_reconstruction,
    replace_extensions_with_synthetic_fields,
    replace_miners_with_synthetic_fields,
    structural_cells_from_cleanup,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.result import ReconstructionResult


def merge_reconstruction_display_rows(
    structural_rows: Sequence[dict[str, Any]],
    recon_cells: Sequence[DecodedCellDTO],
) -> list[dict[str, Any]]:
    """Row dict merge for replay (structural full_map rows + recon overlay)."""

    merged: dict[tuple[int, int, int | None], dict[str, Any]] = {}
    for r in structural_rows:
        if not isinstance(r, dict):
            continue
        try:
            merged[cell_key_xy_layer(r)] = dict(r)
        except (KeyError, TypeError, ValueError):
            continue
    for cell in recon_cells:
        merged[cell_key_xy_layer(decoded_cell_to_full_map_row(cell))] = (
            decoded_cell_to_full_map_row(cell)
        )
    return sorted(merged.values(), key=lambda row: cell_key_xy_layer(row))


def full_map_rows_from_reconstruction(
    cleanup: CleanupResult,
    recon: ReconstructionResult,
) -> list[dict[str, Any]]:
    """Full_map row list equivalent to replay ``reconstruction_complete``."""

    return rows_from_cells(merged_display_cells_from_reconstruction(cleanup, recon))


_RECON_META_KEY = "_asteroid_lab_reconstruction"


def reconstruction_meta_from_decoded_json(decoded_json: dict[str, Any]) -> dict[str, Any]:
    """``_asteroid_lab_reconstruction`` block from persisted ``decoded_json``."""

    meta = decoded_json.get(_RECON_META_KEY)
    return dict(meta) if isinstance(meta, dict) else {}


def reconstruction_summary_from_decoded_json(decoded_json: dict[str, Any]) -> dict[str, Any]:
    """Persisted confidence / reconstruction counters (if present)."""

    meta = reconstruction_meta_from_decoded_json(decoded_json)
    summary = meta.get("summary_json")
    return dict(summary) if isinstance(summary, dict) else {}


def full_map_island_bbox_from_decoded_json(decoded_json: dict[str, Any]) -> dict[str, int] | None:
    """Topology extent from persist (island-local; PR-F Wave C)."""

    from django_apps.asteroid_lab.snapshots.island_bbox import (
        full_map_island_bbox_from_decoded_json as _island_bbox,
    )

    return _island_bbox(decoded_json)


__all__ = [
    "full_map_rows_from_reconstruction",
    "full_map_island_bbox_from_decoded_json",
    "merge_reconstruction_display_cells",
    "merge_reconstruction_display_rows",
    "merged_display_cells_from_reconstruction",
    "replace_extensions_with_synthetic_fields",
    "replace_miners_with_synthetic_fields",
    "reconstruction_meta_from_decoded_json",
    "reconstruction_summary_from_decoded_json",
    "structural_cells_from_cleanup",
]
