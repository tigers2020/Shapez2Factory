"""P1-ELCP-RF-F1.1: Gate A private_route_overlap slice forensic (read-only)."""

from __future__ import annotations

import pytest

from harness.investigation.rttp_elcp_f11_private_overlap_forensic import (
    ElcpF11PrivateOverlapRootCause,
    run_gate_a_elcp_f11_private_overlap_forensics,
)
from tests.support.rttp_e0_gate_a_frozen_bounds import EXPECTED_OVERLAP_STALE_ROW_COUNT
from tests.support.rttp_f11_gate_a_frozen_bounds import (
    F11_EXPECTED_PRIVATE_OVERLAP_ROW_COUNT,
    F11_UNCLEAR_MAX_ROWS,
)


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


@pytest.mark.django_db
@pytest.mark.slow
def test_gate_a_f11_private_overlap_forensic(
    imported_game_data_batch_module: object,
) -> None:
    result = run_gate_a_elcp_f11_private_overlap_forensics(
        imported_game_data_batch_module=imported_game_data_batch_module,
    )
    assert result.git_sha != "unknown"
    assert result.mirror_parity_ok is True
    assert result.parent_stale_row_count == EXPECTED_OVERLAP_STALE_ROW_COUNT
    assert len(result.rows) == F11_EXPECTED_PRIVATE_OVERLAP_ROW_COUNT
    assert result.unclear_count <= F11_UNCLEAR_MAX_ROWS

    print(f"F11_GIT_SHA={result.git_sha}")
    print(f"F11_PARENT_STALE={result.parent_stale_row_count}")
    print(f"F11_SLICE_ROWS={len(result.rows)}")
    print(f"F11_ROOT_CAUSE_HISTOGRAM={result.root_cause_histogram}")
    print(f"F11_UNCLEAR_COUNT={result.unclear_count}")
    print(f"F11_F12_NOMINATION={result.f12_nomination.to_dict()}")
    print(f"F11_ROWS_JSON={[r.to_dict() for r in result.rows]}")

    for row in result.rows:
        assert row.elcp_e0_mechanism_class == "private_route_overlap"
        assert row.private_overlap_cell_count > 0
        assert row.f11_root_cause is not ElcpF11PrivateOverlapRootCause.UNCLEAR_NEEDS_TRACE or (
            result.unclear_count <= F11_UNCLEAR_MAX_ROWS
        )
