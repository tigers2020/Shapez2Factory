"""P3E3 guarded commit when default is True: small timeline/replay integration."""

from __future__ import annotations

from dataclasses import replace
from typing import Any
from unittest.mock import patch

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    P3E3_REJECT_HARD_PROTECTED_CORRIDOR,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3 import (
    pass3_e3_guarded as p3e3_guarded_mod,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    collect_routing_jobs,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import (
    solver_service,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_events import (  # noqa: E501
    SolverMutationEventKind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
    build_solver_timeline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_state_hash import (
    mining_map_state_hash,
    normalized_mining_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
    trace_run_scope,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline import (
    pass3 as pass3_stage,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    cells_dict_from_mining_map,
    validate_final_mining_layout,
)
from tests.unit.shapez_asteroid.test_pass1_timeline_integration import (
    _decoded_miners_with_belt_escape,
)
from tests.unit.shapez_asteroid.test_step4_merge_routing import (
    _decoded_fluid_miners_with_pipe_escape,
)


def _outlet_stub_cells(mining_map: list[dict[str, Any]]) -> list[tuple[int, int]]:
    raw = cells_dict_from_mining_map(mining_map)
    cells = {k: dict(v) for k, v in raw.items()}
    jobs = collect_routing_jobs(cells)
    return [j[1] for j in jobs]


def test_p3e3_default_true_small_shape_map_keeps_connectivity() -> None:
    out = build_solver_timeline(_decoded_miners_with_belt_escape())
    assert out["ok"] is True
    fv = out["final_validation"]
    assert fv["connectivity_valid"] is True
    assert fv["geometry_valid"] is True


def test_p3e3_default_true_small_fluid_map_keeps_connectivity() -> None:
    out = build_solver_timeline(_decoded_fluid_miners_with_pipe_escape())
    assert out["ok"] is True
    fv = out["final_validation"]
    assert fv["connectivity_valid"] is True
    assert fv["geometry_valid"] is True


def test_p3e3_default_true_keeps_fixed_output_stub() -> None:
    out = build_solver_timeline(_decoded_miners_with_belt_escape())
    assert out["ok"] is True
    step4 = next(f for f in out["solver_timeline"] if f["id"] == "solver_step4_routing")
    p3 = next(f for f in out["solver_timeline"] if f["id"] == "solver_pass3_transport")
    stubs = _outlet_stub_cells(step4["mining_map"])
    # Pass3 frame uses ``map_final`` (post-P4), not the intermediate Pass3 attempt.
    by_xy = {(int(r["x"]), int(r["y"])): r for r in p3["mining_map"]}
    for s in stubs:
        row = by_xy.get(s)
        assert row is not None
        assert row.get("role") == "belt"


def test_p3e3_default_true_rejects_hard_protected_corridor() -> None:
    orig = p3e3_guarded_mod._p3e3_collect_guarded_lex_replacement

    def inject_hard(**kwargs: Any) -> Any:
        out = orig(**kwargs)
        if out[-1] is not None:
            return out
        rem, rep, a, b, hu, su, err = out
        if err is not None:
            return out
        tc: dict[tuple[int, int], str] = kwargs["transport_cells"]  # type: ignore[assignment]
        outlets: tuple[tuple[int, int], ...] = tuple(kwargs["outlets_order"])  # type: ignore[assignment]
        anchor: tuple[int, int] = kwargs["anchor"]  # type: ignore[assignment]
        st = frozenset(outlets)
        removable = [c for c in tc if c not in st and c != anchor]
        if not removable:
            return out
        victim = min(removable)
        new_rem = frozenset(rem) | {victim} if rem else frozenset({victim})
        new_hard = frozenset(hu) | {victim}
        return (new_rem, rep, a, b, new_hard, su, None)

    with patch.object(p3e3_guarded_mod, "_p3e3_collect_guarded_lex_replacement", inject_hard):
        out = build_solver_timeline(_decoded_miners_with_belt_escape())

    assert out["ok"] is True
    p3 = next(f for f in out["solver_timeline"] if f["id"] == "solver_pass3_transport")
    s = p3["summary"]
    assert s.get("p3e3_guarded_commit_enabled") is True
    assert s.get("p3e3_guarded_commit_attempted") is True
    assert s.get("p3e3_guarded_committed") is False
    assert s.get("p3e3_guarded_commit_committed") is False
    assert (
        s.get("p3e3_guarded_commit_rejected_reason") == P3E3_REJECT_HARD_PROTECTED_CORRIDOR
        or s.get("p3e3_guarded_rejected_reason") == P3E3_REJECT_HARD_PROTECTED_CORRIDOR
    )


def test_p3e3_default_true_rolls_back_on_validation_failure() -> None:
    real_p3 = solver_service.run_pass3_transport_minimization_from_maps
    captured_hash: list[str] = []

    def p3_wrap(mm: list[dict[str, Any]], **kw: object) -> Any:
        a, b, c = real_p3(mm, **kw)
        if not c.get("pass3_skipped"):
            captured_hash.append(
                mining_map_state_hash(normalized_mining_map(a)),
            )
        return a, b, c

    real_val = validate_final_mining_layout

    def val_wrap(m: list[dict[str, Any]]) -> Any:
        r = real_val(m)
        if captured_hash and mining_map_state_hash(normalized_mining_map(m)) == captured_hash[0]:
            return replace(r, connectivity_valid=False, disconnected_stub_count=1)
        return r

    with (
        patch.object(solver_service, "run_pass3_transport_minimization_from_maps", p3_wrap),
        patch.object(pass3_stage, "_validate_final_mining_layout", val_wrap),
    ):
        out = build_solver_timeline(_decoded_miners_with_belt_escape())

    ss = out["solver_summary"]
    assert ss.get("pass3_reverted") is True
    assert ss.get("pass3_rollback_reason") == "final_validation_failed_after_pass3"
    assert ss.get("pass3_map_accepted") is False


def test_p3e3_default_true_emits_replay_event_and_summary() -> None:
    with trace_run_scope():
        out = build_solver_timeline(_decoded_miners_with_belt_escape())

    assert out["ok"] is True
    replay = out.get("solver_replay") or {}
    events = replay.get("events") or []
    kinds = {e.get("kind") for e in events if isinstance(e, dict)}
    assert SolverMutationEventKind.PASS3_LAYOUT_SNAPSHOT.value in kinds
    assert SolverMutationEventKind.MAP_DIFF_COMMITTED.value in kinds

    p3 = next(f for f in out["solver_timeline"] if f["id"] == "solver_pass3_transport")
    s = p3["summary"]
    assert s.get("p3e3_guarded_commit_enabled") is True
    assert s.get("p3e3_guarded_commit_attempted") is True
    assert "p3e3_guarded_rejected_reason" in s
