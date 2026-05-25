"""Placement overlay projection — Lab wire rows from BundleCandidate (PR-1)."""

from __future__ import annotations

from django_apps.asteroid_lab.contracts.catalog_placement import (
    CardinalDirection,
    CatalogPlacementRef,
)
from django_apps.asteroid_lab.optimization.candidates.bundle_pattern import BundlePattern
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.candidates.pattern_library import build_pattern_library
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.optimization.materialization.placement_overlay_projection import (
    build_candidate_placement_overlay_rows,
    build_confirmed_placement_overlay_rows,
    build_selected_placement_overlay_rows,
    merge_overlay_rows_by_priority,
    resolve_placement_transport_kind,
)


def _pattern(pattern_id: str) -> BundlePattern:
    for row in build_pattern_library():
        if row.pattern_id == pattern_id:
            return row
    raise AssertionError(pattern_id)


def _translate(anchor: tuple[int, int], offset: tuple[int, int]) -> tuple[int, int]:
    return (anchor[0] + offset[0], anchor[1] + offset[1])


def _candidate(
    anchor: tuple[int, int] = (5, 5),
    *,
    pattern_id: str = "lin_e_len1",
) -> BundleCandidate:
    pattern = _pattern(pattern_id)
    occupied = frozenset(_translate(anchor, o) for o in pattern.occupied_offsets)
    output_stub = _translate(anchor, pattern.output_stub_offset)
    return BundleCandidate(
        candidate_id=f"{anchor[0]},{anchor[1]}:{pattern.pattern_id}:shape_belt",
        anchor_coord=anchor,
        pattern=pattern,
        occupied_cells=occupied,
        output_stub=output_stub,
        output_dir=pattern.output_dir,
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=pattern.throughput_factor,
        route_probe_cost=3,
        reachable=True,
        catalog_placement_ref=CatalogPlacementRef(
            canonical_id="ExtractorDefaultInternalVariant",
            anchor_coord=anchor,
            rotation=CardinalDirection.E,
        ),
    )


def test_confirmed_rows_use_miner_cell_kind_and_none_transport() -> None:
    cand = _candidate()
    rows, diag = build_confirmed_placement_overlay_rows(
        committed_ids=(cand.candidate_id,),
        candidates_by_id={cand.candidate_id: cand},
        reserved_route_cells=frozenset({(7, 5), (8, 5)}),
    )
    miners = [r for r in rows if r.get("cell_kind") == "shape_miner"]
    assert len(miners) == 1
    assert miners[0]["transport_kind"] == "none"
    assert miners[0]["transport"] == ""
    assert miners[0]["tile_type"] == "Layout_ShapeMiner"
    assert miners[0]["overlay_semantic_kind"] == "placement.confirmed_extractor"
    assert miners[0].get("commit_state") == "confirmed"
    assert diag.visible_miner_cell_count == 1
    assert diag.visible_extension_cell_count == 1


def test_candidate_rows_omit_commit_state() -> None:
    cand = _candidate()
    rows = build_candidate_placement_overlay_rows((cand,))
    assert all("commit_state" not in r for r in rows)
    assert any(r["overlay_semantic_kind"] == "placement.candidate_extractor" for r in rows)


def test_selected_rows_omit_commit_state() -> None:
    cand = _candidate()
    rows = build_selected_placement_overlay_rows((cand.candidate_id,), {cand.candidate_id: cand})
    assert all("commit_state" not in r for r in rows)
    assert all(
        r.get("transport_kind") == "none"
        for r in rows
        if r["cell_kind"] in ("shape_miner", "shape_miner_extension")
    )


def test_merge_prefers_placement_over_route() -> None:
    placement = [
        {
            "x": 1,
            "y": 0,
            "kind": "placement.confirmed_extractor",
            "cell_kind": "shape_miner",
        }
    ]
    route = [
        {
            "x": 1,
            "y": 0,
            "kind": "route.committed_path",
            "cell_kind": "space_belt",
        }
    ]
    merged = merge_overlay_rows_by_priority(placement + route)
    assert len(merged) == 1
    assert merged[0]["cell_kind"] == "shape_miner"


def test_overlap_emits_metrics_json_fields() -> None:
    cand = _candidate(anchor=(5, 5))
    overlap_coord = next(iter(cand.occupied_cells))
    _rows, diag = build_confirmed_placement_overlay_rows(
        committed_ids=(cand.candidate_id,),
        candidates_by_id={cand.candidate_id: cand},
        reserved_route_cells=frozenset({overlap_coord}),
    )
    assert diag.placement_route_overlap_warning_count >= 1
    assert overlap_coord in diag.placement_route_overlap_warning_coords


def test_route_rows_keep_legacy_kind_route_committed_path() -> None:
    cand = _candidate(anchor=(4, 4))
    rows, _diag = build_confirmed_placement_overlay_rows(
        committed_ids=(cand.candidate_id,),
        candidates_by_id={cand.candidate_id: cand},
        reserved_route_cells=frozenset({(8, 4), (9, 4)}),
    )
    route_rows = [r for r in rows if r.get("kind") == "route.committed_path"]
    assert route_rows
    assert route_rows[0]["cell_kind"] == "space_belt"
    assert route_rows[0]["transport_kind"] == "shape_belt"
    assert route_rows[0]["transport"] == "shape_belt"


def test_confirmed_includes_extension_overlay_cells() -> None:
    cand = _candidate(pattern_id="lin_e_len2")
    rows, _diag = build_confirmed_placement_overlay_rows(
        committed_ids=(cand.candidate_id,),
        candidates_by_id={cand.candidate_id: cand},
        reserved_route_cells=frozenset(),
    )
    assert any(r.get("cell_kind") == "shape_miner_extension" for r in rows)


def test_resolve_placement_transport_kind_prefers_fluid_field_at_anchor() -> None:
    cand = _candidate(anchor=(2, -10))
    resolved = resolve_placement_transport_kind(
        cand,
        {(2, -10): "asteroid_fluid_field"},
    )
    assert resolved is TransportKind.FLUID_PIPE


def test_confirmed_overlay_uses_fluid_miner_on_fluid_field() -> None:
    cand = _candidate(anchor=(2, -10))
    rows, _diag = build_confirmed_placement_overlay_rows(
        committed_ids=(cand.candidate_id,),
        candidates_by_id={cand.candidate_id: cand},
        reserved_route_cells=frozenset(),
        field_kind_by_coord={(2, -10): "asteroid_fluid_field"},
    )
    miners = [r for r in rows if r.get("cell_kind") == "fluid_miner"]
    assert len(miners) == 1
    assert miners[0]["tile_type"] == "Layout_FluidMiner"
    assert miners[0]["x"] == 2
    assert miners[0]["y"] == -10
