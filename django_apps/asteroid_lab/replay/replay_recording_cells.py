"""Output-only helpers: build optimization replay cell dicts from runtime snapshots."""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab.optimization.loaded_snapshot import LoadedReconstructionSnapshot
from django_apps.asteroid_lab.optimization.materialization_dtos import RouteMaterializationResult
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_loaded_snapshot,
)
from django_apps.asteroid_lab.services.dto import DecodedCellDTO


def visible_cell_dicts_from_loaded(
    loaded: LoadedReconstructionSnapshot,
) -> tuple[dict[str, Any], ...]:
    """Mineable cells as server-grid wire rows for ``RuntimeReplayRecorder``."""

    inp = optimization_input_from_loaded_snapshot(loaded)
    by_server: dict[tuple[int, int], DecodedCellDTO] = {}
    for cell in loaded.cells:
        if isinstance(cell.server_x, int) and isinstance(cell.server_y, int):
            by_server[(int(cell.server_x), int(cell.server_y))] = cell

    rows: list[dict[str, Any]] = []
    for coord in sorted(inp.mineable_cells, key=lambda c: (c[1], c[0])):
        decoded = by_server.get(coord)
        rows.append(
            {
                "server_x": int(coord[0]),
                "server_y": int(coord[1]),
                "cell_kind": str(decoded.cell_kind) if decoded is not None else "asteroid",
                "transport_kind": str(decoded.transport_kind) if decoded is not None else "none",
            }
        )
    return tuple(rows)


def overlay_cell_dicts_from_materialization(
    materialization: RouteMaterializationResult,
) -> tuple[dict[str, Any], ...]:
    """Materialized transport cells as overlay wire rows."""

    if materialization.layout is None:
        return ()
    return tuple(
        {
            "server_x": int(c.coord[0]),
            "server_y": int(c.coord[1]),
            "cell_kind": "route_materialized",
            "transport_kind": c.transport_kind.value,
        }
        for c in materialization.layout.cells
    )
