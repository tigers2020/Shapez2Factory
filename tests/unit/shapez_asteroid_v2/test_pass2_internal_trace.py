"""Pass2 internal fill: runtime ``TraceEvent`` rows parallel to ``beam_trace`` (slice 1)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import BBox
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    Pass1Result,
    ReconstructionDTO,
    SolverRunContext,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    CommitReason,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement import (
    pass2_internal as pass2_internal_mod,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement import (
    pass2_route_probe,
    run_pass1_outer_placement,
    run_pass2_internal_fill,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime.trace_collector import (
    TraceCollector,
)

_PASS2_PHASE = "pass2_internal"


def _mineable_grid(
    *,
    base_x: int,
    base_y: int,
    size: int,
    hole: tuple[int, int],
) -> tuple[tuple[int, int], ...]:
    return tuple(
        (x, y)
        for x in range(base_x, base_x + size)
        for y in range(base_y, base_y + size)
        if (x, y) != hole
    )


def _standard_recon_for_trace_tests(
    *,
    run_id: str,
    base_x: int = 20,
    base_y: int = 20,
    size: int = 6,
    hole: tuple[int, int] | None = None,
) -> ReconstructionDTO:
    _ = run_id
    hole_cell = hole if hole is not None else (base_x + 2, base_y + 2)
    mineable = _mineable_grid(base_x=base_x, base_y=base_y, size=size, hole=hole_cell)
    bbox = BBox(
        min_x=base_x,
        min_y=base_y,
        max_x=base_x + size - 1,
        max_y=base_y + size - 1,
    )
    shell = tuple(
        sorted(
            (
                c
                for c in mineable
                if min(
                    c[0] - bbox.min_x,
                    bbox.max_x - c[0],
                    c[1] - bbox.min_y,
                    bbox.max_y - c[1],
                )
                == 0
            ),
            key=lambda c: (c[1], c[0]),
        )
    )
    barrier = tuple({*shell, hole_cell})
    return ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=shell,
        full_barrier_cells=barrier,
        belt_cells=mineable,
        asteroid_bbox=bbox,
    )


def test_pass2_trace_emits_noop_when_no_remaining_mineable() -> None:
    mineable = ((200, 200),)
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        full_barrier_cells=(mineable),
        belt_cells=mineable,
        asteroid_bbox=BBox(min_x=200, min_y=200, max_x=200, max_y=200),
    )
    p1 = Pass1Result(
        placement_occupied_cells=mineable,
        output_stub_cells=((200, 199),),
        occupied_cells=((199, 200), (200, 199), (200, 200)),
    )
    ctx = SolverRunContext(run_id="p2_trace_noop", reconstruction=recon)
    trace = TraceCollector(ctx.run_id)
    run_pass2_internal_fill(ctx, p1, trace=trace)
    p2_events = trace.events_for_phase(_PASS2_PHASE)
    assert [e.event_type for e in p2_events] == ["pass2_noop"]
    assert all(not e.committed for e in p2_events)
    assert all(e.commit_reason is None for e in p2_events)


def test_pass2_trace_optimizer_selected_and_summary() -> None:
    recon = _standard_recon_for_trace_tests(run_id="p2_trace_sel")
    ctx = SolverRunContext(run_id="p2_trace_sel", reconstruction=recon)
    trace = TraceCollector(ctx.run_id)
    p1 = run_pass1_outer_placement(ctx, recon, trace=TraceCollector(ctx.run_id))
    p2 = run_pass2_internal_fill(ctx, p1, trace=trace)
    p2_events = trace.events_for_phase(_PASS2_PHASE)
    selected = [e for e in p2_events if e.event_type == "pass2_optimizer_selected"]
    summaries = [e for e in p2_events if e.event_type == "pass2_optimizer_summary"]
    assert len(p2.provisional_placements) == len(selected)
    assert len(summaries) == 1
    for e in selected:
        assert e.committed is True
        assert e.commit_reason is CommitReason.NORMAL_GAIN
    assert summaries[0].committed is False
    assert summaries[0].commit_reason is None


def test_pass2_trace_step_indices_monotonic_in_pass2_phase() -> None:
    recon = _standard_recon_for_trace_tests(run_id="p2_trace_steps", base_x=30, base_y=30)
    ctx = SolverRunContext(run_id="p2_trace_steps", reconstruction=recon)
    trace = TraceCollector(ctx.run_id)
    p1 = run_pass1_outer_placement(ctx, recon, trace=TraceCollector(ctx.run_id))
    run_pass2_internal_fill(ctx, p1, trace=trace)
    p2_events = trace.events_for_phase(_PASS2_PHASE)
    steps = [e.step_index for e in p2_events]
    assert steps == list(range(len(steps)))


def test_pass2_trace_stub_probe_rejected_matches_beam_rows() -> None:
    recon = _standard_recon_for_trace_tests(run_id="p2_trace_stub", base_x=40, base_y=40)
    ctx = SolverRunContext(run_id="p2_trace_stub", reconstruction=recon)
    trace = TraceCollector(ctx.run_id)
    p1 = run_pass1_outer_placement(ctx, recon, trace=TraceCollector(ctx.run_id))

    def _unreachable(
        cand: object,
        *,
        pass1_fixed_cells: object,
        reconstruction: object,
        ctx: object,
    ) -> pass2_route_probe.Pass2RouteProbe:
        _ = pass1_fixed_cells, reconstruction, ctx
        cid = getattr(cand, "candidate_id", "x")
        return pass2_route_probe.Pass2RouteProbe(
            candidate_id=str(cid),
            reachable=False,
            path_cells=(),
            goal_cell=None,
            reject_reason="pass2_stub_not_externally_reachable",
        )

    with patch.object(pass2_internal_mod, "probe_pass2_stub_route", side_effect=_unreachable):
        p2 = run_pass2_internal_fill(ctx, p1, trace=trace)

    beam_stub = [
        row
        for row in (p2.beam_trace or ())
        if row.get("reject_reason") == "pass2_stub_not_externally_reachable"
    ]
    trace_stub = [
        e
        for e in trace.events_for_phase(_PASS2_PHASE)
        if e.event_type == "pass2_stub_route_probe_rejected"
    ]
    assert len(beam_stub) == len(trace_stub)
    for e in trace_stub:
        assert e.committed is False
        assert e.commit_reason is None


def test_pass2_trace_candidate_rejected_events_parallel_to_beam() -> None:
    recon = _standard_recon_for_trace_tests(run_id="p2_trace_crej", base_x=50, base_y=50)
    ctx = SolverRunContext(run_id="p2_trace_crej", reconstruction=recon)
    trace = TraceCollector(ctx.run_id)
    p1 = run_pass1_outer_placement(ctx, recon, trace=TraceCollector(ctx.run_id))
    p2 = run_pass2_internal_fill(ctx, p1, trace=trace)
    beam_crej = [
        row
        for row in (p2.beam_trace or ())
        if row.get("placement_pass") == "pass2"
        and "event_type" not in row
        and row.get("reject_reason") not in (None, "pass2_stub_not_externally_reachable")
    ]
    trace_crej = [
        e
        for e in trace.events_for_phase(_PASS2_PHASE)
        if e.event_type == "pass2_candidate_rejected"
    ]
    assert len(beam_crej) == len(trace_crej)
    for e in trace_crej:
        assert e.committed is False
        assert e.commit_reason is None


@pytest.mark.parametrize(
    "non_committed_type",
    ("pass2_optimizer_summary", "pass2_noop"),
)
def test_pass2_non_committed_trace_events_have_no_commit_reason(non_committed_type: str) -> None:
    recon = _standard_recon_for_trace_tests(run_id="p2_nc", base_x=60, base_y=60)
    ctx = SolverRunContext(run_id="p2_nc", reconstruction=recon)
    trace = TraceCollector(ctx.run_id)
    p1 = run_pass1_outer_placement(ctx, recon, trace=TraceCollector(ctx.run_id))
    if non_committed_type == "pass2_noop":
        mineable = ((300, 300),)
        r = ReconstructionDTO(
            mineable_placement_cells=mineable,
            full_barrier_cells=(mineable),
            belt_cells=mineable,
            asteroid_bbox=BBox(min_x=300, min_y=300, max_x=300, max_y=300),
        )
        p1b = Pass1Result(
            placement_occupied_cells=mineable,
            output_stub_cells=((300, 299),),
            occupied_cells=((299, 300), (300, 299), (300, 300)),
        )
        ctx_b = SolverRunContext(run_id="p2_nc_noop", reconstruction=r)
        trace_b = TraceCollector(ctx_b.run_id)
        run_pass2_internal_fill(ctx_b, p1b, trace=trace_b)
        sample = next(
            e for e in trace_b.events_for_phase(_PASS2_PHASE) if e.event_type == non_committed_type
        )
    else:
        run_pass2_internal_fill(ctx, p1, trace=trace)
        sample = next(
            e for e in trace.events_for_phase(_PASS2_PHASE) if e.event_type == non_committed_type
        )
    assert sample.committed is False
    assert sample.commit_reason is None


def test_pass2_trace_stub_probe_rejected_has_no_commit_reason() -> None:
    recon = _standard_recon_for_trace_tests(run_id="p2_nc_stub", base_x=61, base_y=61)
    ctx = SolverRunContext(run_id="p2_nc_stub", reconstruction=recon)
    trace = TraceCollector(ctx.run_id)
    p1 = run_pass1_outer_placement(ctx, recon, trace=TraceCollector(ctx.run_id))

    def _unreachable(
        cand: object,
        *,
        pass1_fixed_cells: object,
        reconstruction: object,
        ctx: object,
    ) -> pass2_route_probe.Pass2RouteProbe:
        _ = pass1_fixed_cells, reconstruction, ctx
        cid = getattr(cand, "candidate_id", "x")
        return pass2_route_probe.Pass2RouteProbe(
            candidate_id=str(cid),
            reachable=False,
            path_cells=(),
            goal_cell=None,
            reject_reason="pass2_stub_not_externally_reachable",
        )

    with patch.object(pass2_internal_mod, "probe_pass2_stub_route", side_effect=_unreachable):
        run_pass2_internal_fill(ctx, p1, trace=trace)
    sample = next(
        e
        for e in trace.events_for_phase(_PASS2_PHASE)
        if e.event_type == "pass2_stub_route_probe_rejected"
    )
    assert sample.committed is False
    assert sample.commit_reason is None
