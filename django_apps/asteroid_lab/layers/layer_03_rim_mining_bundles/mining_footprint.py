"""Mining-footprint prefilter before full seed projection (R2-lite)."""

from __future__ import annotations

from django_apps.asteroid_lab.genetic_sample.coord_transform import (
    rotate_offset,
    steps_from_canonical_e,
)
from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.project import _MINING_CELL_KINDS
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.seed_catalog import MinerSeedEntry
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.decoded_blueprint_snapshot import (
    build_decoded_blueprint_snapshot,
)
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

_MinerExtractorLocal = Coord


def projected_mining_cells_at_anchor(
    *,
    seed: MinerSeedEntry,
    anchor_coord: Coord,
    output_dir: Direction,
    complete_map: ReconstructionCompleteMap,
) -> frozenset[Coord] | None:
    """Return mining cell coords if computable; None if seed has no extractor."""
    del complete_map
    snap = build_decoded_blueprint_snapshot(seed.decoded_json)
    extractor_local: _MinerExtractorLocal | None = None
    for cell in snap.cells:
        if cell.cell_kind in ("shape_miner", "fluid_miner"):
            extractor_local = (cell.x, cell.y)
            break
    if extractor_local is None:
        return None

    steps = steps_from_canonical_e(output_dir)
    mining_cells: set[Coord] = set()
    for cell in snap.cells:
        if cell.cell_kind not in _MINING_CELL_KINDS:
            continue
        offset = (cell.x - extractor_local[0], cell.y - extractor_local[1])
        map_coord = (
            anchor_coord[0] + rotate_offset(offset, steps)[0],
            anchor_coord[1] + rotate_offset(offset, steps)[1],
        )
        mining_cells.add(map_coord)
    return frozenset(mining_cells)


def mining_footprint_off_field(
    *,
    seed: MinerSeedEntry,
    anchor_coord: Coord,
    output_dir: Direction,
    complete_map: ReconstructionCompleteMap,
) -> bool:
    cells = projected_mining_cells_at_anchor(
        seed=seed,
        anchor_coord=anchor_coord,
        output_dir=output_dir,
        complete_map=complete_map,
    )
    if cells is None:
        return False
    return bool(cells - complete_map.field_cells)


__all__ = ["mining_footprint_off_field", "projected_mining_cells_at_anchor"]
