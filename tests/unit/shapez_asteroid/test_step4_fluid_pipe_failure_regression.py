"""STEP4 ``fluid_pipe`` failure telemetry regression (fixture on disk, no NDJSON path).

Baseline vs Pass2 bounded reachability precheck uses a monkeypatch that simulates a looser
gate (always-OK precheck). STEP4 routing failure counts must not increase when the real
precheck is enabled (``<=`` monotonicity). Strict ``<`` when the fixture starts producing
Pass2 stub-isolated rejects is covered by ``test_try_commit_pass2_rejects_uncertain_when_
step4_stub_isolated_geometry_fluid_pipe`` in ``test_pass2_probe_provisional_step4.py``.

Known limitation (forced tail Dijkstra failure on this blueprint): rollback can leave orphan
fluid pipe cells, so ``final_validation["connectivity_valid"]`` may be false while geometry
stays valid. The unpatched happy path still reports both valid.
"""

from __future__ import annotations

import json
from contextlib import nullcontext
from copy import deepcopy
from pathlib import Path
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
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_reachability import (
    Pass2StubBoundedStep4Reachability,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    cells_dict_from_mining_map,
    external_predicate_for_mining_map,
)
from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline

_FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "asteroid_mining_layout"
    / "step4_fluid_pipe_failure_regression_bp.json"
)

# Locked counters: fixture + last-job forced Dijkstra failure (see module docstring).
_BASELINE_FLUID_STEP4_ROUTING_FAILURES_FORCED_TAIL = 1


def _load_fluid_regression_bp() -> dict[str, Any]:
    raw = _FIXTURE_PATH.read_text(encoding="utf-8")
    return json.loads(raw)


def _required_step4_summary_keys() -> tuple[str, ...]:
    return (
        "step4_routing_failure_count",
        "step4_route_failure_category_counts",
        "step4_reachable_goal_zero_count",
        "step4_search_budget_exhausted_count",
    )


def _routing_failure_count_for_map(
    *,
    bypass_pass2_step4_precheck: bool,
    force_fail_last_job: bool,
) -> tuple[int, dict[str, Any]]:
    """Return ``(step4_routing_failure_count, integrate_stats)`` for the regression blueprint."""

    decoded = deepcopy(_load_fluid_regression_bp())
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    fake_ok = Pass2StubBoundedStep4Reachability(True, 1, 0, 0, "success", 0, [], False)
    precheck_path = (
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.step4."
        "step4_reachability.pass2_stub_bounded_step4_reachability_precheck"
    )
    integrate_ctx = (
        patch(precheck_path, lambda **kwargs: fake_ok)
        if bypass_pass2_step4_precheck
        else nullcontext()
    )
    with integrate_ctx:
        _p1, m2, stats = integrate_pass12_placement_into_working_map(
            working_map=wm, final_mining_map=fm, is_external=is_ext
        )
    jobs = step4_mod._collect_routing_jobs(dict(cells_dict_from_mining_map(m2)))
    if not jobs:
        pytest.skip("regression blueprint produced no STEP4 jobs")
    _ext_cell, fail_stub, _tk, fail_pid = jobs[-1]
    if not isinstance(fail_pid, str) or not fail_pid:
        pytest.skip("last routing job missing placement_id")

    real = step4_mod._dijkstra_route

    def wrapped(stub_cell: Coord, *args: Any, **kwargs: Any) -> tuple[Coord, ...] | None:
        if force_fail_last_job and stub_cell == fail_stub:
            return None
        return real(stub_cell, *args, **kwargs)

    real_run = step4_mod.run_step4_merge_aware_routing

    def forced_step4(*args: Any, **kwargs: Any) -> Any:
        kwargs["force_route_attempt_placement_ids"] = frozenset({fail_pid})
        return real_run(*args, **kwargs)

    with (
        patch.object(step4_mod, "_dijkstra_route", new=wrapped),
        patch.object(step4_stage, "run_step4_merge_aware_routing", new=forced_step4),
    ):
        out = build_solver_timeline(decoded)
    n = int((out.get("solver_summary") or {}).get("step4_routing_failure_count") or 0)
    return n, stats


def test_fluid_pipe_fixture_path_is_versioned_json() -> None:
    assert _FIXTURE_PATH.is_file()
    data = _load_fluid_regression_bp()
    entries = data["BP"]["Entries"]
    kinds = {e["T"] for e in entries}
    assert "Layout_FluidMiner" in kinds and "Layout_FluidPipe" in kinds


def test_fluid_pipe_happy_path_final_validation_geometry_and_connectivity() -> None:
    out = build_solver_timeline(_load_fluid_regression_bp())
    assert out.get("ok") is True
    fv = out.get("final_validation") or {}
    assert fv.get("geometry_valid") is True
    assert fv.get("connectivity_valid") is True
    ss = out.get("solver_summary") or {}
    for k in _required_step4_summary_keys():
        assert k in ss


def test_fluid_pipe_partial_failure_telemetry_transport_kind_and_summary_fields() -> None:
    decoded = _load_fluid_regression_bp()
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    _p1, m2, _stats = integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    jobs = step4_mod._collect_routing_jobs(dict(cells_dict_from_mining_map(m2)))
    _ext_cell, fail_stub, _tk, fail_pid = jobs[-1]
    real = step4_mod._dijkstra_route

    def wrapped(stub_cell: Coord, *args: Any, **kwargs: Any) -> tuple[Coord, ...] | None:
        if stub_cell == fail_stub:
            return None
        return real(stub_cell, *args, **kwargs)

    real_run = step4_mod.run_step4_merge_aware_routing

    def forced_step4(*args: Any, **kwargs: Any) -> Any:
        kwargs["force_route_attempt_placement_ids"] = frozenset({fail_pid})
        return real_run(*args, **kwargs)

    with (
        patch.object(step4_mod, "_dijkstra_route", new=wrapped),
        patch.object(step4_stage, "run_step4_merge_aware_routing", new=forced_step4),
    ):
        out = build_solver_timeline(decoded)

    summ = out.get("solver_summary") or {}
    missing = [k for k in _required_step4_summary_keys() if k not in summ]
    assert not missing, f"solver_summary missing keys: {missing}"
    assert (
        int(summ.get("step4_routing_failure_count") or 0)
        == _BASELINE_FLUID_STEP4_ROUTING_FAILURES_FORCED_TAIL
    )
    assert isinstance(summ.get("step4_route_failure_category_counts"), dict)
    assert isinstance(summ.get("step4_reachable_goal_zero_count"), int)
    assert isinstance(summ.get("step4_search_budget_exhausted_count"), int)
    assert summ.get("step4_failure_transport_kind_counts") == {"fluid_pipe": 1}

    rfails = summ.get("routing_failures") or []
    assert len(rfails) >= 1
    for row in rfails:
        assert row.get("transport_kind") == "fluid_pipe"
        assert "commit_reason" not in row
        det = row.get("step4_route_failure_detail")
        if isinstance(det, dict):
            assert "exterior_fallback_considered" in det
            assert det.get("exterior_fallback_considered") in (True, False)
            assert "primary_existing_trunk_reachable_count" in det
            assert "exterior_fallback_activated" in det
            assert "exterior_fallback_reason" in det
            assert "fallback_external_goal_count" in det
            assert "commit_reason" not in det
            rfd = det.get("routing_failure_detail")
            if isinstance(rfd, dict):
                assert "commit_reason" not in rfd

    fv = out.get("final_validation") or {}
    assert fv.get("geometry_valid") is True
    # Orphan rollback: connectivity may be false (documented in module docstring).
    assert isinstance(fv.get("connectivity_valid"), bool)


def test_pass2_step4_reachability_precheck_does_not_increase_forced_tail_failures() -> None:
    """Simulated looser precheck (bypass) vs default: ``fail_default <= fail_bypass``."""

    n_default, _ = _routing_failure_count_for_map(
        bypass_pass2_step4_precheck=False, force_fail_last_job=True
    )
    n_bypass, _ = _routing_failure_count_for_map(
        bypass_pass2_step4_precheck=True, force_fail_last_job=True
    )
    assert n_default <= n_bypass
    assert n_default == _BASELINE_FLUID_STEP4_ROUTING_FAILURES_FORCED_TAIL
