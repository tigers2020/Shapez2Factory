"""Pass1 straight extension chain and Pass2 branching geometry."""

from __future__ import annotations

import pytest

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
grow_pass1_straight_extension_chain = _bc.grow_pass1_straight_extension_chain
grow_pass2_branching_extension_cells = _bc.grow_pass2_branching_extension_cells
lex_key_pass1_best_output = _bc.lex_key_pass1_best_output
step_cell = _bc.step_cell


def _straight(
    extractor: tuple[int, int],
    out_dir: tuple[int, int],
    mineable: frozenset[tuple[int, int]],
) -> tuple[tuple[tuple[int, int], tuple[int, int], tuple[int, int]], ...]:
    stub = step_cell(extractor, out_dir)
    used = {extractor, stub}
    recon = ReconstructionDTO()
    return grow_pass1_straight_extension_chain(
        extractor,
        out_dir,
        stub,
        mineable,
        used,
        TransportKind.SHAPE_BELT,
        recon,
    )


@pytest.mark.parametrize(
    ("out_dir", "expected_cells"),
    [
        ((0, -1), ((5, 6), (5, 7), (5, 8))),
        ((1, 0), ((4, 5), (3, 5), (2, 5))),
        ((0, 1), ((5, 4), (5, 3), (5, 2))),
        ((-1, 0), ((6, 5), (7, 5), (8, 5))),
    ],
)
def test_pass1_straight_chain_opposite_output_cardinals(
    out_dir: tuple[int, int],
    expected_cells: tuple[tuple[int, int], ...],
) -> None:
    """N/E/S/W output → collinear chain opposite direction, up to 3 cells."""

    extr = (5, 5)
    stub = step_cell(extr, out_dir)
    mineable = frozenset({extr, stub, *expected_cells})
    exts = _straight(extr, out_dir, mineable)
    got = tuple(c for c, _p, _o in exts)
    assert got == expected_cells
    chain_vec = (-out_dir[0], -out_dir[1])
    prev = extr
    for i, (cell, parent, orient) in enumerate(exts):
        assert parent == prev
        assert orient == _bc.orientation_toward_parent(cell, parent)
        assert (cell[0] - prev[0], cell[1] - prev[1]) == chain_vec
        prev = cell
        if i > 0:
            pcell, _, _ = exts[i - 1]
            assert abs(cell[0] - pcell[0]) + abs(cell[1] - pcell[1]) == 1


def test_grow_pass1_straight_uses_mineable_not_global_x_guard() -> None:
    """Decoded mineable never includes X==0 (STEP1 §6.2.1)."""

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
    exts = grow_pass1_straight_extension_chain(
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


def test_grow_pass1_straight_allows_mineable_when_full_barrier_overlaps_no_belt_carveout() -> None:
    """STEP1: mineable may overlap full_barrier; straight chain still grows."""

    mineable = frozenset({(100, 100), (101, 100), (99, 100), (100, 99), (100, 101)})
    barrier = frozenset(mineable)
    recon = ReconstructionDTO(
        mineable_placement_cells=tuple(sorted(mineable)),
        extraction_shell_cells=tuple(sorted(mineable)),
        full_barrier_cells=tuple(sorted(barrier)),
        belt_cells=(),
        asteroid_bbox=BBox(min_x=99, min_y=99, max_x=101, max_y=101),
        external_margin=3,
        external_margin_bbox_source="mineable",
    )
    extractor = (100, 100)
    out_dir = (0, -1)
    stub = step_cell(extractor, out_dir)
    used = {extractor, stub}
    exts = grow_pass1_straight_extension_chain(
        extractor,
        out_dir,
        stub,
        mineable,
        used,
        TransportKind.SHAPE_BELT,
        recon,
    )
    assert len(exts) >= 1
    assert all(c in mineable for c, _p, _o in exts)


def test_pass1_straight_chain_stops_when_not_mineable() -> None:
    """Chain truncates when the next opposite cell is outside mineable."""

    extr = (5, 5)
    out_dir = (0, -1)
    stub = step_cell(extr, out_dir)
    mineable = frozenset({extr, stub, (5, 6), (5, 7)})
    exts = grow_pass1_straight_extension_chain(
        extr,
        out_dir,
        stub,
        mineable,
        {extr, stub},
        TransportKind.SHAPE_BELT,
        ReconstructionDTO(),
    )
    assert len(exts) == 2
    assert [c for c, _, _ in exts] == [(5, 6), (5, 7)]


def test_pass2_branching_fills_three_side_slots_when_mineable() -> None:
    """Pass2 keeps output-excluded three sides + BFS (not used by Pass1)."""

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
    exts = grow_pass2_branching_extension_cells(
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
