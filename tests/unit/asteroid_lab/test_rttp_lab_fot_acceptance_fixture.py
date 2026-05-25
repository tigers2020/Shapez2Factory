"""Lab-equivalent acceptance: reconstruction fixture — no extractor on peer FOT (PR1.5)."""

from __future__ import annotations

from dataclasses import replace

from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
)
from django_apps.asteroid_lab.optimization.candidates.placement_cells import (
    fixed_output_transport_cell,
)
from django_apps.asteroid_lab.optimization.input_contracts import RttpSkeletonConfig
from django_apps.asteroid_lab.optimization.materialization.placement_overlay_projection import (
    build_confirmed_placement_overlay_rows,
)
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_reconstruction,
)
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.reconstruction.topology_contract import (
    decode_shapez_copy_string,
    load_reconstruction_fixture_line_pairs,
)
from tests.support.catalog_test_fixtures import build_minimal_test_catalog_slice

# Fixture line 2: maps that previously committed W miners at (-1,-10) / (-2,-10).
_FIXTURE_LINE_INDEX = 2
_LAB_COORDS = frozenset({(-1, -10), (-2, -10), (-1, -9), (-2, -9)})


def _inp_from_fixture_line(line_index: int):
    required_copy, _ = load_reconstruction_fixture_line_pairs()[line_index]
    snap = decode_shapez_copy_string(required_copy)
    cleanup = deconstruct_snapshot(snap)
    recon = run_topology_reconstruction(cleanup)
    inp = optimization_input_from_reconstruction(recon, cleanup=cleanup)
    if inp.catalog_slice is None:
        inp = replace(inp, catalog_slice=build_minimal_test_catalog_slice())
    return inp


def test_fixture_line2_no_extractor_occupies_peer_fot() -> None:
    """Committed layout must satisfy INV-COMMIT-FOT on real reconstruction map."""
    inp = _inp_from_fixture_line(_FIXTURE_LINE_INDEX)
    result = run_rttp_pipeline(inp, policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM)
    committed = result.commit_result.committed_ids
    assert committed, "expected at least one commit"

    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    by_id = {c.candidate_id: c for c in generation.normal_candidates}

    for a_id in committed:
        for b_id in committed:
            if a_id == b_id:
                continue
            a = by_id[a_id]
            b = by_id[b_id]
            assert fixed_output_transport_cell(a) not in b.occupied_cells, (
                f"{b_id} extractor on {b.occupied_cells} blocks FOT of {a_id} at "
                f"{fixed_output_transport_cell(a)}"
            )
            assert fixed_output_transport_cell(b) not in a.occupied_cells, (
                f"{a_id} extractor on {a.occupied_cells} blocks FOT of {b_id} at "
                f"{fixed_output_transport_cell(b)}"
            )


def test_fixture_line2_lab_region_overlay_when_n_miner_committed() -> None:
    """If N@(-1,-9) commits, (-1,-10) overlay must be FOT not extractor (Lab hover)."""
    inp = _inp_from_fixture_line(_FIXTURE_LINE_INDEX)
    result = run_rttp_pipeline(inp, policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM)
    committed = result.commit_result.committed_ids
    assert committed

    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    by_id = {c.candidate_id: c for c in generation.normal_candidates}

    n_at_lab = tuple(
        cid
        for cid in committed
        if (c := by_id.get(cid)) is not None
        and c.anchor_coord == (-1, -9)
        and c.output_dir == "N"
    )
    if not n_at_lab:
        return

    rows, _ = build_confirmed_placement_overlay_rows(
        committed_ids=committed,
        candidates_by_id=by_id,
        reserved_route_cells=result.commit_result.reserved_route_cells,
        field_kind_by_coord=None,
    )
    fot_coord = (-1, -10)
    fot_rows = [r for r in rows if (int(r["x"]), int(r["y"])) == fot_coord]
    assert fot_rows, f"expected overlay at {fot_coord}"
    assert any("fixed_output_transport" in str(r.get("overlay_semantic_kind", "")) for r in fot_rows)
    assert not any(
        str(r.get("overlay_semantic_kind", "")) == "placement.confirmed_extractor"
        for r in fot_rows
    )
