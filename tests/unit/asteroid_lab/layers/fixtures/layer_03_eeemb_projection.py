"""Colinear E E E M B seed; M local (4,0); anchor (7,3)."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.seed_catalog import (
    MinerSeedEntry,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame


def eeemb_decoded_json() -> dict[str, object]:
    return {
        "BP": {
            "Entries": [
                {"T": "Layout_ShapeMinerExtension", "X": 1, "Y": 0, "R": 0},
                {"T": "Layout_ShapeMinerExtension", "X": 2, "Y": 0, "R": 0},
                {"T": "Layout_ShapeMinerExtension", "X": 3, "Y": 0, "R": 0},
                {"T": "Layout_ShapeMiner", "X": 4, "Y": 0, "R": 0},
                {"T": "SpaceBelt_Forward", "X": 5, "Y": 0, "R": 0},
                {"T": "SpaceBelt_Forward", "X": 6, "Y": 0, "R": 0},
            ],
        },
    }


def eeemb_seed_entry() -> MinerSeedEntry:
    return MinerSeedEntry(
        gene_key="test_eeemb",
        pattern_id="eeemb_test",
        intrinsic_priority_rank=1,
        throughput_factor=16,
        topology_signature="topo_eeemb",
        decoded_json=eeemb_decoded_json(),
    )


def eeemb_complete_map() -> ReconstructionCompleteMap:
    field = frozenset({(4, 3), (5, 3), (6, 3), (7, 3)})
    return ReconstructionCompleteMap(
        cells=(),
        field_cells=field,
        shape_field_cell_count=len(field),
        fluid_field_cell_count=0,
        external_void_cells=frozenset({(8, 3)}),
        coord_frame=CoordFrame.ISLAND_RAW,
    )


__all__ = ["eeemb_complete_map", "eeemb_seed_entry"]
