"""Full-map snapshot steps for lab replay (output-only; not solver input)."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from typing import Any

from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.replay.deconstruction_frames import load_cleanup_result
from django_apps.asteroid_lab.services.dto import (
    DecodedBlueprintSnapshotDTO,
    DecodedCellDTO,
)
from django_apps.asteroid_lab.snapshots.transport_components import (
    is_transport_tile,
)


def cell_key_xy_layer(row: dict[str, Any]) -> tuple[int, int, int | None]:
    layer = row.get("layer")
    ly: int | None = None if layer is None else int(layer)
    return (int(row["x"]), int(row["y"]), ly)


def decoded_cell_to_full_map_row(cell: DecodedCellDTO, **extra: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
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


def rows_from_cells(cells: Sequence[DecodedCellDTO], **extra: Any) -> list[dict[str, Any]]:
    return [decoded_cell_to_full_map_row(c, **extra) for c in cells]


def diff_maps(prev: Sequence[dict[str, Any]], nxt: Sequence[dict[str, Any]]) -> dict[str, Any]:
    pk = {cell_key_xy_layer(r): r for r in prev}
    nk = {cell_key_xy_layer(r): r for r in nxt}
    removed = [pk[k] for k in pk if k not in nk]
    added = [nk[k] for k in nk if k not in pk]
    changed: list[dict[str, Any]] = []
    for k, before in pk.items():
        if k not in nk:
            continue
        after = nk[k]
        if before != after:
            changed.append({"before": before, "after": after})
    return {"added": added, "removed": removed, "changed": changed}


def _without_transport(c: DecodedCellDTO) -> bool:
    return not is_transport_tile(c)


def _synthetic_asteroid_field_cell(source: DecodedCellDTO, field_cell_kind: str) -> DecodedCellDTO:
    """Replay-only cell: same (x,y,layer) as removed miner/extension; not in decode BP."""

    return DecodedCellDTO(
        x=source.x,
        y=source.y,
        layer=source.layer,
        rotation=0,
        tile_type="",
        cell_kind=field_cell_kind,
        transport_kind="none",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={"_replay_synthetic": True, "_from_cell_kind": source.cell_kind},
    )


def _field_cell_kind_for_miner(c: DecodedCellDTO) -> str:
    return "asteroid_shape_field" if c.cell_kind == "shape_miner" else "asteroid_fluid_field"


def _field_cell_kind_for_extension(c: DecodedCellDTO) -> str:
    if c.cell_kind == "shape_miner_extension":
        return "asteroid_shape_field"
    return "asteroid_fluid_field"


def _replace_miners_with_synthetic_fields(
    cells: Sequence[DecodedCellDTO],
) -> tuple[DecodedCellDTO, ...]:
    out: list[DecodedCellDTO] = []
    for c in cells:
        if c.cell_kind in ("fluid_miner", "shape_miner"):
            out.append(_synthetic_asteroid_field_cell(c, _field_cell_kind_for_miner(c)))
        else:
            out.append(c)
    return tuple(out)


def _replace_extensions_with_synthetic_fields(
    cells: Sequence[DecodedCellDTO],
) -> tuple[DecodedCellDTO, ...]:
    out: list[DecodedCellDTO] = []
    for c in cells:
        if c.cell_kind in ("fluid_miner_extension", "shape_miner_extension"):
            out.append(_synthetic_asteroid_field_cell(c, _field_cell_kind_for_extension(c)))
        else:
            out.append(c)
    return tuple(out)


def snapshot_summary_from_rows(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
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


def decode_snapshot_summary(snapshot: DecodedBlueprintSnapshotDTO) -> dict[str, Any]:
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
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
]:
    """Return full_map rows for transport / extractor / extension cleanup and reconstruction."""

    all_cells = snapshot.cells
    after_transport = tuple(c for c in all_cells if _without_transport(c))
    after_extractors = _replace_miners_with_synthetic_fields(after_transport)
    after_extensions = _replace_extensions_with_synthetic_fields(after_extractors)
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
    "build_cleanup_and_reconstruction_rows",
    "cell_key_xy_layer",
    "decode_snapshot_summary",
    "decoded_cell_to_full_map_row",
    "diff_maps",
    "rows_from_cells",
    "snapshot_summary_from_rows",
]
