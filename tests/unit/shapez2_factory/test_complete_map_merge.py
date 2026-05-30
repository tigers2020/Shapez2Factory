"""PR-CLI-2c — pure parity for the display_map split (no Django).

Locks the synthetic-field transforms + cell-level merge extracted from the Django viewer /
replay row shaping into ``complete_map_merge`` so reconstruction-complete cells are identical.
"""

from __future__ import annotations

from shapez2_factory.domain.asteroid_lab.cleanup.result import CleanupResult
from shapez2_factory.domain.asteroid_lab.decoded_cell import DecodedCellDTO
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map_merge import (
    merge_reconstruction_display_cells,
    merged_display_cells_from_reconstruction,
    replace_extensions_with_synthetic_fields,
    replace_miners_with_synthetic_fields,
    structural_cells_from_cleanup,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.result import ReconstructionResult


def _cell(x: int, y: int, cell_kind: str, *, transport_kind: str = "none") -> DecodedCellDTO:
    return DecodedCellDTO(
        x=x,
        y=y,
        layer=None,
        rotation=0,
        tile_type="",
        cell_kind=cell_kind,
        transport_kind=transport_kind,
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={},
    )


def test_replace_miners_with_synthetic_fields_maps_kind_and_keeps_coord() -> None:
    out = replace_miners_with_synthetic_fields(
        (_cell(1, 1, "shape_miner"), _cell(2, 2, "fluid_miner"))
    )

    assert [(c.x, c.y, c.cell_kind) for c in out] == [
        (1, 1, "asteroid_shape_field"),
        (2, 2, "asteroid_fluid_field"),
    ]


def test_replace_extensions_with_synthetic_fields_maps_kind() -> None:
    out = replace_extensions_with_synthetic_fields(
        (_cell(1, 1, "shape_miner_extension"), _cell(2, 2, "fluid_miner_extension"))
    )

    assert [c.cell_kind for c in out] == ["asteroid_shape_field", "asteroid_fluid_field"]


def test_structural_cells_from_cleanup_drops_transport_and_synthesizes_fields() -> None:
    cleanup = CleanupResult(
        cleaned_cells=(),
        removed_building_cells=(),
        ignored_transport_cells=(),
        wall_coords=frozenset(),
        bbox_bounds=None,
        original_cells=(
            _cell(1, 1, "space_belt", transport_kind="belt"),
            _cell(2, 1, "shape_miner"),
            _cell(3, 1, "shape_miner_extension"),
            _cell(4, 1, "unknown"),
        ),
    )

    structural = structural_cells_from_cleanup(cleanup)

    kinds = {(c.x, c.y): c.cell_kind for c in structural}
    assert (1, 1) not in kinds  # transport dropped
    assert kinds[(2, 1)] == "asteroid_shape_field"
    assert kinds[(3, 1)] == "asteroid_shape_field"
    assert kinds[(4, 1)] == "unknown"


def test_merge_overlays_recon_on_structural_sorted() -> None:
    structural = (_cell(1, 1, "asteroid_shape_field"), _cell(2, 1, "unknown"))
    recon = (_cell(2, 1, "internal_void"),)

    merged = merge_reconstruction_display_cells(structural, recon)

    by_coord = {(c.x, c.y): c.cell_kind for c in merged}
    assert by_coord[(1, 1)] == "asteroid_shape_field"
    assert by_coord[(2, 1)] == "internal_void"  # recon overrides structural
    assert [(c.x, c.y) for c in merged] == sorted((c.x, c.y) for c in merged)


def test_merged_display_cells_from_reconstruction_end_to_end() -> None:
    cleanup = CleanupResult(
        cleaned_cells=(),
        removed_building_cells=(),
        ignored_transport_cells=(),
        wall_coords=frozenset(),
        bbox_bounds=None,
        original_cells=(
            _cell(1, 1, "shape_miner"),
            _cell(2, 1, "space_pipe", transport_kind="pipe"),
        ),
    )
    recon = ReconstructionResult(cells=(_cell(5, 5, "internal_void"),))

    merged = merged_display_cells_from_reconstruction(cleanup, recon)

    by_coord = {(c.x, c.y): c.cell_kind for c in merged}
    assert by_coord[(1, 1)] == "asteroid_shape_field"
    assert (2, 1) not in by_coord  # transport removed
    assert by_coord[(5, 5)] == "internal_void"  # recon overlay added
