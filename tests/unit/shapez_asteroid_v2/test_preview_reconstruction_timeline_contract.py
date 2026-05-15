"""v2 preview map timeline: mining_map rows must reflect full reconstruction, not shell-only."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2 import (
    preview_reconstruction_timeline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    ReconstructionDTO,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.reconstruction import (
    reconstruct_asteroid_mining_field,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime.trace_collector import (
    TraceCollector,
)

_dominant_surface_for_shell = preview_reconstruction_timeline._dominant_surface_for_shell
build_v2_preview_map_frames = preview_reconstruction_timeline.build_v2_preview_map_frames
expand_pass1_replay_mining_map_frames = (
    preview_reconstruction_timeline.expand_pass1_replay_mining_map_frames
)
PREVIEW_TILE = preview_reconstruction_timeline.PREVIEW_ASTEROID_REPLACE_TILE_T
_apply_mineable_highlights = preview_reconstruction_timeline._apply_mineable_highlights


def _tr() -> TraceCollector:
    return TraceCollector("preview_timeline_contract")


def test_apply_mineable_highlights_promotes_inferred_in_mineable_set() -> None:
    rows = [
        {"x": 3, "y": 3, "role": "inferred", "surface": "shape", "phase": "v2_recon_inner_patch"},
        {"x": 5, "y": 5, "role": "occupied", "surface": "shape", "layout_kind": "asteroid_field"},
    ]
    mineable = frozenset({(3, 3), (5, 5)})
    out = _apply_mineable_highlights(rows, mineable, "v2_recon_mineable", "test_kind")
    by = {(int(r["x"]), int(r["y"])): r for r in out}
    assert by[(3, 3)]["role"] == "mineable"
    assert by[(3, 3)]["layout_kind"] == "asteroid_field"
    assert by[(3, 3)]["surface"] == "shape"
    assert by[(3, 3)]["phase"] == "v2_recon_mineable"
    assert by[(3, 3)]["source_kind"] == "test_kind"
    assert by[(5, 5)]["role"] == "occupied"
    assert by[(5, 5)]["phase"] == "v2_recon_mineable"


def test_apply_mineable_highlights_sets_default_surface_when_missing() -> None:
    rows = [{"x": 1, "y": 2, "role": "inferred", "phase": "x"}]
    out = _apply_mineable_highlights(rows, frozenset({(1, 2)}), "v2_recon_mineable", None)
    r = out[0]
    assert r["role"] == "mineable"
    assert r["surface"] == "shape"


def test_apply_mineable_highlights_leaves_inferred_outside_mineable() -> None:
    rows = [{"x": 9, "y": 9, "role": "inferred", "surface": "shape"}]
    out = _apply_mineable_highlights(rows, frozenset({(1, 1)}), "v2_recon_mineable", None)
    assert out[0]["role"] == "inferred"
    assert out[0].get("layout_kind") is None


def test_v2_recon_mineable_frame_interior_cells_are_mineable_role() -> None:
    entries: list[dict[str, int | str]] = []
    for x in range(2, 7):
        for y in range(2, 7):
            if x in (2, 6) or y in (2, 6):
                entries.append({"X": x, "Y": y, "T": "AsteroidField_Test"})
    entries.append({"X": 7, "Y": 3, "T": "Belt_Straight"})
    entries.append({"X": 4, "Y": 4, "T": "Layout_ShapeMiner"})
    entries.append({"X": 5, "Y": 4, "T": "Layout_ShapeMinerExtension"})
    decoded = {"BP": {"Entries": entries}}
    recon = reconstruct_asteroid_mining_field(decoded)
    frames = build_v2_preview_map_frames(
        decoded, recon, source_kind="mixed_existing_layout", trace=_tr()
    ).frames
    mineable_fr = next(f for f in frames if f["id"] == "v2_recon_mineable")
    interior = set(recon.interior_patch_cells)
    for r in mineable_fr["mining_map"]:
        xy = (int(r["x"]), int(r["y"]))
        if xy in interior:
            assert r.get("role") == "mineable"
            assert r.get("layout_kind") == "asteroid_field"


def test_transport_shell_frame_includes_extractors_without_asteroid_field_tiles() -> None:
    """Regression: shell = AsteroidField* only; island layouts still need visible cells."""

    decoded = {
        "BP": {
            "Entries": [
                {"X": 5, "Y": 5, "T": "Layout_FluidMiner"},
                {"X": 6, "Y": 5, "T": "SpacePipe_Straight"},
            ]
        }
    }
    recon = reconstruct_asteroid_mining_field(decoded)
    assert recon.extraction_shell_cells == ()
    assert recon.extractor_cells and recon.pipe_cells

    frames = build_v2_preview_map_frames(
        decoded, recon, source_kind="existing_fluid_layout", trace=_tr()
    ).frames
    first = next(f for f in frames if f.get("id") == "v2_recon_transport_shell")
    mm = first["mining_map"]
    xs = {int(r["x"]) for r in mm}
    assert 5 in xs and 6 in xs
    roles = {(int(r["x"]), int(r["y"])): r.get("role") for r in mm}
    assert roles.get((5, 5)) == "occupied"
    assert roles.get((6, 5)) == "pipe"


def test_transport_shell_frame_includes_asteroid_shell_when_present() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 2, "Y": 2, "T": "AsteroidField_Test"},
                {"X": 3, "Y": 2, "T": "AsteroidField_Test"},
            ]
        }
    }
    recon = reconstruct_asteroid_mining_field(decoded)
    frames = build_v2_preview_map_frames(
        decoded, recon, source_kind="raw_asteroid_field", trace=_tr()
    ).frames
    first = next(f for f in frames if f.get("id") == "v2_recon_transport_shell")
    assert len(first["mining_map"]) >= 2


def test_expand_pass1_emits_skip_frame_when_no_mineable_cells() -> None:
    recon = ReconstructionDTO(
        full_barrier_cells=((2, 2), (3, 2)),
        extraction_shell_cells=((2, 2), (3, 2)),
        mineable_placement_cells=(),
    )
    mineable_rows = [{"x": 2, "y": 2, "role": "occupied", "surface": "shape"}]
    frames = expand_pass1_replay_mining_map_frames(
        recon,
        mineable_rows,
        dominant="shape",
        source_kind="raw_asteroid_field",
        trace=_tr(),
    ).frames
    assert len(frames) == 1
    assert frames[0]["id"] == "v2_pass1_skipped_no_mineable"
    assert frames[0]["summary"].get("pass1_event_kind") == "skipped_no_mineable"


def test_reconstruction_preview_frame_order_includes_strip_and_inner_patch() -> None:
    entries: list[dict[str, int | str]] = []
    for x in range(2, 7):
        for y in range(2, 7):
            if x in (2, 6) or y in (2, 6):
                entries.append({"X": x, "Y": y, "T": "AsteroidField_Test"})
    entries.append({"X": 7, "Y": 3, "T": "Belt_Straight"})
    entries.append({"X": 4, "Y": 4, "T": "Layout_ShapeMiner"})
    entries.append({"X": 5, "Y": 4, "T": "Layout_ShapeMinerExtension"})
    decoded = {"BP": {"Entries": entries}}
    recon = reconstruct_asteroid_mining_field(decoded)
    frames = build_v2_preview_map_frames(
        decoded, recon, source_kind="mixed_existing_layout", trace=_tr()
    ).frames
    ids = [f.get("id") for f in frames if isinstance(f, dict) and f.get("id")]
    assert ids[:7] == [
        "v2_recon_transport_shell",
        "v2_recon_strip_transport",
        "v2_recon_strip_extractors",
        "v2_recon_strip_extensions",
        "v2_recon_interior_void",
        "v2_recon_inner_patch",
        "v2_recon_mineable",
    ]
    assert ids[7] == "v2_pass1_candidates"
    assert "v2_pass2_candidates" in ids
    shell = next(f for f in frames if f["id"] == "v2_recon_transport_shell")
    stripped = next(f for f in frames if f["id"] == "v2_recon_strip_transport")
    assert len(shell["mining_map"]) > len(stripped["mining_map"])

    strip_ex = next(f for f in frames if f["id"] == "v2_recon_strip_extractors")
    by_xy_ex = {(int(r["x"]), int(r["y"])): r for r in strip_ex["mining_map"]}
    assert by_xy_ex[(4, 4)]["layout_kind"] == "asteroid_field"
    assert by_xy_ex[(4, 4)].get("t") == PREVIEW_TILE

    strip_ext = next(f for f in frames if f["id"] == "v2_recon_strip_extensions")
    by_xy_sx = {(int(r["x"]), int(r["y"])): r for r in strip_ext["mining_map"]}
    assert by_xy_sx[(5, 4)]["layout_kind"] == "asteroid_field"
    assert by_xy_sx[(5, 4)].get("t") == PREVIEW_TILE

    inner = next(f for f in frames if f["id"] == "v2_recon_inner_patch")
    roles = {((int(r["x"]), int(r["y"])), r.get("role")) for r in inner["mining_map"]}
    assert any(role == "inferred" for (_xy, role) in roles)

    inferred_n = sum(1 for r in inner["mining_map"] if r.get("role") == "inferred")
    assert inferred_n == len(recon.interior_patch_cells)

    mineable_fr = next(f for f in frames if f["id"] == "v2_recon_mineable")
    phased = sum(1 for r in mineable_fr["mining_map"] if r.get("phase") == "v2_recon_mineable")
    assert phased == len(recon.mineable_placement_cells)


def test_dominant_surface_includes_fluid_miner_not_on_shell_tiles() -> None:
    """Shell entries are only ``AsteroidField*`` (no surface hint); fluid miner must set default."""

    entries: list[dict[str, int | str]] = []
    for x in range(2, 7):
        for y in range(2, 7):
            if x in (2, 6) or y in (2, 6):
                entries.append({"X": x, "Y": y, "T": "AsteroidField_Test"})
    entries.append({"X": 4, "Y": 4, "T": "Layout_FluidMiner"})
    decoded = {"BP": {"Entries": entries}}
    recon = reconstruct_asteroid_mining_field(decoded)
    assert _dominant_surface_for_shell(decoded, recon) == "fluid"

    _frames = build_v2_preview_map_frames(
        decoded, recon, source_kind="mixed_existing_layout", trace=_tr()
    ).frames
    inner = next(f for f in _frames if f.get("id") == "v2_recon_inner_patch")
    by_xy = {(int(r["x"]), int(r["y"])): r for r in inner["mining_map"]}
    assert by_xy[(2, 4)]["surface"] == "fluid"


def test_strip_extensions_does_not_fill_voids_from_belt_extension_coord_collision() -> None:
    """Belt + extension at same coord: transport removes the cell.

    Extension strip must not paint.
    """

    entries: list[dict[str, int | str]] = []
    for x in range(2, 7):
        for y in range(2, 7):
            if x in (2, 6) or y in (2, 6):
                entries.append({"X": x, "Y": y, "T": "AsteroidField_Test"})
    entries.append({"X": 4, "Y": 4, "T": "Belt_Straight"})
    entries.append({"X": 4, "Y": 4, "T": "Layout_ShapeMinerExtension"})
    decoded = {"BP": {"Entries": entries}}
    recon = reconstruct_asteroid_mining_field(decoded)
    assert (4, 4) in recon.belt_cells
    assert (4, 4) in recon.extension_cells

    frames = build_v2_preview_map_frames(
        decoded, recon, source_kind="mixed_existing_layout", trace=_tr()
    ).frames
    strip_ext = next(f for f in frames if f["id"] == "v2_recon_strip_extensions")
    keys = {(int(r["x"]), int(r["y"])) for r in strip_ext["mining_map"]}
    assert (4, 4) not in keys


def test_strip_asteroid_surface_follows_extractor_or_extension_kind() -> None:
    """Preview-replaced field cells inherit shape vs fluid from the stripped equipment ``T``."""

    entries: list[dict[str, int | str]] = []
    for x in range(2, 7):
        for y in range(2, 7):
            if x in (2, 6) or y in (2, 6):
                entries.append({"X": x, "Y": y, "T": "AsteroidField_Test"})
    entries.append({"X": 4, "Y": 4, "T": "Layout_FluidMiner"})
    entries.append({"X": 5, "Y": 4, "T": "Layout_ShapeMiner"})
    entries.append({"X": 5, "Y": 5, "T": "Layout_FluidMinerExtension"})
    entries.append({"X": 4, "Y": 5, "T": "Layout_ShapeMinerExtension"})
    decoded = {"BP": {"Entries": entries}}
    recon = reconstruct_asteroid_mining_field(decoded)
    frames = build_v2_preview_map_frames(
        decoded, recon, source_kind="mixed_existing_layout", trace=_tr()
    ).frames

    strip_ex = next(f for f in frames if f["id"] == "v2_recon_strip_extractors")
    by_ex = {(int(r["x"]), int(r["y"])): r for r in strip_ex["mining_map"]}
    assert by_ex[(4, 4)].get("surface") == "fluid"
    assert by_ex[(5, 4)].get("surface") == "shape"

    strip_ext = next(f for f in frames if f["id"] == "v2_recon_strip_extensions")
    by_sx = {(int(r["x"]), int(r["y"])): r for r in strip_ext["mining_map"]}
    assert by_sx[(5, 5)].get("surface") == "fluid"
    assert by_sx[(4, 5)].get("surface") == "shape"


def test_pass1_commit_bundle_replay_includes_output_direction() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import BBox
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
        SolverRunContext,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement import (
        pass1_outer as pass1o,
    )

    mineable = tuple((x, y) for x in range(20, 26) for y in range(20, 26) if (x, y) != (22, 22))
    barrier = tuple({*mineable, (22, 22)})
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=mineable,
        full_barrier_cells=barrier,
        asteroid_bbox=BBox(min_x=20, min_y=20, max_x=25, max_y=25),
    )
    ctx = SolverRunContext(run_id="preview_contract", reconstruction=recon)
    events: list[dict[str, object]] = []
    pass1o.run_pass1_outer_placement(
        ctx, recon, replay_events=events, replay_event_cap=None, trace=TraceCollector(ctx.run_id)
    )
    commits = [e for e in events if e.get("kind") == "commit_bundle"]
    assert commits
    c0 = commits[0]
    assert "output_direction" in c0
    assert isinstance(c0["output_direction"], list) and len(c0["output_direction"]) == 2
    assert c0.get("output_stub_physical") is True
    assert "output_stub_cell" in c0


def test_pass1_preview_no_pass1_stub_role_extractor_has_layout_kind_and_r() -> None:
    """Committed/provisional Pass1 frames: extractor body only; no pass1_stub_* overlay."""

    entries: list[dict[str, int | str]] = []
    for x in range(2, 7):
        for y in range(2, 7):
            if x in (2, 6) or y in (2, 6):
                entries.append({"X": x, "Y": y, "T": "AsteroidField_Test"})
    entries.append({"X": 7, "Y": 3, "T": "Belt_Straight"})
    entries.append({"X": 4, "Y": 4, "T": "Layout_ShapeMiner"})
    entries.append({"X": 5, "Y": 4, "T": "Layout_ShapeMinerExtension"})
    decoded = {"BP": {"Entries": entries}}
    recon = reconstruct_asteroid_mining_field(decoded)
    mineable_f = frozenset(recon.mineable_placement_cells)
    result = build_v2_preview_map_frames(
        decoded, recon, source_kind="mixed_existing_layout", trace=_tr()
    )
    matched = False
    for fr in result.frames:
        summ = fr.get("summary") or {}
        ek = summ.get("pass1_event_kind")
        if ek not in ("commit_bundle", "pass1_provisional_final"):
            continue
        matched = True
        mm = fr.get("mining_map") or []
        for row in mm:
            pr = row.get("pass1_replay_role")
            if pr is not None:
                assert not str(pr).startswith("pass1_stub_")
            if pr is not None and str(pr).startswith("pass1_extractor_"):
                assert row.get("layout_kind") in ("miner", "fluid_miner")
                assert "r" in row
                xy = (int(row["x"]), int(row["y"]))
                assert xy in mineable_f
    assert matched, "expected Pass1 commit or provisional preview frame"


def test_pass1_probe_output_stub_highlight_only() -> None:
    """probe_output may paint stub cell; committed overlay does not use pass1_stub_*."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2 import (
        preview_reconstruction_timeline as pv,
    )

    mineable_rows = [
        {"x": 10, "y": 10, "role": "occupied", "surface": "shape", "layout_kind": "asteroid_field"},
        {"x": 11, "y": 10, "role": "inferred", "surface": "shape"},
    ]
    committed = [
        {
            "extractor_cell": [10, 10],
            "output_stub_cell": [11, 10],
            "extension_cells": [],
            "transport_kind": "shape_belt",
            "output_direction": [1, 0],
        }
    ]
    rows_committed = pv._mining_map_with_pass1_replay_overlay(
        mineable_rows,
        frame_id="f_commit",
        source_kind=None,
        dominant="shape",
        committed_bundles=committed,
        highlight_event=None,
    )
    by_c = {(int(r["x"]), int(r["y"])): r for r in rows_committed}
    assert by_c[(10, 10)].get("layout_kind") == "miner"
    assert by_c[(10, 10)].get("r") == 0
    assert by_c[(11, 10)].get("pass1_replay_role") is None

    rows_probe = pv._mining_map_with_pass1_replay_overlay(
        mineable_rows,
        frame_id="f_probe",
        source_kind=None,
        dominant="shape",
        committed_bundles=[],
        highlight_event={
            "kind": "probe_output",
            "output_stub_cell": [11, 10],
            "reject_reason": None,
        },
    )
    by_p = {(int(r["x"]), int(r["y"])): r for r in rows_probe}
    assert by_p[(11, 10)].get("pass1_replay_role") == "pass1_probe_stub_ok"


def test_pass1_replay_committed_paints_output_stub_belt_before_extensions() -> None:
    """Committed overlay paints belt on output stub (no prior belt row) before extensions."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2 import (
        preview_reconstruction_timeline as pv,
    )

    mineable_rows = [
        {"x": 9, "y": 10, "role": "occupied", "surface": "shape", "layout_kind": "asteroid_field"},
        {"x": 10, "y": 10, "role": "occupied", "surface": "shape", "layout_kind": "asteroid_field"},
        {"x": 11, "y": 10, "role": "inferred", "surface": "shape"},
    ]
    committed = [
        {
            "extractor_cell": [10, 10],
            "output_stub_cell": [11, 10],
            "extension_cells": [[9, 10]],
            "transport_kind": "shape_belt",
            "output_direction": [1, 0],
        }
    ]
    rows = pv._mining_map_with_pass1_replay_overlay(
        mineable_rows,
        frame_id="f_stub_belt",
        source_kind=None,
        dominant="shape",
        committed_bundles=committed,
        highlight_event=None,
    )
    by_c = {(int(r["x"]), int(r["y"])): r for r in rows}
    stub = by_c[(11, 10)]
    assert stub.get("role") == "belt"
    assert stub.get("r") == 0
    assert stub.get("pass1_replay_role") is None
    assert by_c[(9, 10)].get("layout_kind") == "extension"


def test_pass1_replay_committed_paints_output_stub_pipe_before_extensions() -> None:
    """Same for fluid pipe transport on the output stub."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2 import (
        preview_reconstruction_timeline as pv,
    )

    mineable_rows = [
        {"x": 10, "y": 9, "role": "occupied", "surface": "fluid", "layout_kind": "asteroid_field"},
        {"x": 10, "y": 10, "role": "occupied", "surface": "fluid", "layout_kind": "asteroid_field"},
        {"x": 11, "y": 10, "role": "inferred", "surface": "fluid"},
    ]
    committed = [
        {
            "extractor_cell": [10, 10],
            "output_stub_cell": [11, 10],
            "extension_cells": [[10, 9]],
            "transport_kind": "fluid_pipe",
            "output_direction": [1, 0],
        }
    ]
    rows = pv._mining_map_with_pass1_replay_overlay(
        mineable_rows,
        frame_id="f_stub_pipe",
        source_kind=None,
        dominant="fluid",
        committed_bundles=committed,
        highlight_event=None,
    )
    by_c = {(int(r["x"]), int(r["y"])): r for r in rows}
    stub = by_c[(11, 10)]
    assert stub.get("role") == "pipe"
    assert stub.get("surface") == "fluid"
    assert stub.get("r") == 0
    assert stub.get("pass1_replay_role") is None
    assert by_c[(10, 9)].get("layout_kind") == "fluid_extension"


def test_pass1_replay_extension_overlay_extension_tile_metadata() -> None:
    """Committed extension_cells get extension layout_kind / t / r; stub stays unbadged."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2 import (
        preview_reconstruction_timeline as pv,
    )

    mineable_rows = [
        {"x": 9, "y": 10, "role": "occupied", "surface": "shape", "layout_kind": "asteroid_field"},
        {"x": 10, "y": 10, "role": "occupied", "surface": "shape", "layout_kind": "asteroid_field"},
        {"x": 11, "y": 10, "role": "belt", "surface": "shape"},
    ]
    committed_shape = [
        {
            "extractor_cell": [10, 10],
            "output_stub_cell": [11, 10],
            "extension_cells": [[9, 10]],
            "transport_kind": "shape_belt",
            "output_direction": [1, 0],
        }
    ]
    rows_shape = pv._mining_map_with_pass1_replay_overlay(
        mineable_rows,
        frame_id="f_shape",
        source_kind=None,
        dominant="shape",
        committed_bundles=committed_shape,
        highlight_event=None,
    )
    by_s = {(int(r["x"]), int(r["y"])): r for r in rows_shape}
    ext_shape = by_s[(9, 10)]
    assert ext_shape.get("pass1_replay_role") == "pass1_extension_0_0"
    assert ext_shape.get("layout_kind") == "extension"
    assert ext_shape.get("t") == "Layout_ShapeMinerExtension"
    assert ext_shape.get("surface") == "shape"
    assert ext_shape.get("r") == 0
    assert by_s[(10, 10)].get("layout_kind") == "miner"
    assert by_s[(11, 10)].get("pass1_replay_role") is None

    mineable_fluid = [
        {"x": 10, "y": 9, "role": "occupied", "surface": "fluid", "layout_kind": "asteroid_field"},
        {"x": 10, "y": 10, "role": "occupied", "surface": "fluid", "layout_kind": "asteroid_field"},
        {"x": 11, "y": 10, "role": "pipe", "surface": "fluid"},
    ]
    committed_fluid = [
        {
            "extractor_cell": [10, 10],
            "output_stub_cell": [11, 10],
            "extension_cells": [[10, 9]],
            "transport_kind": "fluid_pipe",
            "output_direction": [1, 0],
        }
    ]
    rows_fluid = pv._mining_map_with_pass1_replay_overlay(
        mineable_fluid,
        frame_id="f_fluid",
        source_kind=None,
        dominant="fluid",
        committed_bundles=committed_fluid,
        highlight_event=None,
    )
    by_f = {(int(r["x"]), int(r["y"])): r for r in rows_fluid}
    ext_fluid = by_f[(10, 9)]
    assert ext_fluid.get("pass1_replay_role") == "pass1_extension_0_0"
    assert ext_fluid.get("layout_kind") == "fluid_extension"
    assert ext_fluid.get("t") == "Layout_FluidMinerExtension"
    assert ext_fluid.get("surface") == "fluid"
    assert ext_fluid.get("r") == 1
    assert by_f[(10, 10)].get("layout_kind") == "fluid_miner"


def test_pass1_extension_orientation_dirs_branching_from_extractor() -> None:
    """Two first-hop extensions share extractor parent; each ``r`` faces that parent."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2 import (
        preview_reconstruction_timeline as pv,
    )

    extr = (10, 10)
    dirs = pv._pass1_extension_orientation_dirs(extr, [[10, 11], [9, 10]])
    assert dirs == ((0, -1), (1, 0))


def test_pass1_extension_orientation_dirs_chain() -> None:
    """Second extension attaches to first; both orient toward their immediate parent."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2 import (
        preview_reconstruction_timeline as pv,
    )

    dirs = pv._pass1_extension_orientation_dirs((10, 10), [[9, 10], [8, 10]])
    assert dirs == ((1, 0), (1, 0))


def test_pass1_replay_branching_extensions_independent_r() -> None:
    """Sibling extensions under one extractor get distinct parent-facing rotations."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2 import (
        preview_reconstruction_timeline as pv,
    )

    mineable_rows = [
        {"x": 9, "y": 10, "role": "occupied", "surface": "shape", "layout_kind": "asteroid_field"},
        {"x": 10, "y": 10, "role": "occupied", "surface": "shape", "layout_kind": "asteroid_field"},
        {"x": 10, "y": 11, "role": "occupied", "surface": "shape", "layout_kind": "asteroid_field"},
        {"x": 11, "y": 10, "role": "belt", "surface": "shape"},
    ]
    committed = [
        {
            "extractor_cell": [10, 10],
            "output_stub_cell": [11, 10],
            "extension_cells": [[10, 11], [9, 10]],
            "transport_kind": "shape_belt",
            "output_direction": [1, 0],
        }
    ]
    rows = pv._mining_map_with_pass1_replay_overlay(
        mineable_rows,
        frame_id="f_branch",
        source_kind=None,
        dominant="shape",
        committed_bundles=committed,
        highlight_event=None,
    )
    by_c = {(int(r["x"]), int(r["y"])): r for r in rows}
    south = by_c[(10, 11)]
    west = by_c[(9, 10)]
    assert south.get("pass1_replay_role") == "pass1_extension_0_0"
    assert west.get("pass1_replay_role") == "pass1_extension_0_1"
    assert south.get("layout_kind") == "extension"
    assert west.get("layout_kind") == "extension"
    assert south.get("r") == 3
    assert west.get("r") == 0
    assert by_c[(11, 10)].get("pass1_replay_role") is None


def test_pass1_replay_extension_transport_kind_defaults_shape() -> None:
    """Missing ``transport_kind`` in replay bundle JSON defaults to shape belt semantics."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2 import (
        preview_reconstruction_timeline as pv,
    )

    mineable_rows = [
        {"x": 9, "y": 10, "role": "occupied", "surface": "shape", "layout_kind": "asteroid_field"},
        {"x": 10, "y": 10, "role": "occupied", "surface": "shape", "layout_kind": "asteroid_field"},
        {"x": 11, "y": 10, "role": "belt", "surface": "shape"},
    ]
    committed = [
        {
            "extractor_cell": [10, 10],
            "output_stub_cell": [11, 10],
            "extension_cells": [[9, 10]],
            "output_direction": [1, 0],
        }
    ]
    rows = pv._mining_map_with_pass1_replay_overlay(
        mineable_rows,
        frame_id="f_no_tk",
        source_kind=None,
        dominant="shape",
        committed_bundles=committed,
        highlight_event=None,
    )
    ext = {(int(r["x"]), int(r["y"])): r for r in rows}[(9, 10)]
    assert ext.get("layout_kind") == "extension"
    assert ext.get("t") == "Layout_ShapeMinerExtension"
    assert ext.get("surface") == "shape"


def test_pass1_occupied_cells_still_includes_stub() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import BBox
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
        SolverRunContext,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement import (
        pass1_outer as pass1o,
    )

    mineable = tuple((x, y) for x in range(20, 26) for y in range(20, 26) if (x, y) != (22, 22))
    barrier = tuple({*mineable, (22, 22)})
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=mineable,
        full_barrier_cells=barrier,
        asteroid_bbox=BBox(min_x=20, min_y=20, max_x=25, max_y=25),
    )
    ctx = SolverRunContext(run_id="occ_stub", reconstruction=recon)
    p1 = pass1o.run_pass1_outer_placement(ctx, recon, trace=TraceCollector(ctx.run_id))
    if not p1.placements:
        return
    stub = p1.placements[0].output_stub.cell
    assert stub in frozenset(p1.occupied_cells)
    assert stub in frozenset(p1.output_stub_cells)
    assert stub not in frozenset(p1.placement_occupied_cells)
