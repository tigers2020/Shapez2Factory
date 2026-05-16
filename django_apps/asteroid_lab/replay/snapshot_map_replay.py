"""Full-map snapshot steps for lab replay (output-only; not solver input)."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from typing import Any

from django_apps.asteroid_lab.replay.deconstruction_frames import load_cleanup_result
from django_apps.asteroid_lab.replay.reconstruction_frames import run_topology_reconstruction
from django_apps.asteroid_lab.services.dto import (
    DecodedBlueprintSnapshotDTO,
    DecodedCellDTO,
    ExistingLayoutInspectionDTO,
)
from django_apps.asteroid_lab.snapshots.transport_components import (
    is_transport_tile,
)


def cell_key_xy_layer(row: dict[str, Any]) -> tuple[int, int, int | None]:
    layer = row.get("layer")
    ly: int | None = None if layer is None else int(layer)
    return (int(row["x"]), int(row["y"]), ly)


EQUIPMENT_KINDS_FOR_ISSUE_FILTER = frozenset(
    {
        "fluid_miner",
        "fluid_miner_extension",
        "shape_miner",
        "shape_miner_extension",
    }
)

TRANSPORT_TILE_KINDS_FOR_ISSUE_FILTER = frozenset({"space_pipe", "space_belt"})


def filter_issue_cells_for_full_map(
    issue_cells: list[dict[str, Any]],
    full_map_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Drop stale issue rows vs ``full_map`` at (x,y,layer).

    - Equipment: same as before — drop when full_map cell_kind no longer matches.
    - Transport tiles: drop when full_map has no ``space_pipe`` / ``space_belt`` at that
      coordinate (e.g. reconstruction stripped transport; ``transport_disconnected``).
    """

    by_key: dict[tuple[int, int, int | None], dict[str, Any]] = {}
    for r in full_map_rows:
        if not isinstance(r, dict):
            continue
        try:
            by_key[cell_key_xy_layer(r)] = r
        except (KeyError, TypeError, ValueError):
            continue

    out: list[dict[str, Any]] = []
    for ic in issue_cells:
        if not isinstance(ic, dict):
            continue
        ck = ic.get("cell_kind")
        ck_s = ck if isinstance(ck, str) else ""
        if not ck_s and str(ic.get("issue_code") or "") == "miner_attached_to_orphan_transport":
            try:
                key_mt = cell_key_xy_layer(ic)
            except (KeyError, TypeError, ValueError):
                continue
            base_mt = by_key.get(key_mt)
            base_mt_ck = base_mt.get("cell_kind") if isinstance(base_mt, dict) else None
            base_mt_s = base_mt_ck if isinstance(base_mt_ck, str) else ""
            if base_mt_s not in TRANSPORT_TILE_KINDS_FOR_ISSUE_FILTER:
                continue
            out.append(ic)
            continue
        if ck_s in TRANSPORT_TILE_KINDS_FOR_ISSUE_FILTER:
            try:
                key = cell_key_xy_layer(ic)
            except (KeyError, TypeError, ValueError):
                out.append(ic)
                continue
            base = by_key.get(key)
            base_ck = base.get("cell_kind") if isinstance(base, dict) else None
            base_s = base_ck if isinstance(base_ck, str) else ""
            if base_s in TRANSPORT_TILE_KINDS_FOR_ISSUE_FILTER:
                out.append(ic)
            continue
        if ck_s not in EQUIPMENT_KINDS_FOR_ISSUE_FILTER:
            out.append(ic)
            continue
        try:
            key = cell_key_xy_layer(ic)
        except (KeyError, TypeError, ValueError):
            out.append(ic)
            continue
        base = by_key.get(key)
        if base is None:
            out.append(ic)
            continue
        base_ck = base.get("cell_kind")
        if base_ck != ck_s:
            continue
        out.append(ic)
    return out


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
    if cell.server_x is not None and cell.server_y is not None:
        row["server_x"] = cell.server_x
        row["server_y"] = cell.server_y
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
        server_x=source.server_x,
        server_y=source.server_y,
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


def issue_overlay_cells(inspection: ExistingLayoutInspectionDTO) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for iss in inspection.issues:
        for cell in iss.cells_json:
            out.append(
                {
                    **cell,
                    "overlay_role": "issue",
                    "issue_code": iss.issue_code,
                    "severity": iss.severity,
                    "equipment_id": iss.equipment_id,
                }
            )
    return out


__all__ = [
    "build_cleanup_and_reconstruction_rows",
    "cell_key_xy_layer",
    "decode_snapshot_summary",
    "decoded_cell_to_full_map_row",
    "diff_maps",
    "filter_issue_cells_for_full_map",
    "issue_overlay_cells",
    "rows_from_cells",
    "snapshot_summary_from_rows",
]
