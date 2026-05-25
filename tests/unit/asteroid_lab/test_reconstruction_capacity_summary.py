"""PR-2a — reconstruction capacity from terrain + MiningExtractionRule only."""

from __future__ import annotations

from decimal import Decimal

import pytest

from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
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


def _recon_with_confirmed(
    n: int, *, cell_kind: str = "asteroid_shape_field"
) -> ReconstructionResult:
    cells = tuple(_cell(i, 0, cell_kind=cell_kind) for i in range(n))
    confirmed = frozenset((i, 0) for i in range(n))
    return ReconstructionResult(
        cells=cells,
        confirmed_cells=confirmed,
        ambiguous_cells=frozenset(),
        external_void_cells=frozenset(),
        confidence_score=0.94,
        quality_tier="CONFIDENT_RECONSTRUCTION",
    )


def test_decimal_str_four_places() -> None:
    assert decimal_str(Decimal("480")) == "480.0000"


def test_shape_capacity_uses_canon_480_per_platform() -> None:
    recon = _recon_with_confirmed(2)
    row = build_reconstruction_capacity_summary(recon=recon, resource_kind="shape")
    rule = get_active_rule("shape")
    assert row["max_output_per_miner"] == decimal_str(max_output_per_miner(rule))
    assert row["max_output_per_miner"] == "480.0000"
    assert row["capacity_upper_bound_platform_count"] == 2
    assert row["max_throughput_per_min"] == "960.0000"
    assert row["source_kind"] == "CANON_MANUAL"


def test_fluid_capacity_uses_canon_4800_per_platform() -> None:
    recon = _recon_with_confirmed(1, cell_kind="asteroid_fluid_field")
    row = build_reconstruction_capacity_summary(recon=recon, resource_kind="fluid")
    assert row["max_output_per_miner"] == "4800.0000"
    assert row["max_throughput_per_min"] == "4800.0000"


def test_envelope_shape_only_fluid_platform_count_zero() -> None:
    recon = _recon_with_confirmed(3)
    env = build_reconstruction_capacity_envelope(recon=recon)
    assert env["capacity_basis"] == "terrain_upper_bound"
    assert env["primary_resource_kind"] == "shape"
    assert env["by_resource"]["shape"]["max_throughput_per_min"] == "1440.0000"
    assert env["by_resource"]["fluid"]["max_throughput_per_min"] == "0.0000"
    assert env["by_resource"]["fluid"]["capacity_upper_bound_platform_count"] == 0


def test_fluid_dominant_asteroid_uses_fluid_platform_count() -> None:
    recon = _recon_with_confirmed(2, cell_kind="asteroid_fluid_field")
    row = build_reconstruction_capacity_summary(recon=recon, resource_kind="fluid")
    assert row["capacity_upper_bound_platform_count"] == 2
    assert row["max_throughput_per_min"] == "9600.0000"
    assert detect_primary_resource_kind(recon) == "fluid"


def test_observability_snapshot_fields() -> None:
    recon = _recon_with_confirmed(5)
    obs = build_reconstruction_observability(recon=recon)
    assert obs["cell_count"] == 5
    assert obs["confirmed_cell_count"] == 5
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
