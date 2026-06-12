"""Full-map snapshot steps for lab replay (output-only; not solver input)."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.replay.deconstruction_frames import load_cleanup_result
from django_apps.asteroid_lab.services.dto import (
    DecodedBlueprintSnapshotDTO,
    DecodedCellDTO,
)
from django_apps.asteroid_lab.snapshots.transport_components import (
    is_transport_tile,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map_merge import (
    replace_extensions_with_synthetic_fields,
    replace_miners_with_synthetic_fields,
)

FullMapRow = dict[str, object]


def _row_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, (float, str)):
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0
    return 0


def cell_key_xy_layer(row: FullMapRow) -> tuple[int, int, int | None]:
    layer = row.get("layer")
    ly: int | None = None if layer is None else _row_int(layer)
    return (_row_int(row["x"]), _row_int(row["y"]), ly)


def decoded_cell_to_full_map_row(cell: DecodedCellDTO, **extra: object) -> FullMapRow:
    row: FullMapRow = {
        "x": cell.x,
        "y": cell.y,
        "layer": cell.layer,
        "rotation": cell.rotation,
        "cell_kind": cell.cell_kind,
        "transport_kind": cell.transport_kind,
        "tile_type": cell.tile_type,
    }
    row.update(extra)
    return row


def rows_from_cells(cells: Sequence[DecodedCellDTO], **extra: object) -> list[FullMapRow]:
    return [decoded_cell_to_full_map_row(c, **extra) for c in cells]


def diff_maps(prev: Sequence[FullMapRow], nxt: Sequence[FullMapRow]) -> dict[str, object]:
    pk = {cell_key_xy_layer(r): r for r in prev}
    nk = {cell_key_xy_layer(r): r for r in nxt}
    removed = [pk[k] for k in pk if k not in nk]
    added = [nk[k] for k in nk if k not in pk]
    changed: list[dict[str, object]] = []
    for k, before in pk.items():
        if k not in nk:
            continue
        after = nk[k]
        if before != after:
            changed.append({"before": before, "after": after})
    return {"added": added, "removed": removed, "changed": changed}


def _without_transport(c: DecodedCellDTO) -> bool:
    return not is_transport_tile(c)


def snapshot_summary_from_rows(rows: Sequence[FullMapRow]) -> dict[str, object]:
    ck = Counter(str(r.get("cell_kind") or "") for r in rows)

    def n(*kinds: str) -> int:
        return sum(int(ck[k]) for k in kinds)

    return {
        "cell_kind_counts": dict(ck),
        "extractor_count": n("fluid_miner", "shape_miner"),
        "extension_count": n("fluid_miner_extension", "shape_miner_extension"),
        "field_count": n("asteroid_fluid_field", "asteroid_shape_field"),
        "belt_count": int(ck.get("space_belt", 0)),
        "pipe_count": int(ck.get("space_pipe", 0)),
        "internal_void_count": int(ck.get("internal_void", 0)),
        "total_cells": len(rows),
    }


def decode_snapshot_summary(snapshot: DecodedBlueprintSnapshotDTO) -> dict[str, object]:
    ck = dict(snapshot.cell_kind_counts_json)

    def n(*kinds: str) -> int:
        return sum(int(ck.get(k, 0)) for k in kinds)

    return {
        "entry_count": snapshot.entry_count,
        "blueprint_type": snapshot.blueprint_type,
        "binary_version": snapshot.binary_version,
        "bbox": dict(snapshot.bbox_json),
        "cell_kind_counts": dict(ck),
        "transport_kind_counts": dict(snapshot.transport_kind_counts_json),
        "extractor_count": n("fluid_miner", "shape_miner"),
        "extension_count": n("fluid_miner_extension", "shape_miner_extension"),
        "belt_count": int(ck.get("space_belt", 0)),
        "pipe_count": int(ck.get("space_pipe", 0)),
    }


def build_cleanup_and_reconstruction_rows(
    snapshot: DecodedBlueprintSnapshotDTO,
) -> tuple[
    list[FullMapRow],
    list[FullMapRow],
    list[FullMapRow],
    list[FullMapRow],
    list[FullMapRow],
    dict[str, object],
]:
    """Return full_map rows for transport / extractor / extension cleanup and reconstruction."""

    all_cells = snapshot.cells
    after_transport = tuple(c for c in all_cells if _without_transport(c))
    after_extractors = replace_miners_with_synthetic_fields(after_transport)
    after_extensions = replace_extensions_with_synthetic_fields(after_extractors)
    structural = rows_from_cells(after_extensions)
    cleanup = load_cleanup_result(snapshot)
    recon = run_topology_reconstruction(cleanup)
    reconstruction = rows_from_cells(recon.cells)
    recon_summary = {**dict(cleanup.summary_json), **dict(recon.summary_json)}
    return (
        rows_from_cells(all_cells),
        rows_from_cells(after_transport),
        rows_from_cells(after_extractors),
        structural,
        reconstruction,
        dict(recon_summary),
    )


__all__ = [
    "FullMapRow",
    "build_cleanup_and_reconstruction_rows",
    "cell_key_xy_layer",
    "decode_snapshot_summary",
    "decoded_cell_to_full_map_row",
    "diff_maps",
    "rows_from_cells",
    "snapshot_summary_from_rows",
]
