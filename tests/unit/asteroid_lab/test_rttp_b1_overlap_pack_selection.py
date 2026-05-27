"""P1-ELCP-RF-B1 overlap-pack selection (Gate A + frozen Phase 0 constants)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from django_apps.asteroid_lab.contracts.selection_mode import SelectionMode
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
    FixedOutputTransportPolicy,
    RouteProbeStartPolicy,
)
from django_apps.asteroid_lab.optimization.input_contracts import RttpPipelineConfig
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_reconstruction,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.selection.overlap_pack import select_genome_overlap_pack
from django_apps.asteroid_lab.optimization.selection.primary_genome import select_primary_genome
from django_apps.asteroid_lab.reconstruction.complete_map import build_reconstruction_complete_map
from django_apps.asteroid_lab.reconstruction.field_cells import (
    asteroid_field_cell_count_for_placement,
)
from django_apps.asteroid_lab.services.reconstruction_capacity_summary import (
    build_reconstruction_capacity_envelope,
)
from django_apps.asteroid_lab.services.throughput_target import (
    compute_target_throughput_per_min,
    parse_throughput_target_percent,
    primary_reconstruction_max_per_min,
)
from tests.support.rttp_b1_gate_a_frozen_bounds import (
    GATE_A_GREEDY_REGRET_BASELINE,
    GATE_A_PHASE0_VERDICT,
    GATE_A_PLACEMENT_GOAL,
    GATE_A_TARGET_FLOOR,
)


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


@pytest.mark.skipif(
    GATE_A_PHASE0_VERDICT != "GO",
    reason="B1 Phase 0 NO-GO — overlap pack implementation gated off",
)
@pytest.mark.django_db
@pytest.mark.slow
def test_gate_a_overlap_pack_meets_frozen_target_floor(
    imported_game_data_batch_module: object,
) -> None:
    from django_apps.asteroid_lab import models as m
    from django_apps.asteroid_lab.management.commands.import_rttp_core_recovery_test_map import (
        import_core_recovery_test_map,
    )
    from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
        run_reconstruction_for_map_input,
    )
    from django_apps.web.services.asteroid_game_data_snapshot import (
        build_asteroid_game_data_snapshot_with_provenance,
    )

    _ = imported_game_data_batch_module
    project_id = import_core_recovery_test_map(replace=True)
    build = build_asteroid_game_data_snapshot_with_provenance()
    inp_row = m.AsteroidMapInput.objects.filter(project_id=project_id).first()
    assert inp_row is not None
    cleanup, recon = run_reconstruction_for_map_input(
        int(inp_row.pk),
        boundary_run_id="elcp-rf-b1-overlap-pack-gate-a",
    )
    complete_map = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
    inp = optimization_input_from_reconstruction(
        recon,
        cleanup=cleanup,
        catalog_slice=build.catalog_slice,
        complete_map=complete_map,
    )
    cap = build_reconstruction_capacity_envelope(complete_map=complete_map)
    percent = parse_throughput_target_percent({})
    target = compute_target_throughput_per_min(
        reconstruction_max=primary_reconstruction_max_per_min(cap),
        percent=percent,
    )
    platform = asteroid_field_cell_count_for_placement(complete_map, inp.transport_kind)
    pipeline_config = RttpPipelineConfig(
        target_throughput_per_min=target,
        placement_target_percent=percent,
        placement_platform_cell_count=platform,
        reconstruction_max_throughput_per_min=primary_reconstruction_max_per_min(cap),
        selection_mode=SelectionMode.GREEDY_REGRET_OVERLAP_PACK,
    )

    captured: dict[str, object] = {}

    def _capture_select(*args: object, **kwargs: object) -> PlacementGenome:
        captured["mode"] = kwargs["mode"]
        genome = select_primary_genome(*args, **kwargs)
        captured["genome"] = genome
        return genome

    with patch(
        "django_apps.asteroid_lab.optimization.pipeline.select_primary_genome",
        side_effect=_capture_select,
    ):
        run_rttp_pipeline(
            inp,
            policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
            fixed_output_transport_policy=FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
            route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
            pipeline_config=pipeline_config,
        )

    assert captured["mode"] is SelectionMode.GREEDY_REGRET_OVERLAP_PACK
    genome = captured["genome"]
    assert isinstance(genome, PlacementGenome)
    assert len(genome.commit_order) >= GATE_A_TARGET_FLOOR
    assert len(genome.commit_order) <= GATE_A_PLACEMENT_GOAL
    print(f"B1_OVERLAP_PACK_LEN={len(genome.commit_order)}")


@pytest.mark.django_db
@pytest.mark.slow
def test_gate_a_greedy_regret_baseline_unchanged_at_59(
    imported_game_data_batch_module: object,
) -> None:
    from django_apps.asteroid_lab import models as m
    from django_apps.asteroid_lab.management.commands.import_rttp_core_recovery_test_map import (
        import_core_recovery_test_map,
    )
    from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
        run_reconstruction_for_map_input,
    )
    from django_apps.web.services.asteroid_game_data_snapshot import (
        build_asteroid_game_data_snapshot_with_provenance,
    )

    _ = imported_game_data_batch_module
    project_id = import_core_recovery_test_map(replace=True)
    build = build_asteroid_game_data_snapshot_with_provenance()
    inp_row = m.AsteroidMapInput.objects.filter(project_id=project_id).first()
    assert inp_row is not None
    cleanup, recon = run_reconstruction_for_map_input(
        int(inp_row.pk),
        boundary_run_id="elcp-rf-b1-greedy-regret-baseline",
    )
    complete_map = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
    inp = optimization_input_from_reconstruction(
        recon,
        cleanup=cleanup,
        catalog_slice=build.catalog_slice,
        complete_map=complete_map,
    )
    cap = build_reconstruction_capacity_envelope(complete_map=complete_map)
    percent = parse_throughput_target_percent({})
    target = compute_target_throughput_per_min(
        reconstruction_max=primary_reconstruction_max_per_min(cap),
        percent=percent,
    )
    platform = asteroid_field_cell_count_for_placement(complete_map, inp.transport_kind)
    pipeline_config = RttpPipelineConfig(
        target_throughput_per_min=target,
        placement_target_percent=percent,
        placement_platform_cell_count=platform,
        reconstruction_max_throughput_per_min=primary_reconstruction_max_per_min(cap),
        selection_mode=SelectionMode.GREEDY_REGRET,
    )

    captured: dict[str, object] = {}

    def _capture_select(*args: object, **kwargs: object) -> PlacementGenome:
        genome = select_primary_genome(*args, **kwargs)
        captured["genome"] = genome
        return genome

    with patch(
        "django_apps.asteroid_lab.optimization.pipeline.select_primary_genome",
        side_effect=_capture_select,
    ):
        run_rttp_pipeline(
            inp,
            policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
            fixed_output_transport_policy=FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
            route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
            pipeline_config=pipeline_config,
        )

    genome = captured["genome"]
    assert isinstance(genome, PlacementGenome)
    assert len(genome.commit_order) == GATE_A_GREEDY_REGRET_BASELINE


def test_select_genome_overlap_pack_disjoint_pool_returns_all(
    greenfield_optimization_input,
) -> None:
    from tests.unit.asteroid_lab.test_ga_evolution_shadow import (
        _bundle_candidate,
        _skeleton_with_goals,
    )

    inp = greenfield_optimization_input
    skeleton = _skeleton_with_goals(inp, capacity_goals=10)
    pool = tuple(_bundle_candidate((i * 4, 0)) for i in range(5))
    genome = select_genome_overlap_pack(pool, skeleton, inp, goal_count=10)
    assert len(genome.commit_order) == 5
