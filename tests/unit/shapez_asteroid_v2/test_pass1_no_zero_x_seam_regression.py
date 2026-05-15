"""Pass1 must never use ``x == 0`` stubs or treat the missing column as escape space."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import BBox
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    ReconstructionDTO,
    SolverRunContext,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.grid import (
    step_blueprint_cell,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement.pass1_outer import (
    run_pass1_outer_placement,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime.trace_collector import (
    TraceCollector,
)


def test_step_cell_never_produces_x_zero() -> None:
    assert step_blueprint_cell((1, 0), (-1, 0))[0] == -1
    assert step_blueprint_cell((-1, 0), (1, 0))[0] == 1


def test_pass1_no_commit_stub_at_x_zero_two_column_mineable() -> None:
    mineable = tuple((x, y) for x in (-1, 1) for y in range(0, 4))
    bbox = BBox(min_x=-1, min_y=0, max_x=1, max_y=3)
    barrier = tuple(mineable)
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=mineable,
        full_barrier_cells=barrier,
        belt_cells=mineable,
        asteroid_bbox=bbox,
    )
    ctx = SolverRunContext(run_id="seam_regression", reconstruction=recon)
    events: list[dict[str, object]] = []
    p1 = run_pass1_outer_placement(
        ctx, recon, replay_events=events, replay_event_cap=None, trace=TraceCollector(ctx.run_id)
    )

    commits = [e for e in events if e.get("kind") == "commit_bundle"]
    for e in commits:
        stub = e.get("output_stub_cell")
        assert isinstance(stub, list) and len(stub) == 2
        assert stub[0] != 0
        assert e.get("output_stub_physical") is True

    for b in p1.placements:
        assert b.output_stub.cell[0] != 0
        assert b.extractor.cell[0] != 0
        for ext in b.extensions:
            assert ext.cell[0] != 0


def test_probe_west_from_one_yields_minus_one_not_zero() -> None:
    mineable = tuple((x, y) for x in (-1, 1) for y in range(0, 2))
    bbox = BBox(min_x=-1, min_y=0, max_x=1, max_y=1)
    barrier = tuple(mineable)
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=mineable,
        full_barrier_cells=barrier,
        belt_cells=mineable,
        asteroid_bbox=bbox,
    )
    ctx = SolverRunContext(run_id="probe_stub", reconstruction=recon)
    events: list[dict[str, object]] = []
    run_pass1_outer_placement(
        ctx, recon, replay_events=events, replay_event_cap=None, trace=TraceCollector(ctx.run_id)
    )
    probes = [
        e
        for e in events
        if e.get("kind") == "probe_output"
        and e.get("extractor_cell") == [1, 0]
        and e.get("output_direction") == [-1, 0]
    ]
    assert probes
    assert probes[0].get("output_stub_cell") == [-1, 0]
