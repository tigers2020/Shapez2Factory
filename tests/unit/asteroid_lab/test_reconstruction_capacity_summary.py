"""PR-2a — reconstruction capacity from complete map + MiningExtractionRule only."""

from __future__ import annotations

from decimal import Decimal

import pytest

from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.reconstruction.complete_map import (
    build_reconstruction_complete_map,
    overlay_field_cell_count,
)
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.reconstruction.topology_contract import (
    decode_shapez_copy_string,
    load_reconstruction_fixture_line_pairs,
)
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.services.reconstruction_capacity_summary import (
    build_reconstruction_capacity_envelope,
    build_reconstruction_capacity_summary,
    build_reconstruction_observability,
    decimal_str,
    detect_primary_resource_kind,
)
from django_apps.game_data.services.mining_extraction_rules import (
    get_active_rule,
    max_output_per_miner,
    output_per_min,
)
from tests.support.reconstruction_complete_map_fixtures import (
    minimal_complete_map_from_cells,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


def _cell(x: int, y: int, *, cell_kind: str = "asteroid_shape_field") -> DecodedCellDTO:
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


def _recon_with_overlay_cells(
    n: int, *, cell_kind: str = "asteroid_shape_field"
) -> ReconstructionResult:
    cells = tuple(_cell(i, 0, cell_kind=cell_kind) for i in range(n))
    return ReconstructionResult(
        cells=cells,
        confirmed_cells=frozenset({(0, 0)}),
        ambiguous_cells=frozenset(),
        external_void_cells=frozenset(),
        confidence_score=0.94,
        quality_tier="CONFIDENT_RECONSTRUCTION",
    )


def test_decimal_str_four_places() -> None:
    assert decimal_str(Decimal("480")) == "480.0000"


def test_shape_capacity_uses_complete_map_field_cells_not_mask() -> None:
    cells = tuple(_cell(i, 0) for i in range(3))
    complete = minimal_complete_map_from_cells(*cells)
    rule = get_active_rule("shape")
    per_cell = output_per_min(rule, 4)
    row = build_reconstruction_capacity_summary(
        complete_map=complete,
        resource_kind="shape",
    )
    assert row["capacity_upper_bound_platform_count"] == 3
    assert row["max_throughput_per_min"] == decimal_str(per_cell * Decimal(3))


def test_shape_capacity_uses_db_base_mine_rate_times_four_per_field_cell() -> None:
    complete = minimal_complete_map_from_cells(_cell(0, 0), _cell(1, 0))
    row = build_reconstruction_capacity_summary(complete_map=complete, resource_kind="shape")
    rule = get_active_rule("shape")
    per_cell = output_per_min(rule, 4)
    assert row["mini_units_per_confirmed_cell"] == 4
    assert row["capacity_upper_bound_mini_units"] == 8
    assert row["mini_unit_output_per_min"] == decimal_str(rule.mini_unit_output_per_min)
    assert row["output_per_confirmed_cell"] == decimal_str(per_cell)
    assert row["max_output_per_miner"] == decimal_str(max_output_per_miner(rule))
    assert row["max_output_per_miner"] == "480.0000"
    assert row["capacity_upper_bound_platform_count"] == 2
    assert row["max_throughput_per_min"] == decimal_str(per_cell * Decimal(2))
    assert row["source_kind"] == "CANON_MANUAL"


def test_fluid_capacity_uses_db_base_mine_rate_times_four_per_field_cell() -> None:
    complete = minimal_complete_map_from_cells(_cell(0, 0, cell_kind="asteroid_fluid_field"))
    row = build_reconstruction_capacity_summary(complete_map=complete, resource_kind="fluid")
    rule = get_active_rule("fluid")
    per_cell = output_per_min(rule, 4)
    assert row["mini_unit_output_per_min"] == decimal_str(rule.mini_unit_output_per_min)
    assert row["output_per_confirmed_cell"] == decimal_str(per_cell)
    assert row["max_output_per_miner"] == "4800.0000"
    assert row["max_throughput_per_min"] == decimal_str(per_cell)


def test_envelope_shape_only_fluid_platform_count_zero() -> None:
    complete = minimal_complete_map_from_cells(
        _cell(0, 0),
        _cell(1, 0),
        _cell(2, 0),
    )
    env = build_reconstruction_capacity_envelope(complete_map=complete)
    assert env["capacity_basis"] == "terrain_upper_bound"
    assert env["primary_resource_kind"] == "shape"
    assert env["by_resource"]["shape"]["max_throughput_per_min"] == "360.0000"
    assert env["by_resource"]["fluid"]["max_throughput_per_min"] == "0.0000"
    assert env["by_resource"]["fluid"]["capacity_upper_bound_platform_count"] == 0


def test_fluid_dominant_asteroid_uses_fluid_platform_count() -> None:
    complete = minimal_complete_map_from_cells(
        _cell(0, 0, cell_kind="asteroid_fluid_field"),
        _cell(1, 0, cell_kind="asteroid_fluid_field"),
    )
    row = build_reconstruction_capacity_summary(complete_map=complete, resource_kind="fluid")
    assert row["capacity_upper_bound_platform_count"] == 2
    assert row["max_throughput_per_min"] == "2400.0000"
    assert detect_primary_resource_kind(complete) == "fluid"


def test_observability_snapshot_fields() -> None:
    complete = minimal_complete_map_from_cells(*(_cell(i, 0) for i in range(5)))
    recon = _recon_with_overlay_cells(5)
    obs = build_reconstruction_observability(recon=recon, complete_map=complete)
    assert obs["cell_count"] == 5
    assert obs["asteroid_field_cell_count"] == 5
    assert obs["rim_cell_count"] == 5
    assert obs["shape_field_cell_count"] == 5
    assert "mineable_cell_count" not in obs
    assert "confirmed_cell_count" not in obs
    assert obs["quality_tier"] == "CONFIDENT_RECONSTRUCTION"
    assert obs["confidence_score"] == "0.9400"


def test_builders_do_not_accept_solver_summary() -> None:
    import inspect

    for fn in (
        build_reconstruction_capacity_summary,
        build_reconstruction_capacity_envelope,
        build_reconstruction_observability,
    ):
        assert "solver_summary" not in inspect.signature(fn).parameters


def _canon_cleanup_recon_complete():
    required_copy, _solved = load_reconstruction_fixture_line_pairs()[1]
    snap = decode_shapez_copy_string(required_copy)
    cleanup = deconstruct_snapshot(snap)
    recon = run_topology_reconstruction(cleanup)
    complete = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
    return recon, complete


def test_canon_capacity_platform_count_matches_complete_map_shape_fields() -> None:
    recon, complete = _canon_cleanup_recon_complete()
    row = build_reconstruction_capacity_summary(complete_map=complete, resource_kind="shape")
    assert row["capacity_upper_bound_platform_count"] == complete.shape_field_cell_count
    assert overlay_field_cell_count(recon) < len(complete.field_cells)
