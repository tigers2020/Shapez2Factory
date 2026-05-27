"""P1-ELCP-RF-C0: Gate A dual-mode primary commit re-gate (read-only)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.contracts.selection_mode import SelectionMode
from harness.investigation.rttp_elcp_c0_dual_mode import run_gate_a_elcp_c0_dual_mode
from tests.support.rttp_b1_gate_a_frozen_bounds import GATE_A_TARGET_FLOOR
from tests.support.rttp_c0_historical_anchors import (
    HISTORICAL_GREEDY_REGRET_COMMIT_ORDER_LEN,
    HISTORICAL_OVERLAP_PACK_COMMIT_ORDER_LEN,
)


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


@pytest.mark.django_db
@pytest.mark.slow
def test_gate_a_elcp_c0_dual_mode_primary_regate(
    imported_game_data_batch_module: object,
) -> None:
    baseline, overlap, table, verdict, reason = run_gate_a_elcp_c0_dual_mode(
        imported_game_data_batch_module=imported_game_data_batch_module,
    )

    assert baseline.git_sha == overlap.git_sha
    assert baseline.git_sha != "unknown"
    assert baseline.selection_mode == SelectionMode.GREEDY_REGRET.value
    assert overlap.selection_mode == SelectionMode.GREEDY_REGRET_OVERLAP_PACK.value

    assert baseline.commit_order_len == HISTORICAL_GREEDY_REGRET_COMMIT_ORDER_LEN
    assert overlap.commit_order_len >= GATE_A_TARGET_FLOOR
    assert overlap.commit_order_len >= baseline.commit_order_len

    assert baseline.bucket_coverage >= 0.95
    assert overlap.bucket_coverage >= 0.95

    assert verdict in ("BLOCKED", "NARROWED_TO_COMMIT_ORDER", "UNBLOCKED")

    print(f"C0_GIT_SHA={baseline.git_sha}")
    print(f"C0_DUAL_RUN_TABLE={table}")
    print(f"C0_BASELINE_SNAPSHOT={baseline.to_dict()}")
    print(f"C0_OVERLAP_SNAPSHOT={overlap.to_dict()}")
    print(f"C0_REGATE_VERDICT={verdict}")
    print(f"C0_REGATE_REASON={reason}")
    print(
        "C0_HISTORICAL_APPENDIX="
        f"greedy={HISTORICAL_GREEDY_REGRET_COMMIT_ORDER_LEN} "
        f"overlap_target={HISTORICAL_OVERLAP_PACK_COMMIT_ORDER_LEN} "
        "(not primary SoT)"
    )
