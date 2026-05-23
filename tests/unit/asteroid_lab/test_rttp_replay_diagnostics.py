"""Unit tests for RTTP replay diagnostic payload builders (3B-S-2)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    CandidateGenerationResult,
    CandidateRejectReason,
    RejectedBundleCandidate,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import CommitResult
from django_apps.asteroid_lab.optimization.rttp_replay_diagnostics import (
    build_candidates_replay_payload,
    build_commit_replay_payload,
    build_pipeline_start_replay_payload,
    build_selection_replay_payload,
    overlay_cells_from_coords,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton


def _minimal_skeleton() -> RttpSkeleton:
    return RttpSkeleton(
        ring_cells=frozenset({(0, 0)}),
        ring_ports=(),
        lift_columns=(),
        trunk_mask_cells=frozenset({(1, 0), (2, 0)}),
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
