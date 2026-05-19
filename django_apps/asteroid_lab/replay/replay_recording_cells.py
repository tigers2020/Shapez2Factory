"""Output-only helpers: build optimization replay cell dicts from runtime snapshots."""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab.optimization.candidate_dtos import GeneCandidate
from django_apps.asteroid_lab.optimization.commit_best_candidates import ConfirmedGenePlacement
from django_apps.asteroid_lab.optimization.enums import TransportKind
from django_apps.asteroid_lab.optimization.loaded_snapshot import LoadedReconstructionSnapshot
from django_apps.asteroid_lab.optimization.materialization_dtos import RouteMaterializationResult
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_loaded_snapshot,
)
from django_apps.asteroid_lab.services.dto import DecodedCellDTO

# JS ``toneForFullMapCell`` recognises "space_belt"/"space_pipe" (cyan) for transport cells.
_TRANSPORT_TO_BELT_CELL_KIND: dict[str, str] = {
    TransportKind.SHAPE_BELT.value: "space_belt",
    TransportKind.FLUID_PIPE.value: "space_pipe",
}

# JS amber tone for extractors; transport_kind determines shape vs fluid variant.
_TRANSPORT_TO_EXTRACTOR_KIND: dict[str, str] = {
    TransportKind.SHAPE_BELT.value: "shape_miner",
    TransportKind.FLUID_PIPE.value: "fluid_miner",
}

_TRANSPORT_TO_EXTENSION_KIND: dict[str, str] = {
    TransportKind.SHAPE_BELT.value: "shape_miner_extension",
    TransportKind.FLUID_PIPE.value: "fluid_miner_extension",
}


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
    """Materialized transport (belt/pipe) cells as overlay wire rows.

    Uses JS-recognised ``cell_kind`` values (``"space_belt"`` / ``"space_pipe"``) so
    ``toneForFullMapCell`` can colour them cyan instead of falling back to default violet.
    """
    if materialization.layout is None:
        return ()
    return tuple(
        {
            "server_x": int(c.coord[0]),
            "server_y": int(c.coord[1]),
            "cell_kind": _TRANSPORT_TO_BELT_CELL_KIND.get(
                c.transport_kind.value, c.transport_kind.value
            ),
            "transport_kind": c.transport_kind.value,
        }
        for c in materialization.layout.cells
    )


def miner_cell_dicts_from_confirmed(
    confirmed: tuple[ConfirmedGenePlacement, ...],
    candidates_by_id: dict[str, GeneCandidate],
) -> tuple[dict[str, Any], ...]:
    """Extractor + extension cells for confirmed placements as overlay wire rows.

    Uses JS-recognised ``cell_kind`` values (``"shape_miner"`` / ``"fluid_miner"`` and their
    ``_extension`` variants) so ``toneForFullMapCell`` colours them amber.
    """
    rows: list[dict[str, Any]] = []
    for placement in confirmed:
        candidate = candidates_by_id.get(placement.candidate_id)
        if candidate is None:
            continue
        tk = candidate.transport_kind.value
        extractor_kind = _TRANSPORT_TO_EXTRACTOR_KIND.get(tk, "shape_miner")
        ext_kind = _TRANSPORT_TO_EXTENSION_KIND.get(tk, "shape_miner_extension")
        rows.append(
            {
                "server_x": int(candidate.extractor[0]),
                "server_y": int(candidate.extractor[1]),
                "cell_kind": extractor_kind,
                "transport_kind": tk,
            }
        )
        for ext in candidate.extensions:
            rows.append(
                {
                    "server_x": int(ext[0]),
                    "server_y": int(ext[1]),
                    "cell_kind": ext_kind,
                    "transport_kind": tk,
                }
            )
    return tuple(rows)
