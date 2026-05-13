"""Pass12 trace merge ctx refreshes replay layout observation (STEP10 UI)."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass1_timeline_integration as p12_tl,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass1_timeline_integration import (  # noqa: E501
    dominant_surface_from_map,
    maybe_trace_publish_pass12_scratch_after_commit,
    mineable_and_asteroid_coords,
    scratch_from_working_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import (
    solver_trace as solver_trace_mod,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
    trace_bind_pass12_merge_context,
    trace_reset_pass12_merge_context,
)


def _af(x: int, y: int) -> dict:
    return {
        "x": x,
        "y": y,
        "role": "inferred",
        "layout_kind": "asteroid_field",
        "surface": "shape",
    }


def test_maybe_trace_publish_pass12_sets_replay_layout_ctx(
    monkeypatch: object, tmp_path: object, settings: object
) -> None:
    monkeypatch.setenv("SHAPEZ_SOLVER_ALGO_DEBUG", "1")
    settings.BASE_DIR = tmp_path
    fm = [_af(0, 0), _af(1, 0), _af(2, 0)]
    wm = [dict(r) for r in fm]
    is_ext = lambda c: False  # noqa: E731
    mineable, _asteroid = mineable_and_asteroid_coords(fm)
    scratch, transport_init, blocked_init = scratch_from_working_map(wm, mineable_coords=mineable)
    surface = dominant_surface_from_map(fm)
    scratch.transport_kind = "shape_belt"
    tok = trace_bind_pass12_merge_context(
        {
            "working_map": wm,
            "final_mining_map": fm,
            "transport_init": transport_init,
            "blocked_init": blocked_init,
            "mineable": mineable,
            "surface": surface,
            "is_external": is_ext,
        }
    )
    try:
        scratch.next_placement_seq = 1
        maybe_trace_publish_pass12_scratch_after_commit(scratch)
        cur = solver_trace_mod._replay_layout_ctx_var.get()
        assert isinstance(cur, dict)
        mm = cur.get("mining_map")
        assert isinstance(mm, list)
        assert len(mm) >= 1
    finally:
        trace_reset_pass12_merge_context(tok)


def test_integrate_pass12_replay_sink_replay_frame_has_mining_map_payload(
    monkeypatch: object, tmp_path: object, settings: object
) -> None:
    monkeypatch.setenv("SHAPEZ_SOLVER_ALGO_DEBUG", "1")
    settings.BASE_DIR = tmp_path
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_events import (  # noqa: E501
        SolverMutationEventKind,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
        trace_bind_replay_events,
        trace_event,
        trace_run_id_current,
        trace_run_scope,
    )

    fm = [_af(i, 0) for i in range(12)]
    wm = [dict(r) for r in fm]
    is_ext = lambda c: c[0] > 50  # noqa: E731
    sink: list[dict] = []
    with trace_run_scope():
        trace_bind_replay_events(sink)
        p12_tl.integrate_pass12_placement_into_working_map(
            working_map=wm,
            final_mining_map=fm,
            is_external=is_ext,
            replay_events=sink,
        )
        rid = trace_run_id_current()
        assert rid is not None
        for _ in range(15):
            trace_event("test", "phase_checkpoint", {"probe": True})
    rfs = [e for e in sink if e.get("kind") == SolverMutationEventKind.REPLAY_FRAME.value]
    assert rfs, "expected replay_frame events in sink"
    with_maps = [
        e
        for e in rfs
        if isinstance(e.get("payload"), dict) and isinstance(e["payload"].get("mining_map"), list)
    ]
    assert with_maps, "expected at least one replay_frame with mining_map in payload"
