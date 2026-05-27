"""P1-ELCP-RF-E0: overlap-pack post-probe reservation mechanism (read-only)."""

from __future__ import annotations

import pytest

from harness.investigation.rttp_elcp_e0_reservation_mechanism import (
    ElcpE0Verdict,
    is_unattributed_mechanism_class,
    run_gate_a_elcp_e0_reservation_forensics,
)
from tests.support.rttp_e0_gate_a_frozen_bounds import (
    E0_MECHANISM_COVERAGE_MIN,
    E0_UNATTRIBUTED_RATIO_MAX,
    EXPECTED_OVERLAP_STALE_ROW_COUNT,
)


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


@pytest.mark.django_db
@pytest.mark.slow
def test_gate_a_elcp_e0_overlap_reservation_mechanism(
    imported_game_data_batch_module: object,
) -> None:
    result = run_gate_a_elcp_e0_reservation_forensics(
        imported_game_data_batch_module=imported_game_data_batch_module,
    )

    assert result.git_sha != "unknown"
    assert len(result.rows) == EXPECTED_OVERLAP_STALE_ROW_COUNT
    assert result.mirror_parity_ok is True

    unattributed = sum(
        1 for r in result.rows if is_unattributed_mechanism_class(r.elcp_e0_mechanism_class)
    )
    coverage = 1.0 - (unattributed / len(result.rows))
    assert coverage >= E0_MECHANISM_COVERAGE_MIN
    assert (unattributed / len(result.rows)) <= E0_UNATTRIBUTED_RATIO_MAX

    assert isinstance(result.verdict, ElcpE0Verdict)

    print(f"E0_GIT_SHA={result.git_sha}")
    print(f"E0_VERDICT={result.verdict.value}")
    print(f"E0_NOMINATION={result.nomination.to_dict()}")
    print(f"E0_MECHANISM_HISTOGRAM={result.mechanism_histogram}")
    print(f"E0_APPENDIX={result.appendix_aggregate.to_dict()}")
    print(f"E0_ROWS_JSON={[r.to_dict() for r in result.rows]}")
