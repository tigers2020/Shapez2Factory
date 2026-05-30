"""Pure cell-level reconstruction-complete merge (PR-CLI-2c display_map split).

Core-pure structural transforms shared by the Django viewer (``reconstruction/display_map.py``),
replay row shaping (``replay/snapshot_map_replay.py``), and the reconstruction pipeline. Operates
on ``DecodedCellDTO`` only — never reads replay frames or produces full_map row dicts (that shaping
stays Django-side). ``build_reconstruction_complete_map`` consumes
``merged_display_cells_from_reconstruction``.
"""

from __future__ import annotations

from collections.abc import Sequence

from shapez2_factory.domain.asteroid_lab.cleanup.result import CleanupResult
from shapez2_factory.domain.asteroid_lab.decoded_cell import DecodedCellDTO
from shapez2_factory.domain.asteroid_lab.reconstruction.result import ReconstructionResult
from shapez2_factory.domain.asteroid_lab.transport_components import (
    is_transport_tile,
    sort_key_xy_layer,
)


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


def replace_miners_with_synthetic_fields(
    cells: Sequence[DecodedCellDTO],
) -> tuple[DecodedCellDTO, ...]:
    out: list[DecodedCellDTO] = []
    for c in cells:
        if c.cell_kind in ("fluid_miner", "shape_miner"):
            out.append(_synthetic_asteroid_field_cell(c, _field_cell_kind_for_miner(c)))
        else:
            out.append(c)
    return tuple(out)


def replace_extensions_with_synthetic_fields(
    cells: Sequence[DecodedCellDTO],
) -> tuple[DecodedCellDTO, ...]:
    out: list[DecodedCellDTO] = []
    for c in cells:
        if c.cell_kind in ("fluid_miner_extension", "shape_miner_extension"):
            out.append(_synthetic_asteroid_field_cell(c, _field_cell_kind_for_extension(c)))
        else:
            out.append(c)
    return tuple(out)


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


def merged_display_cells_from_reconstruction(
    cleanup: CleanupResult,
    recon: ReconstructionResult,
) -> tuple[DecodedCellDTO, ...]:
    """Full topology cell set for persist (no replay frame reads)."""

    structural = structural_cells_from_cleanup(cleanup)
    return merge_reconstruction_display_cells(structural, recon.cells)


__all__ = [
    "merge_reconstruction_display_cells",
    "merged_display_cells_from_reconstruction",
    "replace_extensions_with_synthetic_fields",
    "replace_miners_with_synthetic_fields",
    "structural_cells_from_cleanup",
]
