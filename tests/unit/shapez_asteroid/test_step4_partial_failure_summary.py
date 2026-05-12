"""STEP4 partial failure: solver_summary lineage and finalized-layout contract."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass1_timeline_integration import (  # noqa: E501
    integrate_pass12_placement_into_working_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
    build_solver_timeline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline import (
    step4 as step4_stage,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_merge_routing as step4_mod,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    cells_dict_from_mining_map,
    external_predicate_for_mining_map,
)
from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline


def _decoded_shape_miners_with_belt_escape() -> dict[str, Any]:
    from tests.unit.shapez_asteroid.test_step4_merge_routing import (
        _decoded_shape_miners_with_belt_escape as _fixture,
    )

    return _fixture()


@pytest.mark.unit
def test_step4_partial_failure_summary_known_good_after_rollback() -> None:
    """Partial STEP4 yields partial_success, explicit summary, zero unfinalized final rows."""

    decoded = _decoded_shape_miners_with_belt_escape()
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    _p1, m2, _stats = integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    jobs = step4_mod._collect_routing_jobs(dict(cells_dict_from_mining_map(m2)))
    if not jobs:
        pytest.skip("no routing jobs in fixture")
    _ext_cell, fail_stub, _tk, fail_pid = jobs[-1]
    if not isinstance(fail_pid, str) or not fail_pid:
        pytest.skip("fixture job missing placement_id")

    real = step4_mod._dijkstra_route

    def wrapped(stub_cell: Coord, *args: Any, **kwargs: Any) -> tuple[Coord, ...] | None:
        if stub_cell == fail_stub:
            return None
        return real(stub_cell, *args, **kwargs)

    real_run_step4 = step4_mod.run_step4_merge_aware_routing

    def forced_step4(*args: Any, **kwargs: Any) -> Any:
        kwargs["force_route_attempt_placement_ids"] = frozenset({fail_pid})
        return real_run_step4(*args, **kwargs)

    with (
        patch.object(step4_mod, "_dijkstra_route", new=wrapped),
        patch.object(step4_stage, "run_step4_merge_aware_routing", new=forced_step4),
    ):
        out = build_solver_timeline(decoded)

    assert out["solver_termination"] == "partial_success"
    assert out["return_reason"] == "step4_partial_failure"
    summ = out["solver_summary"]
    fv = out["final_validation"]

    assert summ["step4_partial_failure"] is True
    assert summ["step4_complete_commit_success"] is False
    assert summ["step4_committed"] is False
    assert summ["step4_returned_layout_source"] == "known_good_after_rollback"
    assert summ["final_unfinalized_placement_count"] == 0
    assert summ["unfinalized_placement_count"] == 0

    assert fv["final_unfinalized_placement_count"] == 0
    assert fv["step4_partial_failure"] is True
    assert fv["step4_returned_layout_source"] == "known_good_after_rollback"

    assert "after_pass2_extractor_count" in summ
    assert "final_extractor_count" in summ
    assert summ["final_extractor_count"] == fv["extractor_count"]
    assert isinstance(summ["extractor_loss_due_to_step4_rollback"], int)
    assert isinstance(summ["route_loss_due_to_step4_rollback"], int)
    assert summ["route_loss_due_to_step4_rollback"] >= 1
    assert isinstance(summ["internal_quarantined_count"], int)
    assert isinstance(summ["step4_known_good_route_count"], int)
    assert isinstance(summ["step4_failed_route_count"], int)
    assert summ["step4_failed_route_count"] >= 1
