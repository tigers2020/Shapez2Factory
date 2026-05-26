"""RTTP E2E: official reconstruction copy-code fixtures → adapter → pipeline."""

from __future__ import annotations

from dataclasses import replace

import pytest

from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_reconstruction,
)
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.reconstruction.topology_contract import (
    decode_shapez_copy_string,
    load_reconstruction_fixture_line_pairs,
)
from tests.support.catalog_test_fixtures import build_minimal_test_catalog_slice

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


def _optimization_input_from_fixture_line(line_index: int) -> OptimizationInput:
    required_copy, _solved_copy = load_reconstruction_fixture_line_pairs()[line_index]
    snap = decode_shapez_copy_string(required_copy)
    cleanup = deconstruct_snapshot(snap)
    recon = run_topology_reconstruction(cleanup)
    inp = optimization_input_from_reconstruction(recon, cleanup=cleanup)
    if inp.catalog_slice is None:
        inp = replace(inp, catalog_slice=build_minimal_test_catalog_slice())
    return inp


@pytest.fixture(params=range(len(load_reconstruction_fixture_line_pairs())))
def reconstruction_fixture_line_index(request: pytest.FixtureRequest) -> int:
    return int(request.param)


def test_rttp_pipeline_deterministic_on_reconstruction_fixture_line(
    reconstruction_fixture_line_index: int,
) -> None:
    """Each ``reconstruction_required_.txt`` line: copy → recon → RTTP commit (G8 on real maps)."""

    inp = _optimization_input_from_fixture_line(reconstruction_fixture_line_index)
    first = run_rttp_pipeline(inp, policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM)
    second = run_rttp_pipeline(inp, policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM)

    assert first == second
    assert first.normal_count >= 1
    assert len(first.commit_result.committed_ids) >= 1
    assert first.validation_passed
    assert first.commit_result.committed_ids == second.commit_result.committed_ids
    assert first.genome.commit_order == second.genome.commit_order


def test_rttp_canon_fixture_line_one_hole_map_has_mineable_and_commits() -> None:
    """Line 1 (canon / hole-asteroid regression): confident recon topology → RTTP."""

    inp = _optimization_input_from_fixture_line(1)
    assert len(inp.mineable_cells) >= 1

    result = run_rttp_pipeline(inp, policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM)
    assert result.normal_count >= 1
    assert len(result.commit_result.committed_ids) >= 1
    assert result.validation_passed
