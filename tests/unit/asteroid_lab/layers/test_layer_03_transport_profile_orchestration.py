"""L3 transport profile orchestration — shape_belt / fluid_pipe within one layer run."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.layers.layer_01_reconstruction.run import run_layer_01
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from shapez2_factory.adapters.asteroid_lab.genetic_sample_seed_snapshot import (
    GeneticSampleSeedEntry,
    GeneticSampleSeedSnapshot,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import (
    CandidateRejectReason,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import (
    TransportKind,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.run import (
    execute_layer_02_exterior_transport_plan,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.candidate_gen import (  # noqa: E501
    generate_candidates,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.transport_profile import (  # noqa: E501
    build_layer03_transport_profiles,
)
from tests.support.reconstruction_complete_map_fixtures import (
    minimal_cleanup_and_recon_from_cells,
)
from tests.unit.asteroid_lab.layers.helpers.l02_complete_map_fixtures import (
    build_rect_field_with_void_shell,
)
from tests.unit.asteroid_lab.layers.helpers.l02_rules import snapshot_rules_for_test


def _field_cell(x: int, y: int, *, cell_kind: str) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=x,
        y=y,
        layer=None,
        rotation=0,
        tile_type="",
        cell_kind=cell_kind,
        transport_kind="none",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={},
    )


def _both_gene_catalog() -> GeneticSampleSeedSnapshot:
    entry = GeneticSampleSeedEntry(
        gene_id="m0e",
        resource_kind="both",
        canonical_output_dir="E",
        occupied_offsets=((0, 0),),
        extractor_offset=(0, 0),
        extension_offsets=(),
        output_stub_offset=(1, 0),
        route_probe_start_offset=(2, 0),
        throughput_factor=4,
        topology_signature_base="m0e_base",
    )
    return GeneticSampleSeedSnapshot(
        schema_version="genetic_sample_seed_v1",
        generated_at="",
        provenance_hash="",
        source_batch_id="",
        deterministic_sort_key="by_gene_id_then_throughput_desc",
        entries=(entry,),
    )


def _mixed_layer01_and_l2_plan():
    shell = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    fluid_coords = {(0, 0), (1, 0), (2, 0), (3, 0)}
    cells = [
        _field_cell(
            x,
            y,
            cell_kind=(
                "asteroid_fluid_field" if (x, y) in fluid_coords else "asteroid_shape_field"
            ),
        )
        for x, y in shell.field_cells
    ]
    cleanup, recon = minimal_cleanup_and_recon_from_cells(*cells)
    layer01 = run_layer_01(cleanup=cleanup, recon=recon)
    plan = execute_layer_02_exterior_transport_plan(
        complete_map=layer01.complete_map,
        capacity_envelope=layer01.capacity_envelope,
        throughput_target_percent=80,
        speed_tier=1,
        rules=snapshot_rules_for_test(),
    )
    return layer01.complete_map, plan


@pytest.mark.django_db
def test_mixed_map_builds_shape_and_fluid_profiles() -> None:
    complete_map, plan = _mixed_layer01_and_l2_plan()
    profiles = build_layer03_transport_profiles(
        complete_map=complete_map,
        exterior_plan=plan,
    )
    assert len(profiles) == 2
    assert profiles[0].transport_kind is TransportKind.SPACE_BELT
    assert profiles[1].transport_kind is TransportKind.SPACE_PIPE
    assert profiles[0].route_goals
    assert profiles[1].route_goals


@pytest.mark.django_db
def test_mixed_map_fluid_pipe_diagnostics_exclude_no_goals() -> None:
    complete_map, plan = _mixed_layer01_and_l2_plan()
    result = generate_candidates(
        complete_map=complete_map,
        exterior_plan=plan,
        genetic_sample_seeds=_both_gene_catalog(),
    )
    fluid_rejects = [
        r
        for r in result.diagnostic_rejected_candidates
        if r.candidate.transport_kind is TransportKind.SPACE_PIPE
    ]
    no_goals = [
        r
        for r in fluid_rejects
        if r.reject_reason is CandidateRejectReason.EXTERIOR_GOAL_UNREACHABLE_NO_GOALS
    ]
    assert not no_goals
