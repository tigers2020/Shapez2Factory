"""Geometry validation tests (Solver Runtime PR2)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from django_apps.asteroid_lab.optimization.candidate_geometry import (
    validate_projected_gene_geometry,
)
from django_apps.asteroid_lab.optimization.enums import CandidateRejectReason, Direction
from django_apps.asteroid_lab.optimization.gene_projection import project_gene_placement
from django_apps.asteroid_lab.optimization.gene_template_loader import load_gene_templates_from_json
from django_apps.asteroid_lab.optimization.input_contracts import greenfield_optimization_input
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_reconstruction,
)
from django_apps.asteroid_lab.reconstruction.pipeline import reconstruct_snapshot
from django_apps.asteroid_lab.services.dto import DecodedBlueprintSnapshotDTO, DecodedCellDTO

_FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "asteroid_lab" / "gene_templates"


def _minimal_gene():
    return load_gene_templates_from_json(_FIXTURE_DIR / "minimal_extractor_e.json")[0]


def _cell(x: int, y: int, **kwargs: str) -> DecodedCellDTO:
    defaults = {
        "tile_type": "",
        "cell_kind": "unknown",
        "transport_kind": "none",
    }
    defaults.update(kwargs)
    return DecodedCellDTO(
        x=x,
        y=y,
        layer=None,
        rotation=0,
        tile_type=defaults["tile_type"],
        cell_kind=defaults["cell_kind"],
        transport_kind=defaults["transport_kind"],
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={},
        server_x=None,
        server_y=None,
    )


def _hole_inp():
    cells = (
        _cell(1, 0, cell_kind="fluid_miner"),
        _cell(2, 0, cell_kind="space_pipe", transport_kind="fluid_pipe"),
        _cell(3, 0, cell_kind="fluid_miner_extension", transport_kind="fluid_pipe"),
        _cell(1, 1, tile_type="UnknownTile_A"),
        _cell(2, 1, cell_kind="fluid_miner"),
        _cell(3, 1, tile_type="UnknownTile_C"),
        _cell(1, 2, tile_type="UnknownTile_D"),
        _cell(3, 2, tile_type="UnknownTile_E"),
        _cell(1, 3, tile_type="UnknownTile_F"),
        _cell(2, 3, tile_type="UnknownTile_G"),
        _cell(3, 3, tile_type="UnknownTile_H"),
    )
    xs = [c.x for c in cells]
    ys = [c.y for c in cells]
    snap = DecodedBlueprintSnapshotDTO(
        project_id=None,
        map_input_id=None,
        binary_version=3,
        blueprint_type="Island",
        entry_count=len(cells),
        bbox_json={
            "min_x": min(xs),
            "max_x": max(xs),
            "min_y": min(ys),
            "max_y": max(ys),
            "width": max(xs) - min(xs) + 1,
            "height": max(ys) - min(ys) + 1,
        },
        cell_kind_counts_json={},
        transport_kind_counts_json={},
        cells=cells,
        summary_json={},
    )
    return optimization_input_from_reconstruction(reconstruct_snapshot(snap))


def _grid_inp_with_interior():
    from django_apps.asteroid_lab.optimization.input_contracts import BBox

    mineable = frozenset((cx, cy) for cx in range(2, 5) for cy in range(2, 5))
    rim = frozenset([(2, 2), (4, 2), (2, 4), (4, 4)])
    interior = mineable - rim
    return replace(
        greenfield_optimization_input(bbox=BBox(1, 5, 1, 5)),
        asteroid_cells=mineable,
        mineable_cells=mineable,
        rim_cells=rim,
        interior_cells=interior,
    )


def test_geometry_accepts_valid_projected_gene() -> None:
    inp = _grid_inp_with_interior()
    rim = (2, 2)
    assert rim in inp.rim_cells
    gene = _minimal_gene()
    projected = project_gene_placement(anchor=rim, rotation=Direction.E, gene=gene)
    result = validate_projected_gene_geometry(inp, projected)
    assert result.valid is True
    assert result.reject_reason is None


def test_geometry_rejects_extractor_not_rim() -> None:
    inp = _grid_inp_with_interior()
    interior = (3, 3)
    assert interior in inp.interior_cells
    gene = _minimal_gene()
    projected = project_gene_placement(anchor=interior, rotation=Direction.E, gene=gene)
    result = validate_projected_gene_geometry(inp, projected)
    assert result.valid is False
    assert result.reject_reason == CandidateRejectReason.EXTRACTOR_NOT_RIM


def test_geometry_rejects_extension_not_mineable() -> None:
    inp = _hole_inp()
    gene = load_gene_templates_from_json(_FIXTURE_DIR / "ext1_w.json")[0]
    rim = next(iter(inp.rim_cells))
    projected = project_gene_placement(anchor=rim, rotation=Direction.E, gene=gene)
    # Force an extension coord outside mineable
    bad_ext = (99, 99)
    projected = replace(
        projected,
        extensions=projected.extensions + (bad_ext,),
        occupied_cells=frozenset(projected.occupied_cells | {bad_ext}),
    )
    result = validate_projected_gene_geometry(inp, projected)
    assert result.valid is False
    assert result.reject_reason == CandidateRejectReason.EXTENSION_NOT_MINEABLE


def test_geometry_rejects_occupied_outside_asteroid() -> None:
    inp = _hole_inp()
    gene = _minimal_gene()
    rim = next(iter(inp.rim_cells))
    projected = project_gene_placement(anchor=rim, rotation=Direction.E, gene=gene)
    outside = next(iter(inp.external_void_cells))
    projected = replace(
        projected,
        occupied_cells=frozenset(projected.occupied_cells | {outside}),
    )
    result = validate_projected_gene_geometry(inp, projected)
    assert result.valid is False
    assert result.reject_reason == CandidateRejectReason.OCCUPIED_OUTSIDE_ASTEROID


def test_geometry_rejects_route_probe_start_inside_occupied() -> None:
    inp = _hole_inp()
    gene = _minimal_gene()
    rim = next(iter(inp.rim_cells))
    projected = project_gene_placement(anchor=rim, rotation=Direction.E, gene=gene)
    projected = replace(projected, route_probe_start=projected.extractor)
    result = validate_projected_gene_geometry(inp, projected)
    assert result.valid is False
    assert result.reject_reason == CandidateRejectReason.OUTPUT_STUB_INSIDE_OCCUPIED


def test_geometry_rejects_route_probe_start_invalid_coord() -> None:
    inp = _hole_inp()
    gene = _minimal_gene()
    rim = next(iter(inp.rim_cells))
    projected = project_gene_placement(anchor=rim, rotation=Direction.E, gene=gene)
    projected = replace(projected, route_probe_start=(inp.bbox.max_sx + 10, inp.bbox.max_sy + 10))
    result = validate_projected_gene_geometry(inp, projected)
    assert result.valid is False
    assert result.reject_reason == CandidateRejectReason.OUTPUT_STUB_INVALID_COORD


def test_geometry_does_not_mutate_optimization_input() -> None:
    inp = _hole_inp()
    before = inp
    gene = _minimal_gene()
    rim = next(iter(inp.rim_cells))
    projected = project_gene_placement(anchor=rim, rotation=Direction.E, gene=gene)
    validate_projected_gene_geometry(inp, projected)
    validate_projected_gene_geometry(inp, projected)
    assert inp == before
