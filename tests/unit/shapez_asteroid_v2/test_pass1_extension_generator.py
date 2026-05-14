"""Pass1 extension geometry: ``grow_extension_cells`` and lexicographic output choice."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import BBox
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    ReconstructionDTO,
    SolverRunContext,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    TransportKind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement import (
    bundle_candidate as _bc,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement.pass1_outer import (
    run_pass1_outer_placement,
)

CARDINAL_DIRS = _bc.CARDINAL_DIRS
grow_extension_cells = _bc.grow_extension_cells
lex_key_pass1_best_output = _bc.lex_key_pass1_best_output
side_directions_after_output = _bc.side_directions_after_output
step_cell = _bc.step_cell


def test_grow_extension_cells_uses_mineable_not_global_x_guard() -> None:
    """Validity is mineable + barriers only; decoded mineable never includes X==0 (STEP1 §6.2.1)."""

    mineable = frozenset({(1, 10), (2, 10), (3, 10), (2, 9), (2, 11)})
    recon = ReconstructionDTO(
        mineable_placement_cells=tuple(sorted(mineable)),
        extraction_shell_cells=tuple(sorted(mineable)),
        full_barrier_cells=(),
        asteroid_bbox=BBox(min_x=1, min_y=9, max_x=3, max_y=11),
        external_margin=3,
        external_margin_bbox_source="mineable",
    )
    extractor = (2, 10)
    out_dir = (0, -1)
    stub = step_cell(extractor, out_dir)
    used = {extractor, stub}
    exts = grow_extension_cells(
        extractor,
        out_dir,
        stub,
        mineable,
        used,
        TransportKind.SHAPE_BELT,
        recon,
    )
    assert len(exts) >= 1
    ext_cells = {c for c, _p, _o in exts}
    assert ext_cells <= mineable


def test_grow_extension_cells_fills_three_side_slots_when_mineable() -> None:
    """Output north: E/S/W extractor-adjacent cells mineable → three extensions."""

    mineable = frozenset(
        {
            (5, 5),
            (6, 5),
            (4, 5),
            (5, 6),
            (5, 4),
        }
    )
    recon = ReconstructionDTO(
        mineable_placement_cells=tuple(sorted(mineable)),
        extraction_shell_cells=tuple(sorted(mineable)),
        full_barrier_cells=(),
        asteroid_bbox=BBox(min_x=4, min_y=4, max_x=6, max_y=6),
        external_margin=3,
        external_margin_bbox_source="mineable",
    )
    extractor = (5, 5)
    out_dir = (0, -1)
    stub = step_cell(extractor, out_dir)
    used = {extractor, stub}
    exts = grow_extension_cells(
        extractor,
        out_dir,
        stub,
        mineable,
        used,
        TransportKind.SHAPE_BELT,
        recon,
    )
    assert len(exts) == 3
    ext_cells = {c for c, _p, _o in exts}
    assert ext_cells == {(6, 5), (5, 6), (4, 5)}
    sides = side_directions_after_output(out_dir)
    assert len(sides) == 3


def test_lex_key_pass1_prefers_more_extensions_then_outer_then_cardinal_order() -> None:
    bbox = BBox(min_x=0, min_y=0, max_x=10, max_y=10)
    ext = (5, 5)
    assert lex_key_pass1_best_output(ext, bbox, 2, CARDINAL_DIRS[0]) < lex_key_pass1_best_output(
        ext, bbox, 1, CARDINAL_DIRS[3]
    )
    assert lex_key_pass1_best_output(ext, bbox, 1, CARDINAL_DIRS[0]) == lex_key_pass1_best_output(
        ext, bbox, 1, CARDINAL_DIRS[0]
    )
    outer = (0, 5)
    inner = (5, 5)
    assert lex_key_pass1_best_output(outer, bbox, 1, (1, 0)) < lex_key_pass1_best_output(
        inner, bbox, 1, (1, 0)
    )
    assert lex_key_pass1_best_output(ext, bbox, 1, (0, -1)) < lex_key_pass1_best_output(
        ext, bbox, 1, (-1, 0)
    )


def test_run_pass1_commits_non_empty_extensions_on_open_grid() -> None:
    mineable = tuple((x, y) for x in range(20, 26) for y in range(20, 26) if (x, y) != (22, 22))
    barrier = tuple({*mineable, (22, 22)})
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=mineable,
        full_barrier_cells=barrier,
        belt_cells=mineable,
        asteroid_bbox=BBox(min_x=20, min_y=20, max_x=25, max_y=25),
        external_margin=3,
        external_margin_bbox_source="mineable",
    )
    ctx = SolverRunContext(run_id="ext_open", reconstruction=recon)
    p1 = run_pass1_outer_placement(ctx, recon)
    assert p1.placements
    assert max(len(b.extensions) for b in p1.placements) >= 1


def test_cheap_escape_probe_cells_not_in_pass1_placement_occupied() -> None:
    mineable = tuple((x, y) for x in range(20, 26) for y in range(20, 26) if (x, y) != (22, 22))
    barrier = tuple({*mineable, (22, 22)})
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=mineable,
        full_barrier_cells=barrier,
        belt_cells=mineable,
        asteroid_bbox=BBox(min_x=20, min_y=20, max_x=25, max_y=25),
        external_margin=3,
        external_margin_bbox_source="mineable",
    )
    ctx = SolverRunContext(run_id="cheap_not_occ", reconstruction=recon)
    p1 = run_pass1_outer_placement(ctx, recon)
    po = frozenset(p1.placement_occupied_cells)
    for b in p1.placements:
        assert b.extractor.cell in po
        for ext in b.extensions:
            assert ext.cell in po
        assert b.output_stub.cell not in po
