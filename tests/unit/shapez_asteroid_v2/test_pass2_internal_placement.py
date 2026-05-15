"""STEP 3 Pass2 internal fill: blocked set, no route geometry, provisional commits only."""

from __future__ import annotations

from pathlib import Path

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import BBox
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    Pass1Result,
    Pass2Result,
    ReconstructionDTO,
    SolverRunContext,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    TransportKind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.orchestration import (
    RoutingStateSnapshot,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement import (
    build_pass2_blocked_set,
    run_pass1_outer_placement,
    run_pass2_internal_fill,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement.placement_fsm import (
    assert_all_provisional_commits,
    assert_no_routed_confirmed,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime.trace_collector import (
    TraceCollector,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_pass2_module_does_not_reference_final_route_cells() -> None:
    root = _repo_root()
    for rel in (
        "django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/pass2_internal.py",
        "django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/pass2_bundle_optimizer.py",
    ):
        src = root / rel
        text = src.read_text(encoding="utf-8")
        assert "final_route_cells" not in text
        assert "asteroid_mining_layout_v2.routing" not in text


def test_build_pass2_blocked_set_unions_pass1_geometry_barriers() -> None:
    p1 = Pass1Result(
        placement_occupied_cells=((20, 21), (20, 22)),
        output_stub_cells=((20, 20),),
        occupied_cells=((20, 20), (20, 21), (20, 22)),
    )
    recon = ReconstructionDTO(
        mineable_placement_cells=((20, 20), (20, 21), (20, 22), (21, 21)),
        full_barrier_cells=((99, 99), (20, 20), (20, 21), (20, 22)),
    )
    blocked = build_pass2_blocked_set(p1, recon)
    assert (20, 21) in blocked
    assert (20, 22) in blocked
    assert (20, 20) in blocked
    assert (99, 99) in blocked


def test_pass2_never_overlaps_pass1_extractor_extension_or_stub() -> None:
    mineable = tuple((x, y) for x in range(20, 26) for y in range(20, 26) if (x, y) != (22, 22))
    bbox = BBox(min_x=20, min_y=20, max_x=25, max_y=25)
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
    barrier = tuple({*mineable, (22, 22)})
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=shell,
        full_barrier_cells=barrier,
        belt_cells=mineable,
        asteroid_bbox=bbox,
    )
    ctx = SolverRunContext(run_id="p2_overlap", reconstruction=recon)
    p1 = run_pass1_outer_placement(ctx, recon, trace=TraceCollector(ctx.run_id))
    p1_occ = frozenset(p1.occupied_cells)
    p2 = run_pass2_internal_fill(ctx, p1, trace=TraceCollector(ctx.run_id))
    for b in p2.provisional_placements:
        cells = {b.extractor.cell, b.output_stub.cell, *(e.cell for e in b.extensions)}
        assert not (cells & p1_occ)


def test_pass2_extractors_lie_outside_blocked_set() -> None:
    """Extractors must come from ``mineable \\ build_pass2_blocked_set`` (§8.2)."""

    mineable = tuple((x, y) for x in range(30, 36) for y in range(30, 36) if (x, y) != (32, 32))
    bbox = BBox(min_x=30, min_y=30, max_x=35, max_y=35)
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
    barrier = tuple({*mineable, (32, 32)})
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=shell,
        full_barrier_cells=barrier,
        belt_cells=mineable,
        asteroid_bbox=bbox,
    )
    ctx = SolverRunContext(run_id="p2_blocked", reconstruction=recon)
    p1 = run_pass1_outer_placement(ctx, recon, trace=TraceCollector(ctx.run_id))
    p2 = run_pass2_internal_fill(ctx, p1, trace=TraceCollector(ctx.run_id))
    blocked = build_pass2_blocked_set(p1, recon)
    for b in p2.provisional_placements:
        assert b.extractor.cell not in blocked
        assert b.extractor.cell in mineable


def test_pass2_provisional_only_no_routed_confirmed() -> None:
    mineable = tuple((x, y) for x in range(60, 66) for y in range(60, 66) if (x, y) != (62, 62))
    bbox = BBox(min_x=60, min_y=60, max_x=65, max_y=65)
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
    barrier = tuple({*mineable, (62, 62)})
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=shell,
        full_barrier_cells=barrier,
        belt_cells=mineable,
        asteroid_bbox=bbox,
    )
    ctx = SolverRunContext(run_id="p2_fsm", reconstruction=recon)
    p1 = run_pass1_outer_placement(ctx, recon, trace=TraceCollector(ctx.run_id))
    p2 = run_pass2_internal_fill(ctx, p1, trace=TraceCollector(ctx.run_id))
    if p2.placement_commit_entries:
        assert_all_provisional_commits(p2.placement_commit_entries)
        assert_no_routed_confirmed(p2.placement_commit_entries)


def test_pass2_deterministic_for_identical_inputs() -> None:
    mineable = tuple((x, y) for x in range(70, 76) for y in range(70, 76) if (x, y) != (72, 72))
    bbox = BBox(min_x=70, min_y=70, max_x=75, max_y=75)
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
    barrier = tuple({*mineable, (72, 72)})
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=shell,
        full_barrier_cells=barrier,
        belt_cells=mineable,
        asteroid_bbox=bbox,
    )
    ctx = SolverRunContext(run_id="det", reconstruction=recon)
    p1 = run_pass1_outer_placement(ctx, recon, trace=TraceCollector(ctx.run_id))
    a = run_pass2_internal_fill(ctx, p1, trace=TraceCollector(ctx.run_id))
    b = run_pass2_internal_fill(ctx, p1, trace=TraceCollector(ctx.run_id))
    assert a == b


def test_pass2_ignores_routing_state_final_route_cell_noise() -> None:
    mineable = tuple((x, y) for x in range(80, 86) for y in range(80, 86) if (x, y) != (82, 82))
    bbox = BBox(min_x=80, min_y=80, max_x=85, max_y=85)
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
    barrier = tuple({*mineable, (82, 82)})
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=shell,
        full_barrier_cells=barrier,
        belt_cells=mineable,
        asteroid_bbox=bbox,
    )
    noise = RoutingStateSnapshot(final_route_cells=((1, 1), (2, 2), (3, 3)))
    ctx_plain = SolverRunContext(run_id="noise", reconstruction=recon)
    ctx_noisy = SolverRunContext(run_id="noise", reconstruction=recon, routing_state=noise)
    p1 = run_pass1_outer_placement(ctx_plain, recon, trace=TraceCollector(ctx_plain.run_id))
    assert run_pass2_internal_fill(
        ctx_plain, p1, trace=TraceCollector(ctx_plain.run_id)
    ) == run_pass2_internal_fill(ctx_noisy, p1, trace=TraceCollector(ctx_noisy.run_id))


def test_pass2_transport_kind_pipe_when_only_pipe_cells() -> None:
    mineable = tuple(
        (x, y) for x in range(130, 136) for y in range(130, 136) if (x, y) != (132, 132)
    )
    bbox = BBox(min_x=130, min_y=130, max_x=135, max_y=135)
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
    barrier = tuple({*mineable, (132, 132)})
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=shell,
        full_barrier_cells=barrier,
        belt_cells=(),
        pipe_cells=mineable,
        asteroid_bbox=bbox,
    )
    ctx = SolverRunContext(run_id="pipe_only", reconstruction=recon)
    p1 = run_pass1_outer_placement(ctx, recon, trace=TraceCollector(ctx.run_id))
    p2 = run_pass2_internal_fill(ctx, p1, trace=TraceCollector(ctx.run_id))
    for b in p2.provisional_placements:
        assert b.extractor.transport_kind is TransportKind.FLUID_PIPE
        assert b.output_stub.transport_kind is TransportKind.FLUID_PIPE


def test_pass2_transport_kind_belt_when_belt_cells_present() -> None:
    mineable = tuple(
        (x, y) for x in range(140, 146) for y in range(140, 146) if (x, y) != (142, 142)
    )
    bbox = BBox(min_x=140, min_y=140, max_x=145, max_y=145)
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
    barrier = tuple({*mineable, (142, 142)})
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=shell,
        full_barrier_cells=barrier,
        belt_cells=mineable,
        pipe_cells=((999, 999),),
        asteroid_bbox=bbox,
    )
    ctx = SolverRunContext(run_id="belt_pref", reconstruction=recon)
    p1 = run_pass1_outer_placement(ctx, recon, trace=TraceCollector(ctx.run_id))
    p2 = run_pass2_internal_fill(ctx, p1, trace=TraceCollector(ctx.run_id))
    for b in p2.provisional_placements:
        assert b.extractor.transport_kind is TransportKind.SHAPE_BELT


def test_pass2_internal_module_has_no_escape_bfs_state() -> None:
    """Cheap escape BFS is only in ``pass1_outer``; Pass2 does not keep probe fringe."""

    src = (
        _repo_root()
        / "django_apps"
        / "shapez_asteroid"
        / "services"
        / "asteroid_mining_layout_v2"
        / "placement"
        / "pass2_internal.py"
    )
    text = src.read_text(encoding="utf-8")
    assert "deque" not in text
    assert "seen" not in text


def test_pass2_empty_when_no_remaining_mineable() -> None:
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
    ctx = SolverRunContext(run_id="full", reconstruction=recon)
    p2 = run_pass2_internal_fill(ctx, p1, trace=TraceCollector(ctx.run_id))
    assert p2 == Pass2Result()
