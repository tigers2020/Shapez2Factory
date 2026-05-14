"""Pass12 merged-seed orphan bootstrap retry: NDJSON / failure-class telemetry (S2)."""

from __future__ import annotations

import copy

from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass12_merged_layout_seed as p12,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.orphan_island_external_bootstrap import (  # noqa: E501
    empty_orphan_island_bootstrap_trace,
)


def _base_drop_row() -> dict:
    return {
        "miner_cell": [9, 5],
        "preserve_drop_reason": "NO_MATCHING_STUB",
        "expected_stub_role": "pipe",
        "adjacent_transport_cells": [{"role": "pipe", "x": 10, "y": 5}],
        "adjacent_cardinal_cells": [],
        "preserve_stub_recovery": {
            "accepted": False,
            "rejected_reason": "no_same_kind_route",
            "rejected_reason_subtype": "frontier_cap",
        },
    }


def test_apply_seed_drop_telemetry_bootstrap_failure_geometry_maps_exterior_reason() -> None:
    row = _base_drop_row()
    trace = empty_orphan_island_bootstrap_trace()
    trace["bootstrap_failure_reason"] = "geometry_no_path"
    p12._apply_seed_orphan_bootstrap_drop_telemetry(
        row,
        seed_bootstrap_trace=trace,
        seed_bootstrap_invoked=True,
        recovery_retry_after_bootstrap=False,
        initial_stub_trace=copy.deepcopy(row),
    )
    assert row["bootstrap_attempted"] is True
    assert row["bootstrap_committed"] is False
    assert row["recovery_retry_after_bootstrap"] is False
    assert row["final_rejected_reason"] == "no_bootstrap_route_to_exterior"
    assert row["preserve_route_failure_class"] == "no_external_bootstrap_available"


def test_apply_seed_drop_telemetry_post_bootstrap_retry_still_no_route() -> None:
    row = _base_drop_row()
    trace = empty_orphan_island_bootstrap_trace()
    trace["bootstrap_attempted"] = True
    trace["bootstrap_committed"] = True
    p12._apply_seed_orphan_bootstrap_drop_telemetry(
        row,
        seed_bootstrap_trace=trace,
        seed_bootstrap_invoked=True,
        recovery_retry_after_bootstrap=True,
        initial_stub_trace={"preserve_stub_recovery": {"rejected_reason": "no_same_kind_route"}},
    )
    assert row["bootstrap_committed"] is True
    assert row["recovery_retry_after_bootstrap"] is True
    assert row["final_rejected_reason"] == "no_same_kind_route_after_bootstrap_failure"
    assert row["preserve_route_failure_class"] == "recovery_failed_after_bootstrap"


def test_apply_seed_drop_telemetry_occupied_neighbor_ring_stays_local_geometry() -> None:
    row = _base_drop_row()
    psr = row["preserve_stub_recovery"]
    assert isinstance(psr, dict)
    psr["rejected_reason_subtype"] = "occupied_neighbor_ring"
    trace = empty_orphan_island_bootstrap_trace()
    trace["bootstrap_attempted"] = True
    trace["bootstrap_committed"] = True
    p12._apply_seed_orphan_bootstrap_drop_telemetry(
        row,
        seed_bootstrap_trace=trace,
        seed_bootstrap_invoked=True,
        recovery_retry_after_bootstrap=True,
        initial_stub_trace={"preserve_stub_recovery": {"rejected_reason": "no_stub_space"}},
    )
    assert row["preserve_route_failure_class"] == "occupied_neighbor_ring"
    assert "commit_reason" not in psr


def test_apply_seed_drop_telemetry_not_invoked_marks_bootstrap_attempted_false() -> None:
    row = _base_drop_row()
    trace = empty_orphan_island_bootstrap_trace()
    p12._apply_seed_orphan_bootstrap_drop_telemetry(
        row,
        seed_bootstrap_trace=trace,
        seed_bootstrap_invoked=False,
        recovery_retry_after_bootstrap=False,
        initial_stub_trace=None,
    )
    assert row["bootstrap_attempted"] is False
    assert row["bootstrap_committed"] is False
