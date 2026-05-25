"""Terrain rim highlight DTO — replay/UI artifact only."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.optimization.reconstruction_adapter import _rim_cells
from django_apps.asteroid_lab.reconstruction.complete_map import build_reconstruction_complete_map
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.reconstruction.rim_highlight import (
    build_terrain_rim_highlight,
    build_terrain_rim_highlight_from_renderable_cells,
    canonicalize_void_edges,
    terrain_rim_highlight_to_metrics_dict,
)
from django_apps.asteroid_lab.reconstruction.rim_topology import field_rim_cells
from django_apps.asteroid_lab.reconstruction.topology_contract import (
    decode_shapez_copy_string,
    load_reconstruction_fixture_line_pairs,
)
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame


def _canon_complete_map():
    required_copy, _solved = load_reconstruction_fixture_line_pairs()[1]
    snap = decode_shapez_copy_string(required_copy)
    cleanup = deconstruct_snapshot(snap)
    recon = run_topology_reconstruction(cleanup)
    return build_reconstruction_complete_map(cleanup=cleanup, recon=recon)


def test_field_rim_cells_matches_adapter_rim_parity() -> None:
    complete = _canon_complete_map()
    expected = _rim_cells(complete.field_cells)
    assert field_rim_cells(complete.field_cells) == expected


def test_build_terrain_rim_highlight_rim_subset_of_field() -> None:
    complete = _canon_complete_map()
    dto = build_terrain_rim_highlight(complete)
    rim_set = frozenset(dto.rim_cells)
    assert rim_set <= complete.field_cells
    assert dto.version == 1
    assert dto.coord_frame == CoordFrame.ISLAND_RAW


def test_void_edge_cells_subset_of_rim_and_edges_canonical() -> None:
    complete = _canon_complete_map()
    dto = build_terrain_rim_highlight(complete)
    rim_set = frozenset(dto.rim_cells)
    for entry in dto.void_edge_cells:
        assert (entry.x, entry.y) in rim_set
        assert entry.edges == canonicalize_void_edges(entry.edges)
        for ch in entry.edges:
            assert ch in "nesw"


def test_canonicalize_void_edges_rejects_unknown_char() -> None:
    with pytest.raises(ValueError, match="unknown"):
        canonicalize_void_edges("nx")


def test_canonicalize_void_edges_orders_nesw() -> None:
    assert canonicalize_void_edges("wn") == "nw"


def test_metrics_dict_wire_shape() -> None:
    complete = _canon_complete_map()
    dto = build_terrain_rim_highlight(complete)
    wire = terrain_rim_highlight_to_metrics_dict(dto)
    assert wire["version"] == 1
    assert "rim_cells" in wire
    assert "void_edge_cells" in wire
    assert "outer_outline_loops" in wire
    assert wire["coord_frame"] == CoordFrame.ISLAND_RAW.value


def test_outer_outline_loop_is_closed_polygon() -> None:
    complete = _canon_complete_map()
    dto = build_terrain_rim_highlight(complete)
    assert dto.outer_outline_loops
    primary = dto.outer_outline_loops[0]
    assert len(primary) >= 4
    assert primary[0] == primary[-1]


def test_partial_factory_delegates_same_as_complete() -> None:
    complete = _canon_complete_map()
    from_renderable = build_terrain_rim_highlight_from_renderable_cells(
        field_cells=complete.field_cells,
        external_void_cells=complete.external_void_cells,
        coord_frame=complete.coord_frame,
    )
    from_complete = build_terrain_rim_highlight(complete)
    assert from_renderable == from_complete
