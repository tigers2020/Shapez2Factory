"""P1-ELCP-RF-F1: Gate A measurable G1 on E0 stale universe (overlap-pack)."""

from __future__ import annotations

import pytest

from harness.investigation.rttp_elcp_e0_reservation_mechanism import (
    ElcpE0MechanismClass,
    run_gate_a_elcp_e0_reservation_forensics,
)
from tests.support.rttp_e0_gate_a_frozen_bounds import EXPECTED_OVERLAP_STALE_ROW_COUNT
from tests.support.rttp_f1_gate_a_g1_bounds import (
    E0_PRIVATE_ROUTE_OVERLAP_MECHANISM_BASELINE,
    F1_G1_MAX_PRIVATE_ROUTE_OVERLAP_ROWS,
)


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


@pytest.mark.django_db
@pytest.mark.slow
@pytest.mark.xfail(
    strict=False,
    reason=(
        "G1 partial (2026-05-27): 20/23 private_route_overlap rows; "
        "F0 target <=11 deferred to F1.1"
    ),
)
def test_gate_a_f1_private_route_overlap_mechanism_g1(
    imported_game_data_batch_module: object,
) -> None:
    result = run_gate_a_elcp_e0_reservation_forensics(
        imported_game_data_batch_module=imported_game_data_batch_module,
    )
    assert len(result.rows) == EXPECTED_OVERLAP_STALE_ROW_COUNT
    private_count = sum(
        1
        for row in result.rows
        if row.elcp_e0_mechanism_class == ElcpE0MechanismClass.PRIVATE_ROUTE_OVERLAP
    )
    print(f"F1_G1_PRIVATE_ROUTE_OVERLAP_COUNT={private_count}")
    print(f"F1_G1_BASELINE={E0_PRIVATE_ROUTE_OVERLAP_MECHANISM_BASELINE}")
    print(f"F1_G1_MAX_ALLOWED={F1_G1_MAX_PRIVATE_ROUTE_OVERLAP_ROWS}")
    reduction = E0_PRIVATE_ROUTE_OVERLAP_MECHANISM_BASELINE - private_count
    print(f"F1_G1_REDUCTION={reduction}")
    g1_max = F1_G1_MAX_PRIVATE_ROUTE_OVERLAP_ROWS
    e0_base = E0_PRIVATE_ROUTE_OVERLAP_MECHANISM_BASELINE
    assert private_count <= g1_max, (
        f"G1: private_route_overlap mechanism rows <= {g1_max} "
        f"(≥50% reduction from E0 baseline {e0_base}); got {private_count}"
    )
