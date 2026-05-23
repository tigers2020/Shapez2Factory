"""Unit tests for RTTP replay diagnostic payload builders (3B-S-2)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    CandidateGenerationResult,
    CandidateRejectReason,
    RejectedBundleCandidate,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import CommitResult
from django_apps.asteroid_lab.optimization.input_contracts import (
    LiftColumn,
    OptimizationInput,
    RttpSkeletonConfig,
)
from django_apps.asteroid_lab.optimization.rttp_replay_diagnostics import (
    build_candidates_replay_payload,
    build_commit_replay_payload,
    build_pipeline_start_replay_payload,
    build_selection_replay_payload,
    overlay_cells_from_coords,
    skeleton_route_visible_domain,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder


@pytest.fixture
def existing_trunk_optimization_input() -> OptimizationInput:
    from tests.unit.asteroid_lab.test_rttp_existing_trunk import (
        _existing_trunk_optimization_input,
    )

    return _existing_trunk_optimization_input()


def _minimal_skeleton() -> RttpSkeleton:
    return RttpSkeleton(
        ring_cells=frozenset({(0, 0)}),
        ring_ports=(),
        lift_columns=(),
        trunk_mask_cells=frozenset({(0, 1), (1, 0), (2, 0)}),
        capacity_goals=1,
        inner_cells=frozenset({(0, 1)}),
        skeleton_id="sk_test",
    )


def test_overlay_cells_from_coords_emits_wire_shape() -> None:
    cells = overlay_cells_from_coords(
        ((0, 0), (1, 0)),
        kind="candidate.bundle",
        transport="shape_belt",
    )
    assert len(cells) == 2
    assert cells[0]["x"] == 0
    assert cells[0]["kind"] == "candidate.bundle"
    assert cells[0]["transport"] == "shape_belt"


def test_pipeline_start_payload_has_description_and_overlay() -> None:
    payload = build_pipeline_start_replay_payload(_minimal_skeleton())
    assert "sk_test" in payload.description
    assert payload.cell_overlay_json.get("cells")
    assert len(payload.cell_overlay_json["cells"]) >= 1


def test_rttp_pipeline_start_overlay_does_not_draw_trunk_mask_outside_asteroid() -> None:
    skeleton = _minimal_skeleton()
    visible = skeleton_route_visible_domain(skeleton)
    outside_trunk = skeleton.trunk_mask_cells - visible
    assert outside_trunk, "fixture must include trunk mask cells outside ring|inner"

    payload = build_pipeline_start_replay_payload(skeleton)
    overlay_coords = {(c["x"], c["y"]) for c in payload.cell_overlay_json["cells"]}
    assert not (outside_trunk & overlay_coords)
    assert overlay_coords <= {(x, y) for x, y in visible}


def test_rttp_lift_column_overlay_clipped_to_valid_domain() -> None:
    skeleton = RttpSkeleton(
        ring_cells=frozenset({(0, 1)}),
        ring_ports=(),
        lift_columns=(
            LiftColumn(platform_coord=(0, 0), lift_coord=(0, 1), target_lane=0),
            LiftColumn(platform_coord=(50, 50), lift_coord=(50, 51), target_lane=1),
        ),
        trunk_mask_cells=frozenset({(0, 0)}),
        capacity_goals=1,
        inner_cells=frozenset({(0, 0)}),
        skeleton_id="sk_lift_clip",
    )
    visible = skeleton_route_visible_domain(skeleton)

    payload = build_pipeline_start_replay_payload(skeleton)
    probe_coords = {
        (c["x"], c["y"])
        for c in payload.cell_overlay_json["cells"]
        if c["kind"] == "probe.start"
    }
    assert probe_coords == {(0, 0)}
    assert (50, 50) not in probe_coords
    assert all(coord in visible for coord in probe_coords)


def test_rttp_route_domain_snapshot_no_large_void_bbox() -> None:
    skeleton = _minimal_skeleton()
    visible = skeleton_route_visible_domain(skeleton)
    outside_trunk = skeleton.trunk_mask_cells - visible
    payload = build_pipeline_start_replay_payload(skeleton)
    cells = payload.cell_overlay_json["cells"]
    assert cells
    overlay_coords = {(int(c["x"]), int(c["y"])) for c in cells}
    assert overlay_coords <= {(x, y) for x, y in visible}
    assert not (outside_trunk & overlay_coords)
    xs = [int(c["x"]) for c in cells]
    ys = [int(c["y"]) for c in cells]
    vis_xs = [x for x, _ in visible]
    vis_ys = [y for _, y in visible]
    assert min(xs) >= min(vis_xs)
    assert max(xs) <= max(vis_xs)
    assert min(ys) >= min(vis_ys)
    assert max(ys) <= max(vis_ys)


def test_rttp_pipeline_start_overlay_clipped_for_existing_trunk_outside_footprint(
    existing_trunk_optimization_input: OptimizationInput,
) -> None:
    inp = existing_trunk_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    visible = skeleton_route_visible_domain(skeleton)
    outside = skeleton.trunk_mask_cells - visible
    assert outside, "existing trunk must extend outside ring|inner for this regression"

    payload = build_pipeline_start_replay_payload(skeleton)
    overlay_coords = {(c["x"], c["y"]) for c in payload.cell_overlay_json["cells"]}
    assert not (outside & overlay_coords)


def test_rttp_pipeline_start_greenfield_overlay_stays_in_visible_domain(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    skeleton = RttpSkeletonBuilder.build(
        greenfield_optimization_input,
        config=RttpSkeletonConfig(),
    )
    visible = skeleton_route_visible_domain(skeleton)
    payload = build_pipeline_start_replay_payload(skeleton)
    for cell in payload.cell_overlay_json["cells"]:
        assert (cell["x"], cell["y"]) in visible


def test_candidates_payload_summarizes_counts() -> None:
    gen = CandidateGenerationResult(
        normal_candidates=(),
        rejected_candidates=(
            RejectedBundleCandidate(
                candidate_id="rej_1",
                anchor_coord=(3, 3),
                pattern_id="p1",
                rejection_reason=CandidateRejectReason.NOT_REACHABLE,
                route_probe_cost=5,
            ),
        ),
    )
    payload = build_candidates_replay_payload(gen)
    assert "normal_count: 0" in payload.description
    assert "rejected_count: 1" in payload.description
    assert payload.cell_overlay_json["cells"][0]["kind"] == "candidate.rejected"


def test_selection_payload_lists_commit_order_without_candidates() -> None:
    genome = PlacementGenome(commit_order=("cand_001", "cand_002"))
    payload = build_selection_replay_payload(genome, ())
    assert "cand_001" in payload.description
    assert payload.cell_overlay_json.get("cells") == []


def test_commit_payload_reports_validation_and_overlays_routes() -> None:
    commit = CommitResult(
        committed_ids=("cand_001",),
        reserved_route_cells=frozenset({(2, 0), (3, 0)}),
        domain_version=1,
        conflicts=(),
    )
    payload = build_commit_replay_payload(
        commit,
        validation_passed=True,
        normal_count=1,
        commit_order=("cand_001",),
    )
    assert "validation_passed: True" in payload.description
    kinds = {c["kind"] for c in payload.cell_overlay_json.get("cells", [])}
    assert "route.committed_path" in kinds
