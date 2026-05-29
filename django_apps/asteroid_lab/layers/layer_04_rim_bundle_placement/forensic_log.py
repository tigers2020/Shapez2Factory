"""Layer 04 selected-placement forensic JSONL (observability only; not solver input)."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any, cast

from django_apps.asteroid_lab.layers.contracts.candidates import BundlePlacement
from django_apps.asteroid_lab.layers.contracts.layer_slugs import LAYER_04_RIM_BUNDLE_PLACEMENT
from django_apps.asteroid_lab.layers.contracts.rim_placement import RimBundlePlacement
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

LAYER04_SELECTED_PLACEMENTS_FILENAME = "layer_04_selected_placements.jsonl"
RECORD_TYPE_LAYER04_SELECTED_PLACEMENT = "layer04_selected_placement"


def _coord_wire(coord: Coord) -> dict[str, int]:
    x, y = coord
    return {"x": x, "y": y}


def _sorted_coord_wires(cells: frozenset[Coord] | tuple[Coord, ...]) -> list[dict[str, int]]:
    return [_coord_wire(c) for c in sorted(cells, key=lambda c: (c[0], c[1]))]


def _cell_placement_wire(cell: BundlePlacement) -> dict[str, Any]:
    x, y = cell.coord
    return {
        "x": x,
        "y": y,
        "layout_t": cell.layout_t,
        "rotation": cell.rotation,
        "cell_role": cell.cell_role.value,
    }


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return str(value)


def build_layer04_selected_placement_record(placement: RimBundlePlacement) -> dict[str, Any]:
    """One forensic JSONL row for a single L4 selected placement."""
    cell_rows = [_cell_placement_wire(cell) for cell in placement.cell_placements]
    cell_rows.sort(key=lambda row: (row["x"], row["y"], row["cell_role"]))
    record: dict[str, Any] = {
        "record_type": RECORD_TYPE_LAYER04_SELECTED_PLACEMENT,
        "layer_slug": LAYER_04_RIM_BUNDLE_PLACEMENT,
        "candidate_id": placement.candidate_id,
        "placement_id": placement.placement_id,
        "equivalence_key": placement.equivalence_key,
        "gene_key": placement.gene_key,
        "anchor_coord": _coord_wire(placement.anchor_coord),
        "transport_kind": placement.transport_kind.value,
        "resource_kind": placement.resource_kind.value,
        "extractor_cells": _sorted_coord_wires(placement.extractor_cells),
        "extension_cells": _sorted_coord_wires(placement.extension_cells),
        "output_stub_cells": _sorted_coord_wires(placement.output_stub_cells),
        "cell_placements": cell_rows,
        "probed_route_path_cells": _sorted_coord_wires(placement.probed_route_path_cells),
    }
    return cast(dict[str, Any], _json_safe(record))


def write_layer04_selected_placements_log(
    *,
    run_dir: Path,
    selected_placements: tuple[RimBundlePlacement, ...],
) -> Path:
    """Write ``layer_04_selected_placements.jsonl`` under the layer-stack run directory."""
    path = run_dir / LAYER04_SELECTED_PLACEMENTS_FILENAME
    ordered = sorted(selected_placements, key=lambda p: p.candidate_id)
    lines: list[str] = []
    for placement in ordered:
        row = build_layer04_selected_placement_record(placement)
        lines.append(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    if lines:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    else:
        path.write_text("", encoding="utf-8")
    return path


__all__ = [
    "LAYER04_SELECTED_PLACEMENTS_FILENAME",
    "RECORD_TYPE_LAYER04_SELECTED_PLACEMENT",
    "build_layer04_selected_placement_record",
    "write_layer04_selected_placements_log",
]
