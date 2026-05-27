"""P1-ELCP-RF-D0: overlap-pack stale_candidate_reachable attribution (read-only)."""

from __future__ import annotations

import pytest

from harness.investigation.rttp_elcp_d0_stale_attribution import (
    ElcpD0Verdict,
    ElcpStaleAttributionClass,
    run_gate_a_elcp_d0_overlap_stale_forensics,
)
from tests.support.rttp_d0_gate_a_frozen_bounds import (
    D0_ATTRIBUTION_COVERAGE_MIN,
    D0_UNATTRIBUTED_RATIO_MAX,
    EXPECTED_OVERLAP_STALE_ROW_COUNT,
)


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


@pytest.mark.django_db
@pytest.mark.slow
def test_gate_a_elcp_d0_overlap_stale_attribution(
    imported_game_data_batch_module: object,
) -> None:
    result = run_gate_a_elcp_d0_overlap_stale_forensics(
        imported_game_data_batch_module=imported_game_data_batch_module,
    )

    assert result.git_sha != "unknown"
    assert len(result.rows) == EXPECTED_OVERLAP_STALE_ROW_COUNT
    assert all(
        r.probe_failure_class == "stale_candidate_reachable" for r in result.rows
    )

    unattributed = sum(
        1
        for r in result.rows
        if r.stale_attribution_class is ElcpStaleAttributionClass.UNATTRIBUTED_STALE
    )
    assert result.attribution_coverage >= D0_ATTRIBUTION_COVERAGE_MIN
    assert result.unattributed_ratio <= D0_UNATTRIBUTED_RATIO_MAX
    assert unattributed / len(result.rows) <= D0_UNATTRIBUTED_RATIO_MAX

    assert isinstance(result.verdict, ElcpD0Verdict)

    print(f"D0_GIT_SHA={result.git_sha}")
    print(f"D0_VERDICT={result.verdict.value}")
    print(f"D0_HISTOGRAM={result.histogram}")
    print(f"D0_ATTRIBUTION_COVERAGE={result.attribution_coverage}")
    print(f"D0_ROWS_JSON={[r.to_dict() for r in result.rows]}")
