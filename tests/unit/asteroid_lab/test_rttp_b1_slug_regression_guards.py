"""P1-ELCP-RF-B1 Phase C — Gate A primary slug selection regression guards."""

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
from django_apps.asteroid_lab.optimization.selection.primary_genome import select_primary_genome
from django_apps.asteroid_lab.reconstruction.complete_map import build_reconstruction_complete_map
from django_apps.asteroid_lab.reconstruction.field_cells import (
    asteroid_field_cell_count_for_placement,
)
from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
    run_reconstruction_for_map_input,
)
from django_apps.asteroid_lab.services.reconstruction_capacity_summary import (
    build_reconstruction_capacity_envelope,
)
from django_apps.asteroid_lab.services.throughput_target import (
    compute_target_throughput_per_min,
    parse_throughput_target_percent,
    primary_reconstruction_max_per_min,
)
from django_apps.web.services.asteroid_game_data_snapshot import (
    build_asteroid_game_data_snapshot_with_provenance,
)
from tests.support.rttp_b1_cert_slug_import import CERT_SLUG, import_cert_candidate_recon_l0
from tests.support.rttp_b1_gate_a_frozen_bounds import (
    CERT_SLUG_GREEDY_REGRET_BASELINE,
    GATE_A_PHASE0_VERDICT,
)


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


def _cert_slug_commit_order_len(
    *,
    selection_mode: SelectionMode,
    boundary_run_id: str,
) -> int:
    from django_apps.asteroid_lab import models as m

    project_id = import_cert_candidate_recon_l0(replace=True)
    build = build_asteroid_game_data_snapshot_with_provenance()
    inp_row = m.AsteroidMapInput.objects.filter(project_id=project_id).first()
    assert inp_row is not None
    cleanup, recon = run_reconstruction_for_map_input(
        int(inp_row.pk),
        boundary_run_id=boundary_run_id,
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
        selection_mode=selection_mode,
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
    return len(genome.commit_order)


@pytest.mark.skipif(
    GATE_A_PHASE0_VERDICT != "GO",
    reason="B1 Phase 0 NO-GO — cert slug guards gated off",
)
@pytest.mark.django_db
@pytest.mark.slow
def test_cert_slug_greedy_regret_baseline_unchanged(
    imported_game_data_batch_module: object,
) -> None:
    _ = imported_game_data_batch_module
    length = _cert_slug_commit_order_len(
        selection_mode=SelectionMode.GREEDY_REGRET,
        boundary_run_id="elcp-rf-b1-cert-greedy-regret",
    )
    assert length == CERT_SLUG_GREEDY_REGRET_BASELINE, (
        f"{CERT_SLUG} GREEDY_REGRET commit_order_len drift: got {length}, "
        f"frozen {CERT_SLUG_GREEDY_REGRET_BASELINE}"
    )


@pytest.mark.skipif(
    GATE_A_PHASE0_VERDICT != "GO",
    reason="B1 Phase 0 NO-GO — cert slug guards gated off",
)
@pytest.mark.django_db
@pytest.mark.slow
def test_cert_slug_overlap_pack_at_least_greedy_baseline(
    imported_game_data_batch_module: object,
) -> None:
    _ = imported_game_data_batch_module
    greedy_len = _cert_slug_commit_order_len(
        selection_mode=SelectionMode.GREEDY_REGRET,
        boundary_run_id="elcp-rf-b1-cert-greedy-regret-for-compare",
    )
    overlap_len = _cert_slug_commit_order_len(
        selection_mode=SelectionMode.GREEDY_REGRET_OVERLAP_PACK,
        boundary_run_id="elcp-rf-b1-cert-overlap-pack",
    )
    assert overlap_len >= greedy_len
    assert overlap_len >= CERT_SLUG_GREEDY_REGRET_BASELINE
    print(f"B1_CERT_SLUG_GREEDY_LEN={greedy_len} " f"B1_CERT_SLUG_OVERLAP_LEN={overlap_len}")
