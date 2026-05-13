"""PlacementCommitState helpers (Algorithm §9.6 alignment)."""

from __future__ import annotations

from dataclasses import replace
from typing import Any
from unittest.mock import patch

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitRecord,
    PlacementCommitState,
    PlacementCommitTransitionError,
    apply_placement_commit_state_transition,
    transition_placement_record_to_rolled_back,
    unfinalized_placement_count_from_placement_commit_by_id,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.finalize import (
    build_final_solver_output,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_map_ops import (
    rollback_placement_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_merge_routing import (
    step4_routing_skipped_result,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation_contracts import (  # noqa: E501
    FinalValidationReport,
)


def test_transition_to_rolled_back_preserves_rollback_reason() -> None:
    rec = PlacementCommitRecord(
        placement_id="p1-000001",
        placement_pass="pass1",
        extractor_cell=(1, 1),
        extension_cells=(),
        stub_cell=(2, 1),
        transport_kind="shape_belt",
        state=PlacementCommitState.QUARANTINED_UNROUTED,
        route_id="route-x",
        rollback_reason="no_route",
    )
    out = transition_placement_record_to_rolled_back(rec)
    assert out.state == PlacementCommitState.ROLLED_BACK
    assert out.rollback_reason == "no_route"
    assert out.route_id is None


def test_transition_to_rolled_back_explicit_reason() -> None:
    rec = PlacementCommitRecord(
        placement_id="p1-000002",
        placement_pass="pass1",
        extractor_cell=(3, 1),
        extension_cells=(),
        stub_cell=(4, 1),
        transport_kind="shape_belt",
        state=PlacementCommitState.ROUTED_CONFIRMED,
        route_id="route-y",
        rollback_reason=None,
    )
    out = transition_placement_record_to_rolled_back(
        rec,
        rollback_reason="p2c_trunk_disconnect",
    )
    assert out.state == PlacementCommitState.ROLLED_BACK
    assert out.rollback_reason == "p2c_trunk_disconnect"
    assert out.route_id is None


def _empty_counts() -> dict[str, int]:
    return {"extractors": 0, "extensions": 0, "transport_cells": 0}


def test_routed_confirmed_may_quarantine_then_rolled_back() -> None:
    """§9.6 / 03: cascade·geometry 파손 시 ROUTED → QUARANTINE → ROLLED_BACK (P2-C 등)."""

    rec = PlacementCommitRecord(
        placement_id="p1-000010",
        placement_pass="pass1",
        extractor_cell=(1, 1),
        extension_cells=(),
        stub_cell=(2, 1),
        transport_kind="shape_belt",
        state=PlacementCommitState.ROUTED_CONFIRMED,
        route_id="route-z",
    )
    qu = apply_placement_commit_state_transition(
        rec,
        to=PlacementCommitState.QUARANTINED_UNROUTED,
        rollback_reason="p2c_trunk_disconnect",
        clear_route_id=True,
        context="test_quarantine",
    )
    assert qu.state == PlacementCommitState.QUARANTINED_UNROUTED
    assert qu.route_id is None
    rb = transition_placement_record_to_rolled_back(qu, rollback_reason="p2c_trunk_disconnect")
    assert rb.state == PlacementCommitState.ROLLED_BACK


def test_routed_confirmed_cannot_revert_to_provisional() -> None:
    rec = PlacementCommitRecord(
        placement_id="p1-000012",
        placement_pass="pass1",
        extractor_cell=(1, 1),
        extension_cells=(),
        stub_cell=(2, 1),
        transport_kind="shape_belt",
        state=PlacementCommitState.ROUTED_CONFIRMED,
        route_id="route-z2",
    )
    with pytest.raises(PlacementCommitTransitionError):
        apply_placement_commit_state_transition(
            rec,
            to=PlacementCommitState.PROVISIONAL_PLACED,
            context="illegal_revert",
        )


def test_rolled_back_cannot_transition_to_provisional() -> None:
    rec = PlacementCommitRecord(
        placement_id="p1-000011",
        placement_pass="pass1",
        extractor_cell=(1, 1),
        extension_cells=(),
        stub_cell=(2, 1),
        transport_kind="shape_belt",
        state=PlacementCommitState.ROLLED_BACK,
        rollback_reason="no_route",
    )
    with pytest.raises(PlacementCommitTransitionError):
        apply_placement_commit_state_transition(
            rec,
            to=PlacementCommitState.PROVISIONAL_PLACED,
            context="illegal_reentry",
        )


def test_unfinalized_count_from_placement_commit_by_id() -> None:
    m = {
        "a": PlacementCommitState.ROUTED_CONFIRMED.value,
        "b": PlacementCommitState.QUARANTINED_UNROUTED.value,
        "c": PlacementCommitState.PROVISIONAL_PLACED.value,
    }
    assert unfinalized_placement_count_from_placement_commit_by_id(m) == 2


def test_finalize_rejects_quarantine_in_placement_commit_by_id_when_counter_zero() -> None:
    """``placement_commit_by_id`` is authoritative for P2-B; do not allow ok tier if it desyncs."""

    empty: list[dict[str, Any]] = []
    routing_state: dict[str, Any] = {"hard_protected_corridors": []}
    step4 = replace(
        step4_routing_skipped_result(empty),
        placement_commit_by_id={"p1-000001": PlacementCommitState.QUARANTINED_UNROUTED.value},
    )
    good = FinalValidationReport(
        geometry_valid=True,
        connectivity_valid=True,
        disconnected_stub_count=0,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=0,
        overlap_violation_count=0,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
        extractor_count=0,
        extension_count=0,
        transport_cell_count=0,
        transport_connectivity_ok=True,
    )
    pass3_summary: dict[str, Any] = {
        "after_internal_transport_count": 0,
        "pass3_skipped": True,
        "pass3_committed": False,
    }
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.finalize."
        "_validate_final_mining_layout",
        return_value=good,
    ):
        _out, summary = build_final_solver_output(
            run_id="fsm-quarantine-desync",
            map_timeline=[{"mining_map": empty}, {"mining_map": empty}],
            map_after_pass1=empty,
            map_after_pass2=empty,
            map_after_routing=empty,
            map_final=empty,
            pass12_status_fields={},
            pass12_stats={},
            pass12_phase="test",
            pass12_skipped=True,
            pre_counts=_empty_counts(),
            post_pass2_counts=_empty_counts(),
            step4_result=step4,
            routing_state_summary=routing_state,
            post_step4_counts=_empty_counts(),
            unfinalized_placement_count=0,
            pass3_summary=pass3_summary,
            existing_layout_analysis=None,
            step_hash_step4=None,
            step_hash_pass3=None,
            step_hash_p4=None,
            solver_state_hash=None,
            replay_events=[],
            debug_location="tests.unit.shapez_asteroid.test_placement_commit_fsm",
        )

    assert summary["solver_termination"].endswith("failure")
    assert summary["return_reason"] == "validation_unfinalized_placement_failed"


def test_rollback_placement_cells_restores_mineable_and_drops_overlay() -> None:
    """§9.6: spatial rollback restores bundle coords from ``final_cells`` for mineable cells."""

    ext = (5, 5)
    stub = (6, 5)
    mineable = frozenset({ext, stub})
    final_cells = {
        ext: {"x": 5, "y": 5, "role": "occupied", "layout_kind": "shape_miner"},
        stub: {"x": 6, "y": 5, "role": "mineable", "layout_kind": None},
    }
    cells = {
        ext: dict(final_cells[ext]),
        stub: {"x": 6, "y": 5, "role": "belt", "surface": "shape", "placement_id": "p2-000001"},
    }
    rec = PlacementCommitRecord(
        placement_id="p2-000001",
        placement_pass="pass2",
        extractor_cell=ext,
        extension_cells=(),
        stub_cell=stub,
        transport_kind="shape_belt",
        state=PlacementCommitState.PROVISIONAL_PLACED,
    )
    rollback_placement_cells(cells, rec, final_cells, mineable)
    assert cells[ext] == final_cells[ext]
    assert cells[stub] == final_cells[stub]
