"""Full-map snapshot steps for lab replay (output-only; not solver input)."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from typing import Any

from django_apps.asteroid_lab.services.dto import (
    DecodedBlueprintSnapshotDTO,
    DecodedCellDTO,
    ExistingLayoutInspectionDTO,
)
from django_apps.asteroid_lab.snapshots.transport_components import (
    is_transport_tile,
    iter_four_neighbors,
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


def _without_extractors(c: DecodedCellDTO) -> bool:
    return c.cell_kind not in ("fluid_miner", "shape_miner")


def _without_extensions(c: DecodedCellDTO) -> bool:
    return c.cell_kind not in ("fluid_miner_extension", "shape_miner_extension")


def _infer_internal_void_rows(remaining: Sequence[DecodedCellDTO]) -> list[dict[str, Any]]:
    """Flood-fill from padded AABB border; unreachable empty cells → internal_void."""

    if not remaining:
        return []
    xs = [c.x for c in remaining]
    ys = [c.y for c in remaining]
    mn_x, mx_x = min(xs), max(xs)
    mn_y, mx_y = min(ys), max(ys)
    pad = 1
    w0, w1 = mn_x - pad, mx_x + pad
    if w0 == 0:
        w0 = -1
    h0, h1 = mn_y - pad, mx_y + pad
    occupied = {(c.x, c.y) for c in remaining}
    from collections import deque

    q: deque[tuple[int, int]] = deque()
    seen: set[tuple[int, int]] = set()

    def try_enqueue(x: int, y: int) -> None:
        if x == 0:
            return
        if x < w0 or x > w1 or y < h0 or y > h1:
            return
        if (x, y) in occupied or (x, y) in seen:
            return
        seen.add((x, y))
        q.append((x, y))

    for x in range(w0, w1 + 1):
        if x == 0:
            continue
        try_enqueue(x, h0)
        try_enqueue(x, h1)
    for y in range(h0, h1 + 1):
        if w0 != 0:
            try_enqueue(w0, y)
        if w1 != 0:
            try_enqueue(w1, y)

    while q:
        x, y = q.popleft()
        for nx, ny, _nl in iter_four_neighbors(x, y, None):
            try_enqueue(nx, ny)

    voids: list[dict[str, Any]] = []
    for x in range(mn_x, mx_x + 1):
        if x == 0:
            continue
        for y in range(mn_y, mx_y + 1):
            if (x, y) in occupied:
                continue
            if (x, y) in seen:
                continue
            voids.append(
                {
                    "x": x,
                    "y": y,
                    "layer": None,
                    "rotation": 0,
                    "cell_kind": "internal_void",
                    "transport_kind": "none",
                    "tile_type": "",
                    "replay_role": "internal_void",
                }
            )
    return voids


def snapshot_summary_from_rows(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    ck = Counter(str(r.get("cell_kind") or "") for r in rows)

    def n(*kinds: str) -> int:
        return sum(int(ck[k]) for k in kinds)

    return {
        "cell_kind_counts": dict(ck),
        "extractor_count": n("fluid_miner", "shape_miner"),
        "extension_count": n("fluid_miner_extension", "shape_miner_extension"),
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
]:
    """Return full_map rows for transport / extractor / extension cleanup and reconstruction."""

    all_cells = snapshot.cells
    after_transport = tuple(c for c in all_cells if _without_transport(c))
    after_extractors = tuple(c for c in after_transport if _without_extractors(c))
    after_extensions = tuple(c for c in after_extractors if _without_extensions(c))
    void_rows = _infer_internal_void_rows(after_extensions)
    structural = rows_from_cells(after_extensions)
    reconstruction = structural + void_rows
    return (
        rows_from_cells(all_cells),
        rows_from_cells(after_transport),
        rows_from_cells(after_extractors),
        structural,
        reconstruction,
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
    "decode_snapshot_summary",
    "decoded_cell_to_full_map_row",
    "diff_maps",
    "issue_overlay_cells",
    "rows_from_cells",
    "snapshot_summary_from_rows",
]
