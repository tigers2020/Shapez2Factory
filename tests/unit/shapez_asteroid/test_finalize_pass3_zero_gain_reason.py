"""Finalize: ``pass3_zero_gain_reason`` heuristics."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.finalize import (
    _compute_pass3_zero_gain_reason,
)


def test_pass3_zero_gain_reason_skipped_returns_none() -> None:
    assert (
        _compute_pass3_zero_gain_reason(
            {"pass3_skipped": True, "pass3_internal_transport_saved": 0}
        )
        is None
    )


def test_pass3_zero_gain_reason_saved_positive_returns_none() -> None:
    assert (
        _compute_pass3_zero_gain_reason(
            {"pass3_skipped": False, "pass3_internal_transport_saved": 3}
        )
        is None
    )


def test_pass3_zero_gain_reason_hard_protected() -> None:
    r = _compute_pass3_zero_gain_reason(
        {
            "pass3_skipped": False,
            "pass3_internal_transport_saved": 0,
            "pass3_rejected_reason": "rejected_by_hard_protected_corridor",
        }
    )
    assert r == "all_routes_hard_protected"


def test_pass3_zero_gain_reason_default_bucket() -> None:
    r = _compute_pass3_zero_gain_reason(
        {"pass3_skipped": False, "pass3_internal_transport_saved": 0}
    )
    assert r == "no_candidate_route_improved_internal_transport"
