"""MEG unit tests — target, pass predicate, evidence builder, aggregator (spec §10)."""

from __future__ import annotations

from django_apps.asteroid_lab.contracts.rttp_optimization_goal import (
    MINING_EQUIPMENT_GOAL_SHORTFALL_ISSUE_CODE,
    RttpRunStatus,
)
from django_apps.asteroid_lab.optimization.candidates.bundle_pattern import BundlePattern
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.commit.incremental_commit import CommitResult
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.services.mining_equipment_goal import (
    ExteriorPassEvidence,
    MiningEquipmentGoalResult,
    aggregate_mining_equipment_goal_result,
    build_exterior_pass_evidence_for_committed_bundles,
    compute_target_mining_equipment_cells,
    has_confirmed_exterior_pass,
    mining_equipment_cells,
    optimization_goal_passed,
    optimization_goal_to_json,
    resolve_run_status,
)
from django_apps.asteroid_lab.services.placement_goal import compute_placement_goal_count


def test_target_mining_equipment_cells_583_at_80_percent_is_467() -> None:
    assert (
        compute_target_mining_equipment_cells(
            mineable_cell_count=583,
            placement_target_percent=80,
        )
        == 467
    )


def test_placement_goal_count_alias_matches_meg_target() -> None:
    assert compute_placement_goal_count(
        asteroid_field_cell_count=583,
        placement_target_percent=80,
    ) == compute_target_mining_equipment_cells(
        mineable_cell_count=583,
        placement_target_percent=80,
    )


def _bundle_candidate(
    *,
    anchor: tuple[int, int],
    extension_offsets: tuple[tuple[int, int], ...],
) -> BundleCandidate:
    extractor = (0, 0)
    occupied = frozenset({extractor, *extension_offsets})
    pattern = BundlePattern(
        pattern_id="test_lin",
        extension_count=len(extension_offsets),
        occupied_offsets=occupied,
        extractor_offset=extractor,
        extension_offsets=extension_offsets,
        output_dir="east",
        fixed_output_transport_offset=(1, 0),
        output_stub_offset=(1, 0),
        throughput_factor=1,
        topology_kind="linear",
    )
    stub = (anchor[0] + 1, anchor[1])
    return BundleCandidate(
        candidate_id=f"{anchor[0]},{anchor[1]}:test_lin:shape_belt",
        anchor_coord=anchor,
        pattern=pattern,
        occupied_cells=frozenset((anchor[0] + c[0], anchor[1] + c[1]) for c in occupied),
        output_stub=stub,
        output_dir="east",
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=1,
        route_probe_cost=1,
        reachable=True,
        catalog_placement_ref=None,
    )


def _evidence(**kwargs: object) -> ExteriorPassEvidence:
    base: dict[str, object] = {
        "candidate_id": "c1",
        "transport_kind": TransportKind.SHAPE_BELT,
        "output_stub_reserved": True,
        "reached_elcp_lane_id": None,
        "reached_external_margin": False,
        "shareable_trunk_overlap_only": True,
        "lane_capacity_ok": True,
    }
    base.update(kwargs)
    return ExteriorPassEvidence(**base)  # type: ignore[arg-type]


def test_has_confirmed_exterior_pass_elcp_active_requires_lane() -> None:
    assert has_confirmed_exterior_pass(
        _evidence(reached_elcp_lane_id="lane-a", lane_capacity_ok=True),
        elcp_plan_active=True,
    )
    assert not has_confirmed_exterior_pass(
        _evidence(reached_external_margin=True, reached_elcp_lane_id=None),
        elcp_plan_active=True,
    )


def test_has_confirmed_exterior_pass_legacy_margin_when_elcp_inactive() -> None:
    assert has_confirmed_exterior_pass(
        _evidence(reached_external_margin=True),
        elcp_plan_active=False,
    )


def test_has_confirmed_exterior_pass_rejects_missing_stub_or_private_overlap() -> None:
    assert not has_confirmed_exterior_pass(
        _evidence(output_stub_reserved=False),
        elcp_plan_active=False,
    )
    assert not has_confirmed_exterior_pass(
        _evidence(shareable_trunk_overlap_only=False),
        elcp_plan_active=False,
    )


def test_builder_marks_legacy_elcp_fallback_ineligible_for_elcp_pass() -> None:
    candidate = _bundle_candidate(anchor=(0, 0), extension_offsets=())
    by_id = {candidate.candidate_id: candidate}
    commit = CommitResult(
        committed_ids=(candidate.candidate_id,),
        reserved_route_cells=frozenset({candidate.output_stub}),
        domain_version=1,
        conflicts=(),
        exterior_lane_assignments=(
            {
                "candidate_id": candidate.candidate_id,
                "exterior_lane_id": "lane-1",
                "legacy_elcp_fallback": True,
                "reached_goal": [],
            },
        ),
    )
    rows = build_exterior_pass_evidence_for_committed_bundles(
        commit_result=commit,
        candidates_by_id=by_id,
        inp_transport_kind=TransportKind.SHAPE_BELT,
        elcp_plan_active=True,
        exterior_lane_plan_present=True,
    )
    assert len(rows) == 1
    assert rows[0].reached_elcp_lane_id is None
    assert rows[0].output_stub_reserved is True
    assert not has_confirmed_exterior_pass(rows[0], elcp_plan_active=True)


def test_builder_elcp_active_qualifies_with_lane_and_reached_goal() -> None:
    candidate = _bundle_candidate(anchor=(5, 5), extension_offsets=((1, 0), (2, 0)))
    by_id = {candidate.candidate_id: candidate}
    commit = CommitResult(
        committed_ids=(candidate.candidate_id,),
        reserved_route_cells=frozenset({candidate.output_stub}),
        domain_version=1,
        conflicts=(),
        exterior_lane_assignments=(
            {
                "candidate_id": candidate.candidate_id,
                "exterior_lane_id": "lane-east",
                "reached_goal": [10, 5],
            },
        ),
    )
    rows = build_exterior_pass_evidence_for_committed_bundles(
        commit_result=commit,
        candidates_by_id=by_id,
        inp_transport_kind=TransportKind.SHAPE_BELT,
        elcp_plan_active=True,
        exterior_lane_plan_present=True,
    )
    assert has_confirmed_exterior_pass(rows[0], elcp_plan_active=True)


def test_aggregate_counts_pass_qualified_cells_not_route_cells() -> None:
    ext = ((1, 0), (2, 0))
    candidate = _bundle_candidate(anchor=(5, 5), extension_offsets=ext)
    mineable = frozenset(candidate.occupied_cells)
    evidence = ExteriorPassEvidence(
        candidate_id=candidate.candidate_id,
        transport_kind=TransportKind.SHAPE_BELT,
        output_stub_reserved=True,
        reached_elcp_lane_id="lane-1",
        reached_external_margin=True,
        shareable_trunk_overlap_only=True,
        lane_capacity_ok=True,
    )
    result = aggregate_mining_equipment_goal_result(
        evidence_rows=(evidence,),
        candidates_by_id={candidate.candidate_id: candidate},
        mineable_cells=mineable,
        target_mining_equipment_cells=467,
        elcp_plan_active=True,
        committed_ids=(candidate.candidate_id,),
        reserved_route_cells=frozenset({(99, 99), (100, 100)}),
    )
    assert result.confirmed_passed_mining_equipment_cells == 3
    assert result.confirmed_committed_bundle_count == 1
    assert result.confirmed_transport_route_cell_count == 2
    assert result.shortfall == 464


def test_aggregate_bundle_count_vs_equipment_cells_t7() -> None:
    candidate = _bundle_candidate(
        anchor=(0, 0),
        extension_offsets=((1, 0), (2, 0), (3, 0)),
    )
    mineable = frozenset(candidate.occupied_cells)
    evidence = ExteriorPassEvidence(
        candidate_id=candidate.candidate_id,
        transport_kind=TransportKind.SHAPE_BELT,
        output_stub_reserved=True,
        reached_elcp_lane_id="lane-1",
        reached_external_margin=True,
        shareable_trunk_overlap_only=True,
        lane_capacity_ok=True,
    )
    result = aggregate_mining_equipment_goal_result(
        evidence_rows=(evidence,),
        candidates_by_id={candidate.candidate_id: candidate},
        mineable_cells=mineable,
        target_mining_equipment_cells=10,
        elcp_plan_active=True,
        committed_ids=(candidate.candidate_id,),
    )
    assert result.confirmed_committed_bundle_count == 1
    assert result.confirmed_passed_mining_equipment_cells == 4


def test_aggregate_committed_without_pass_contributes_zero_equipment_cells() -> None:
    candidate = _bundle_candidate(anchor=(1, 1), extension_offsets=((1, 0),))
    mineable = frozenset(candidate.occupied_cells)
    fail_evidence = ExteriorPassEvidence(
        candidate_id=candidate.candidate_id,
        transport_kind=TransportKind.SHAPE_BELT,
        output_stub_reserved=True,
        reached_elcp_lane_id=None,
        reached_external_margin=False,
        shareable_trunk_overlap_only=True,
        lane_capacity_ok=False,
    )
    result = aggregate_mining_equipment_goal_result(
        evidence_rows=(fail_evidence,),
        candidates_by_id={candidate.candidate_id: candidate},
        mineable_cells=mineable,
        target_mining_equipment_cells=467,
        elcp_plan_active=True,
        committed_ids=(candidate.candidate_id,),
        reserved_route_cells=frozenset({(50, 50)}),
    )
    assert result.confirmed_committed_bundle_count == 1
    assert result.confirmed_passed_mining_equipment_cells == 0
    assert result.confirmed_transport_route_cell_count == 1


def test_optimization_goal_to_json_shortfall_not_in_layout_codes_contract() -> None:
    result = MiningEquipmentGoalResult(
        target_mining_equipment_cells=467,
        confirmed_passed_mining_equipment_cells=25,
        confirmed_committed_bundle_count=25,
        shortfall=442,
    )
    block = optimization_goal_to_json(result)
    assert optimization_goal_passed(result) is False
    assert block["issue_code"] == MINING_EQUIPMENT_GOAL_SHORTFALL_ISSUE_CODE
    assert block["shortfall"] == 442


def test_resolve_run_status_partial_when_structural_pass_goal_fail() -> None:
    goal = optimization_goal_to_json(
        MiningEquipmentGoalResult(
            target_mining_equipment_cells=467,
            confirmed_passed_mining_equipment_cells=25,
            confirmed_committed_bundle_count=25,
            shortfall=442,
        )
    )
    assert (
        resolve_run_status(
            structural_validation_passed=True,
            optimization_goal=goal,
        )
        == RttpRunStatus.PARTIAL_SUCCESS
    )


def test_mining_equipment_cells_one_extractor_three_extensions() -> None:
    anchor = (10, 20)
    extensions = ((1, 0), (2, 0), (3, 0))
    candidate = _bundle_candidate(anchor=anchor, extension_offsets=extensions)
    mineable = frozenset(
        {
            anchor,
            (anchor[0] + 1, anchor[1]),
            (anchor[0] + 2, anchor[1]),
            (anchor[0] + 3, anchor[1]),
        }
    )
    cells = mining_equipment_cells(candidate, mineable_cells=mineable)
    assert len(cells) == 4
    assert anchor in cells
