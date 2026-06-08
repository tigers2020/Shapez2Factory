"""Programmatic narrow-corridor fixtures for Sequence 10A regression (S1, S3, S4)."""

from __future__ import annotations

from decimal import Decimal

from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from shapez2_factory.adapters.asteroid_lab.genetic_sample_seed_snapshot import (
    GeneticSampleSeedEntry,
    GeneticSampleSeedSnapshot,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
    ExteriorConnector,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from shapez2_factory.domain.asteroid_lab.decoded_cell import DecodedCellDTO
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord

# --- S1: stale probe after prior commit (reservation sequence) ---

S1_ANCHOR_A: Coord = (1, 2)
S1_ANCHOR_B: Coord = (1, 3)
S1_GOAL: Coord = (6, 2)


def s1_narrow_column_field_cells() -> frozenset[Coord]:
    return frozenset({(1, 1), (1, 2), (1, 3)})


def s1_narrow_column_void_cells() -> frozenset[Coord]:
    return frozenset(
        {
            (2, 1),
            (3, 1),
            (4, 1),
            (5, 1),
            (2, 2),
            (3, 2),
            (4, 2),
            (5, 2),
            (2, 3),
            (3, 3),
            (4, 3),
            (5, 3),
            S1_GOAL,
        }
    )


def s1_probe_vs_commit_complete_map() -> ReconstructionCompleteMap:
    field = s1_narrow_column_field_cells()
    return ReconstructionCompleteMap(
        cells=(),
        field_cells=field,
        shape_field_cell_count=len(field),
        fluid_field_cell_count=0,
        external_void_cells=s1_narrow_column_void_cells(),
        coord_frame=CoordFrame.ISLAND_RAW,
    )


def s1_probe_vs_commit_exterior_plan() -> ExteriorConnectionPlan:
    return ExteriorConnectionPlan(
        transport_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        planning_target_per_min=Decimal("5000"),
        per_connector_capacity_per_min=Decimal("1000"),
        required_connector_count=1,
        reference_connector_count=1,
        spare_connector_count=0,
        planned_connectors=(
            ExteriorConnector(
                connector_id="s1_shape_goal",
                void_coord=S1_GOAL,
                edge=CardinalEdge.EAST,
                layout_t="SpaceBelt_Forward",
                rotation=0,
                capacity_per_min=Decimal("1000"),
                coords=(S1_GOAL,),
                role=ExteriorConnectorRole.REQUIRED,
            ),
        ),
        unmet_reason=None,
    )


def s1_probe_vs_commit_catalog() -> GeneticSampleSeedSnapshot:
    """``blk`` south extension from interior anchor reserves B's platform after A commits."""

    blocker = GeneticSampleSeedEntry(
        gene_id="blk",
        resource_kind="shape",
        canonical_output_dir="E",
        occupied_offsets=((0, 0), (0, 1)),
        extractor_offset=(0, 0),
        extension_offsets=((0, 1),),
        output_stub_offset=(1, 0),
        route_probe_start_offset=(2, 0),
        throughput_factor=8,
        topology_signature_base="blk",
    )
    m0e = GeneticSampleSeedEntry(
        gene_id="m0e",
        resource_kind="both",
        canonical_output_dir="E",
        occupied_offsets=((0, 0),),
        extractor_offset=(0, 0),
        extension_offsets=(),
        output_stub_offset=(1, 0),
        route_probe_start_offset=(2, 0),
        throughput_factor=4,
        topology_signature_base="m0e",
    )
    return GeneticSampleSeedSnapshot(
        schema_version="genetic_sample_seed_v1",
        generated_at="",
        provenance_hash="",
        source_batch_id="narrow_corridor_s1",
        deterministic_sort_key="by_gene_id_then_throughput_desc",
        entries=(blocker, m0e),
    )


# --- S3: shared corridor / trunk sharing (two east rim miners, merge trunk) ---

S3_GOAL: Coord = (5, 2)


def s3_corridor_sharing_complete_map() -> ReconstructionCompleteMap:
    field = frozenset({(1, 1), (1, 3)})
    void = frozenset(
        {
            (2, 1),
            (3, 1),
            (4, 1),
            (5, 1),
            (2, 3),
            (3, 3),
            (4, 3),
            (5, 3),
            S3_GOAL,
        }
    )
    return ReconstructionCompleteMap(
        cells=(),
        field_cells=field,
        shape_field_cell_count=len(field),
        fluid_field_cell_count=0,
        external_void_cells=void,
        coord_frame=CoordFrame.ISLAND_RAW,
    )


def s3_corridor_sharing_exterior_plan() -> ExteriorConnectionPlan:
    return ExteriorConnectionPlan(
        transport_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        planning_target_per_min=Decimal("5000"),
        per_connector_capacity_per_min=Decimal("1000"),
        required_connector_count=1,
        reference_connector_count=1,
        spare_connector_count=0,
        planned_connectors=(
            ExteriorConnector(
                connector_id="s3_merge_goal",
                void_coord=S3_GOAL,
                edge=CardinalEdge.EAST,
                layout_t="SpaceBelt_Forward",
                rotation=0,
                capacity_per_min=Decimal("1000"),
                coords=(S3_GOAL,),
                role=ExteriorConnectorRole.REQUIRED,
            ),
        ),
        unmet_reason=None,
    )


def s3_corridor_sharing_catalog() -> GeneticSampleSeedSnapshot:
    m0e = GeneticSampleSeedEntry(
        gene_id="m0e",
        resource_kind="both",
        canonical_output_dir="E",
        occupied_offsets=((0, 0),),
        extractor_offset=(0, 0),
        extension_offsets=(),
        output_stub_offset=(1, 0),
        route_probe_start_offset=(2, 0),
        throughput_factor=4,
        topology_signature_base="m0e",
    )
    return GeneticSampleSeedSnapshot(
        schema_version="genetic_sample_seed_v1",
        generated_at="",
        provenance_hash="",
        source_batch_id="narrow_corridor_s3",
        deterministic_sort_key="by_gene_id_then_throughput_desc",
        entries=(m0e,),
    )


# --- S4: shape belt vs fluid pipe separate route domains ---

S4_SHAPE_GOAL: Coord = (7, 1)
S4_FLUID_GOAL: Coord = (7, 3)


def _s4_field_cell(x: int, y: int, *, kind: str) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=x,
        y=y,
        layer=None,
        rotation=0,
        tile_type="",
        cell_kind=kind,
        transport_kind="",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={},
    )


def s4_dual_transport_complete_map() -> ReconstructionCompleteMap:
    shape_coords = frozenset({(1, 1), (2, 1), (3, 1)})
    fluid_coords = frozenset({(1, 3), (2, 3), (3, 3)})
    field = shape_coords | fluid_coords
    void = frozenset(
        {
            (4, 1),
            (5, 1),
            (6, 1),
            S4_SHAPE_GOAL,
            (4, 3),
            (5, 3),
            (6, 3),
            S4_FLUID_GOAL,
        }
    )
    cells = tuple(
        [_s4_field_cell(x, y, kind="asteroid_shape_field") for x, y in shape_coords]
        + [_s4_field_cell(x, y, kind="asteroid_fluid_field") for x, y in fluid_coords]
    )
    return ReconstructionCompleteMap(
        cells=cells,
        field_cells=field,
        shape_field_cell_count=len(shape_coords),
        fluid_field_cell_count=len(fluid_coords),
        external_void_cells=void,
        coord_frame=CoordFrame.ISLAND_RAW,
    )


def s4_dual_transport_exterior_plan() -> ExteriorConnectionPlan:
    return ExteriorConnectionPlan(
        transport_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        planning_target_per_min=Decimal("5000"),
        per_connector_capacity_per_min=Decimal("1000"),
        required_connector_count=2,
        reference_connector_count=2,
        spare_connector_count=0,
        planned_connectors=(
            ExteriorConnector(
                connector_id="s4_shape_goal",
                void_coord=S4_SHAPE_GOAL,
                edge=CardinalEdge.EAST,
                layout_t="SpaceBelt_Forward",
                rotation=0,
                capacity_per_min=Decimal("1000"),
                coords=(S4_SHAPE_GOAL,),
                role=ExteriorConnectorRole.REQUIRED,
            ),
            ExteriorConnector(
                connector_id="s4_fluid_goal",
                void_coord=S4_FLUID_GOAL,
                edge=CardinalEdge.EAST,
                layout_t="SpacePipe_Forward",
                rotation=0,
                capacity_per_min=Decimal("345600"),
                coords=(S4_FLUID_GOAL,),
                role=ExteriorConnectorRole.REQUIRED,
            ),
        ),
        unmet_reason=None,
    )


def s4_dual_transport_catalog() -> GeneticSampleSeedSnapshot:
    shape_miner = GeneticSampleSeedEntry(
        gene_id="shape_m0e",
        resource_kind="shape",
        canonical_output_dir="E",
        occupied_offsets=((0, 0),),
        extractor_offset=(0, 0),
        extension_offsets=(),
        output_stub_offset=(1, 0),
        route_probe_start_offset=(2, 0),
        throughput_factor=4,
        topology_signature_base="shape_m0e",
    )
    fluid_miner = GeneticSampleSeedEntry(
        gene_id="fluid_m0e",
        resource_kind="fluid",
        canonical_output_dir="E",
        occupied_offsets=((0, 0),),
        extractor_offset=(0, 0),
        extension_offsets=(),
        output_stub_offset=(1, 0),
        route_probe_start_offset=(2, 0),
        throughput_factor=4,
        topology_signature_base="fluid_m0e",
    )
    return GeneticSampleSeedSnapshot(
        schema_version="genetic_sample_seed_v1",
        generated_at="",
        provenance_hash="",
        source_batch_id="narrow_corridor_s4",
        deterministic_sort_key="by_gene_id_then_throughput_desc",
        entries=(shape_miner, fluid_miner),
    )


# --- S2 / 10B: high-TF vs corridor-pressure tradeoff (extended west field for m3e) ---


def s2_future_expansion_complete_map() -> ReconstructionCompleteMap:
    field = frozenset({(1, 1), (1, 3), (0, 1), (-1, 1), (-2, 1), (-3, 1)})
    void = frozenset(
        {
            (2, 1),
            (3, 1),
            (4, 1),
            (5, 1),
            (2, 3),
            (3, 3),
            (4, 3),
            (5, 3),
            S3_GOAL,
        }
    )
    return ReconstructionCompleteMap(
        cells=(),
        field_cells=field,
        shape_field_cell_count=len(field),
        fluid_field_cell_count=0,
        external_void_cells=void,
        coord_frame=CoordFrame.ISLAND_RAW,
    )


def s2_future_expansion_exterior_plan() -> ExteriorConnectionPlan:
    return s3_corridor_sharing_exterior_plan()


def s2_future_expansion_catalog() -> GeneticSampleSeedSnapshot:
    m3e = GeneticSampleSeedEntry(
        gene_id="m3e",
        resource_kind="shape",
        canonical_output_dir="E",
        occupied_offsets=((0, 0), (-1, 0), (-2, 0), (-3, 0)),
        extractor_offset=(0, 0),
        extension_offsets=((-1, 0), (-2, 0), (-3, 0)),
        output_stub_offset=(1, 0),
        route_probe_start_offset=(2, 0),
        throughput_factor=16,
        topology_signature_base="m3e",
    )
    m0e = GeneticSampleSeedEntry(
        gene_id="m0e",
        resource_kind="both",
        canonical_output_dir="E",
        occupied_offsets=((0, 0),),
        extractor_offset=(0, 0),
        extension_offsets=(),
        output_stub_offset=(1, 0),
        route_probe_start_offset=(2, 0),
        throughput_factor=4,
        topology_signature_base="m0e",
    )
    return GeneticSampleSeedSnapshot(
        schema_version="genetic_sample_seed_v1",
        generated_at="",
        provenance_hash="",
        source_batch_id="narrow_corridor_s2",
        deterministic_sort_key="by_gene_id_then_throughput_desc",
        entries=(m3e, m0e),
    )


__all__ = [
    "S1_ANCHOR_A",
    "S1_ANCHOR_B",
    "S1_GOAL",
    "S3_GOAL",
    "S4_FLUID_GOAL",
    "S4_SHAPE_GOAL",
    "s1_probe_vs_commit_catalog",
    "s1_probe_vs_commit_complete_map",
    "s1_probe_vs_commit_exterior_plan",
    "s3_corridor_sharing_catalog",
    "s3_corridor_sharing_complete_map",
    "s3_corridor_sharing_exterior_plan",
    "s2_future_expansion_catalog",
    "s2_future_expansion_complete_map",
    "s2_future_expansion_exterior_plan",
    "s4_dual_transport_catalog",
    "s4_dual_transport_complete_map",
    "s4_dual_transport_exterior_plan",
]
