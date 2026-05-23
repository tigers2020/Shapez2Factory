"""Reconstruction-complete display map: structural cleanup rows merged with recon overlay.

Shared by replay ``reconstruction_final`` / ``reconstruction_complete`` and ORM persist.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from django_apps.asteroid_lab.cleanup.result import CleanupResult
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.replay.snapshot_map_replay import (
    _replace_extensions_with_synthetic_fields as replace_extensions_with_synthetic_fields,
)
from django_apps.asteroid_lab.replay.snapshot_map_replay import (
    _replace_miners_with_synthetic_fields as replace_miners_with_synthetic_fields,
)
from django_apps.asteroid_lab.replay.snapshot_map_replay import (
    cell_key_xy_layer,
    decoded_cell_to_full_map_row,
    rows_from_cells,
)
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.transport_components import (
    is_transport_tile,
    sort_key_xy_layer,
)


def structural_cells_from_cleanup(cleanup: CleanupResult) -> tuple[DecodedCellDTO, ...]:
    """Post-extension-cleanup cells (replay ``row_extension`` parity)."""

    after_transport = tuple(c for c in cleanup.original_cells if not is_transport_tile(c))
    after_extractors = replace_miners_with_synthetic_fields(after_transport)
    return replace_extensions_with_synthetic_fields(after_extractors)


def merge_reconstruction_display_cells(
    structural: Sequence[DecodedCellDTO],
    recon_cells: Sequence[DecodedCellDTO],
) -> tuple[DecodedCellDTO, ...]:
    """Overlay recon on structural map; keep structural keys absent from ``recon_cells``."""

    merged: dict[tuple[int, int, int | None], DecodedCellDTO] = {
        (c.x, c.y, c.layer): c for c in structural
    }
    for cell in recon_cells:
        merged[(cell.x, cell.y, cell.layer)] = cell
    return tuple(sorted(merged.values(), key=sort_key_xy_layer))


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


def merged_display_cells_from_reconstruction(
    cleanup: CleanupResult,
    recon: ReconstructionResult,
) -> tuple[DecodedCellDTO, ...]:
    """Full topology cell set for persist (no replay frame reads)."""

    structural = structural_cells_from_cleanup(cleanup)
    return merge_reconstruction_display_cells(structural, recon.cells)


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


def full_map_server_bbox_from_decoded_json(decoded_json: dict[str, Any]) -> dict[str, int] | None:
    """Legacy dense bbox meta (read-compat). Prefer ``full_map_island_bbox_from_decoded_json``."""

    island = full_map_island_bbox_from_decoded_json(decoded_json)
    if island is not None:
        return {
            "server_min_x": island["min_x"],
            "server_max_x": island["max_x"],
            "server_min_y": island["min_y"],
            "server_max_y": island["max_y"],
            "server_width": island["width"],
            "server_height": island["height"],
        }
    meta = reconstruction_meta_from_decoded_json(decoded_json)
    bb = meta.get("full_map_server_bbox")
    if not isinstance(bb, dict):
        return None
    if "server_width" not in bb or "server_height" not in bb:
        return None
    return dict(bb)


def server_bbox_from_cells(cells: Sequence[DecodedCellDTO]) -> dict[str, int]:
    """Server grid bbox from cells with ``server_x`` / ``server_y`` attached."""

    sxs = [int(c.server_x) for c in cells if isinstance(c.server_x, int)]
    sys_ = [int(c.server_y) for c in cells if isinstance(c.server_y, int)]
    if not sxs or not sys_:
        return {
            "server_min_x": 0,
            "server_max_x": 0,
            "server_min_y": 0,
            "server_max_y": 0,
            "server_width": 0,
            "server_height": 0,
        }
    mn_x, mx_x = min(sxs), max(sxs)
    mn_y, mx_y = min(sys_), max(sys_)
    return {
        "server_min_x": mn_x,
        "server_max_x": mx_x,
        "server_min_y": mn_y,
        "server_max_y": mx_y,
        "server_width": mx_x - mn_x + 1,
        "server_height": mx_y - mn_y + 1,
    }


__all__ = [
    "full_map_rows_from_reconstruction",
    "full_map_island_bbox_from_decoded_json",
    "full_map_server_bbox_from_decoded_json",
    "merge_reconstruction_display_cells",
    "merge_reconstruction_display_rows",
    "merged_display_cells_from_reconstruction",
    "replace_extensions_with_synthetic_fields",
    "replace_miners_with_synthetic_fields",
    "reconstruction_meta_from_decoded_json",
    "reconstruction_summary_from_decoded_json",
    "server_bbox_from_cells",
    "structural_cells_from_cleanup",
]
