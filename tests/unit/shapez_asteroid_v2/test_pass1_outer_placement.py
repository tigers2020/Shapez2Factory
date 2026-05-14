"""STEP 2 Pass1 outer-first placement contracts (§7, ``06_step2_pass1_placement.md``)."""

from __future__ import annotations

from pathlib import Path

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2 import (
    preview_reconstruction_timeline as _pv_timeline,
)
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
    _inward_chain_direction_from_bbox,
    _preferred_pass1_output_direction,
    pass1_mineable_outer_first_order,
    run_pass1_outer_placement,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement.placement_fsm import (
    assert_all_provisional_commits,
    assert_no_routed_confirmed,
)

expand_pass1_replay_mining_map_frames = _pv_timeline.expand_pass1_replay_mining_map_frames

CARDINAL_DIRS = _bc.CARDINAL_DIRS
grow_pass1_straight_extension_chain = _bc.grow_pass1_straight_extension_chain
grow_pass2_branching_extension_cells = _bc.grow_pass2_branching_extension_cells
side_directions_after_output = _bc.side_directions_after_output
step_cell = _bc.step_cell

_REPO_ROOT = Path(__file__).resolve().parents[3]
_PASS1_PATH = (
    _REPO_ROOT
    / "django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/pass1_outer.py"
)
_PASS1_SRC = _PASS1_PATH.read_text(encoding="utf-8")


def _ctx(run_id: str = "t_pass1") -> SolverRunContext:
    return SolverRunContext(run_id=run_id, reconstruction=ReconstructionDTO())


def _small_mineable_recon() -> ReconstructionDTO:
    mineable = tuple((x, y) for x in range(20, 26) for y in range(20, 26) if (x, y) != (22, 22))
    barrier = tuple({*mineable, (22, 22)})
    return ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=mineable,
        full_barrier_cells=barrier,
        asteroid_bbox=BBox(min_x=20, min_y=20, max_x=25, max_y=25),
        external_margin=3,
        external_margin_bbox_source="mineable",
    )


def test_pass1_outer_non_empty_extensions_when_barrier_overlaps_mineable() -> None:
    """STEP1 overlap: mineable ⊆ full_barrier without belt_cells masking blocked_by_building."""

    recon = _small_mineable_recon()
    p1 = run_pass1_outer_placement(_ctx("t_p1_barrier_overlap"), recon)
    assert p1.placements
    assert max(len(b.extensions) for b in p1.placements) >= 1


def test_pass1_each_bundle_has_one_output_stub_adjacent_to_extractor() -> None:
    recon = _small_mineable_recon()
    p1 = run_pass1_outer_placement(_ctx(), recon)
    for b in p1.placements:
        stub = b.output_stub.cell
        ext = b.extractor.cell
        assert stub in {step_cell(ext, d) for d in CARDINAL_DIRS}
        assert b.output_stub.transport_kind is b.extractor.transport_kind


def test_side_directions_exclude_output_only() -> None:
    for out in CARDINAL_DIRS:
        sides = side_directions_after_output(out)
        assert len(sides) == 3
        assert out not in sides
        assert set(sides) | {out} == set(CARDINAL_DIRS)


def test_extensions_at_most_three_orient_toward_parent() -> None:
    recon = _small_mineable_recon()
    p1 = run_pass1_outer_placement(_ctx(), recon)
    for b in p1.placements:
        assert len(b.extensions) <= 3
        for ext in b.extensions:
            v = (
                ext.parent_cell[0] - ext.cell[0],
                ext.parent_cell[1] - ext.cell[1],
            )
            assert v == ext.orientation_toward_parent
            assert v in CARDINAL_DIRS


def test_bbox_inward_prefers_chain_into_deposit_west_rim() -> None:
    """Nearest bbox face west → straight chain east; output stub west of extractor."""

    bbox = BBox(min_x=20, min_y=20, max_x=25, max_y=25)
    ext = (21, 22)
    assert _inward_chain_direction_from_bbox(ext, bbox) == (1, 0)
    assert _preferred_pass1_output_direction(ext, bbox) == (-1, 0)


def test_bbox_inward_prefers_chain_into_deposit_south_rim() -> None:
    bbox = BBox(min_x=20, min_y=20, max_x=25, max_y=25)
    ext = (22, 24)
    assert _inward_chain_direction_from_bbox(ext, bbox) == (0, -1)
    assert _preferred_pass1_output_direction(ext, bbox) == (0, 1)


def test_pass1_straight_chain_vertical_south_from_extractor() -> None:
    """Pass1: output north → straight chain south only (no ㅗ/ㅓ/ㅏ branching)."""

    mineable = frozenset((11, y) for y in range(100, 106))
    recon = ReconstructionDTO(
        mineable_placement_cells=tuple(sorted(mineable)),
        extraction_shell_cells=tuple(sorted(mineable)),
        full_barrier_cells=(),
        asteroid_bbox=BBox(min_x=11, min_y=100, max_x=11, max_y=105),
        external_margin=3,
        external_margin_bbox_source="mineable",
    )
    extractor = (11, 102)
    out_dir = (0, -1)
    stub = step_cell(extractor, out_dir)
    used: set[tuple[int, int]] = {extractor, stub}
    exts = grow_pass1_straight_extension_chain(
        extractor,
        out_dir,
        stub,
        mineable,
        used,
        TransportKind.SHAPE_BELT,
        recon,
    )
    assert len(exts) == 3
    assert [c for c, _, _ in exts] == [(11, 103), (11, 104), (11, 105)]
    parents = [p for c, p, _o in exts]
    assert parents == [extractor, (11, 103), (11, 104)]


def test_pass2_branching_chain_geometry_still_supported() -> None:
    """Pass2 helper: side slots + BFS (not used for Pass1 outer)."""

    mineable = frozenset((11, y) for y in range(100, 105))
    recon = ReconstructionDTO(
        mineable_placement_cells=tuple(sorted(mineable)),
        extraction_shell_cells=tuple(sorted(mineable)),
        full_barrier_cells=(),
        asteroid_bbox=BBox(min_x=11, min_y=100, max_x=11, max_y=104),
        external_margin=3,
        external_margin_bbox_source="mineable",
    )
    extractor = (11, 102)
    out_dir = (0, -1)
    stub = step_cell(extractor, out_dir)
    used: set[tuple[int, int]] = {extractor, stub}
    exts = grow_pass2_branching_extension_cells(
        extractor,
        out_dir,
        stub,
        mineable,
        used,
        TransportKind.SHAPE_BELT,
        recon,
    )
    assert len(exts) >= 2
    parents = {p for _c, p, _o in exts}
    assert extractor in parents
    assert len(parents) >= 2


def test_occupied_cells_match_exact_union_of_bundle_cells() -> None:
    recon = _small_mineable_recon()
    p1 = run_pass1_outer_placement(_ctx(), recon)
    union: set[tuple[int, int]] = set()
    placement_only: set[tuple[int, int]] = set()
    stubs: set[tuple[int, int]] = set()
    for b in p1.placements:
        union |= {b.extractor.cell, b.output_stub.cell} | {e.cell for e in b.extensions}
        placement_only |= {b.extractor.cell} | {e.cell for e in b.extensions}
        stubs.add(b.output_stub.cell)
    assert set(p1.occupied_cells) == union
    assert set(p1.placement_occupied_cells) == placement_only
    assert set(p1.output_stub_cells) == stubs
    assert not (placement_only & stubs)


def test_pass1_no_final_route_cells_field() -> None:
    p1 = run_pass1_outer_placement(_ctx(), _small_mineable_recon())
    assert getattr(p1, "final_route_cells", ()) == ()


def test_provisional_only_no_routed_confirmed() -> None:
    p1 = run_pass1_outer_placement(_ctx(), _small_mineable_recon())
    if p1.placement_commit_entries:
        assert_all_provisional_commits(p1.placement_commit_entries)
        assert_no_routed_confirmed(p1.placement_commit_entries)


def test_deterministic_scan_order_repeatable() -> None:
    recon = _small_mineable_recon()
    m = frozenset(recon.mineable_placement_cells)
    bb = recon.asteroid_bbox
    assert bb is not None
    a = pass1_mineable_outer_first_order(m, bb)
    b = pass1_mineable_outer_first_order(m, bb)
    assert a == b


def test_transport_kind_pipe_when_only_pipe_cells() -> None:
    mineable = ((30, 30), (30, 31), (31, 30), (31, 31))
    barrier = mineable
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=mineable,
        full_barrier_cells=barrier,
        pipe_cells=((30, 30),),
        belt_cells=(),
        asteroid_bbox=BBox(min_x=30, min_y=30, max_x=31, max_y=31),
        external_margin=3,
        external_margin_bbox_source="mineable",
    )
    p1 = run_pass1_outer_placement(_ctx("pipe_only"), recon)
    for b in p1.placements:
        assert b.extractor.transport_kind is TransportKind.FLUID_PIPE


def test_pass1_source_does_not_import_merge_aware_router() -> None:
    assert "merge_aware_router" not in _PASS1_SRC


def test_expand_pass1_replay_emits_many_frames_and_canonical_ids() -> None:
    recon = _small_mineable_recon()
    p1 = run_pass1_outer_placement(_ctx(), recon)
    mineable_rows = [
        {"x": x, "y": y, "role": "occupied", "surface": "shape", "phase": "v2_recon_mineable"}
        for x, y in sorted(recon.mineable_placement_cells, key=lambda c: (c[1], c[0]))
    ]
    frames = expand_pass1_replay_mining_map_frames(
        recon,
        mineable_rows,
        dominant="shape",
        source_kind="raw_asteroid_field",
    ).frames
    ids = [str(f["id"]) for f in frames]
    assert "v2_pass1_candidates" in ids
    if p1.placements:
        assert "v2_pass1_provisional" in ids
    assert len(frames) >= 2
    for fr in frames:
        summ = fr.get("summary")
        assert isinstance(summ, dict)
        assert summ.get("pass1_replay") is True
