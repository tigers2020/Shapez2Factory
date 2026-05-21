"""Solver Runtime A→M pipeline unit tests (PR7)."""

from __future__ import annotations

from pathlib import Path

from django_apps.asteroid_lab.optimization.bundle_selection_targets import (
    BundleSelectionTargets,
)
from django_apps.asteroid_lab.optimization.candidate_selector import SelectedCandidatePlan
from django_apps.asteroid_lab.optimization.commit_best_candidates import IncrementalCommitResult
from django_apps.asteroid_lab.optimization.enums import (
    ValidationIssueCode,
    ValidationSeverity,
)
from django_apps.asteroid_lab.optimization.final_validation import validate_final_layout
from django_apps.asteroid_lab.optimization.gene_template_loader import load_gene_templates_from_json
from django_apps.asteroid_lab.optimization.input_contracts import (
    BBox,
    greenfield_optimization_input,
)
from django_apps.asteroid_lab.optimization.loaded_snapshot import LoadedReconstructionSnapshot
from django_apps.asteroid_lab.optimization.materialization_dtos import (
    MaterializedLayoutCells,
    RouteMaterializationResult,
)
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_loaded_snapshot,
)
from django_apps.asteroid_lab.optimization.timing_metrics import SolverRuntimeTimingMetrics
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.services.solver_runtime_pipeline import (
    _build_solver_summary,
    _gate_c_branch_hint,
    run_solver_runtime_pipeline,
)

_FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "asteroid_lab" / "gene_templates"


def _minimal_gene_templates() -> tuple:
    return load_gene_templates_from_json(_FIXTURE_DIR / "minimal_extractor_e.json")


def _cell(
    x: int,
    y: int,
    *,
    cell_kind: str = "shape_miner_extension",
    server_x: int | None = None,
    server_y: int | None = None,
) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=x,
        y=y,
        layer=None,
        rotation=0,
        tile_type="",
        cell_kind=cell_kind,
        transport_kind="none",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={},
        server_x=server_x,
        server_y=server_y,
    )


def _pipeline_loaded_snapshot() -> LoadedReconstructionSnapshot:
    """Single rim mineable cell at server (0, 0) with void goals along +x."""

    return LoadedReconstructionSnapshot(
        cells=(_cell(1, 0, cell_kind="shape_miner_extension", server_x=0, server_y=0),),
        server_xy_params=(1, 0),
    )


def test_pipeline_runs_end_to_end_without_orm() -> None:
    loaded = _pipeline_loaded_snapshot()
    inp = optimization_input_from_loaded_snapshot(loaded)
    assert len(inp.rim_cells) >= 1

    result = run_solver_runtime_pipeline(
        loaded=loaded,
        gene_templates=_minimal_gene_templates(),
        run_key="unit",
    )

    assert result.run_key == "unit"
    assert isinstance(result.solver_summary["validation_passed"], bool)
    assert "confirmed_count" in result.solver_summary
    assert "issue_details" in result.solver_summary
    assert isinstance(result.solver_summary["issue_details"], list)
    assert "route_out_count" in result.solver_summary
    assert "target_miner_bundle_count" in result.solver_summary
    assert "best_genome_enabled_gene_count" in result.solver_summary
    assert "commit_attempt_count" in result.solver_summary
    for key in (
        "capacity_satisfied",
        "capacity_deficit_count",
        "throughput_deficit_count",
        "placement_capacity_satisfied",
        "throughput_budget_satisfied",
        "target_placement_count",
        "run_success",
    ):
        assert key in result.solver_summary


def test_solver_summary_includes_commit_skip_reason_fields() -> None:
    loaded = _pipeline_loaded_snapshot()
    result = run_solver_runtime_pipeline(
        loaded=loaded,
        gene_templates=_minimal_gene_templates(),
        run_key="skip_reason",
    )
    summary = result.solver_summary
    assert "skipped_by_reason" in summary
    assert isinstance(summary["skipped_by_reason"], dict)
    assert sum(summary["skipped_by_reason"].values()) == summary["commit_rolled_back_count"]
    for key in (
        "commit_occupied_cell_conflict_count",
        "commit_route_cell_conflict_count",
        "commit_route_probe_failed_count",
        "commit_transport_kind_conflict_count",
        "commit_hard_blocked_conflict_count",
        "commit_hard_protected_conflict_count",
    ):
        assert key in summary
        assert isinstance(summary[key], int)
    assert (
        summary["commit_occupied_cell_conflict_count"]
        + summary["commit_route_cell_conflict_count"]
        + summary["commit_route_probe_failed_count"]
        + summary["commit_transport_kind_conflict_count"]
        + summary["commit_hard_blocked_conflict_count"]
        + summary["commit_hard_protected_conflict_count"]
    ) == summary["commit_rolled_back_count"]


def test_gate_c_branch_hint_classifies_supply_bottleneck() -> None:
    assert (
        _gate_c_branch_hint(
            rim_cell_count=10,
            reachable_anchors_after_prefilter_count=7,
            unique_anchors_in_normal_pool_count=7,
        )
        == "c1_probe_domain"
    )
    assert (
        _gate_c_branch_hint(
            rim_cell_count=7,
            reachable_anchors_after_prefilter_count=12,
            unique_anchors_in_normal_pool_count=7,
        )
        == "c3_dedupe_truncation"
    )
    assert (
        _gate_c_branch_hint(
            rim_cell_count=7,
            reachable_anchors_after_prefilter_count=7,
            unique_anchors_in_normal_pool_count=7,
        )
        == "c2_rim_topology"
    )


def test_gate_c_branch_hint_7_route_snapshot_geometry_limited() -> None:
    """Post-PR-1 production snapshot: rim == reachable == pool anchors → Gate C2."""

    assert (
        _gate_c_branch_hint(
            rim_cell_count=7,
            reachable_anchors_after_prefilter_count=7,
            unique_anchors_in_normal_pool_count=7,
        )
        == "c2_rim_topology"
    )


def test_solver_summary_generation_gate_c_metric_chain() -> None:
    """Six-stage anchor funnel: rim >= reachable >= probe >= dedupe >= truncate >= pool."""

    loaded = _pipeline_loaded_snapshot()
    result = run_solver_runtime_pipeline(
        loaded=loaded,
        gene_templates=_minimal_gene_templates(),
        run_key="gate_c_chain",
    )
    summary = result.solver_summary
    rim = summary["rim_cell_count"]
    reachable = summary["reachable_anchors_after_prefilter_count"]
    probe_anchors = summary["unique_anchors_after_probe_budget_count"]
    dedupe_anchors = summary["unique_anchors_after_dedupe_count"]
    truncate_anchors = summary["unique_anchors_after_truncate_count"]
    pool_anchors = summary["unique_anchors_in_normal_pool_count"]
    assert rim >= reachable >= probe_anchors >= dedupe_anchors >= truncate_anchors
    assert truncate_anchors == pool_anchors
    assert summary["anchors_dropped_by_probe_budget_count"] + probe_anchors == reachable
    assert (
        summary["anchor_preserved_by_truncation_count"]
        + summary["anchor_dropped_by_truncation_count"]
        == dedupe_anchors
    )
    assert summary["gate_c_branch_hint"] == _gate_c_branch_hint(
        rim_cell_count=rim,
        reachable_anchors_after_prefilter_count=reachable,
        unique_anchors_in_normal_pool_count=pool_anchors,
    )


def test_solver_summary_includes_generation_anchor_diagnostic_fields() -> None:
    loaded = _pipeline_loaded_snapshot()
    result = run_solver_runtime_pipeline(
        loaded=loaded,
        gene_templates=_minimal_gene_templates(),
        run_key="gen_diag",
    )
    summary = result.solver_summary
    for key in (
        "rim_cell_count",
        "reachable_anchors_after_prefilter_count",
        "unique_anchors_after_probe_budget_count",
        "anchors_dropped_by_probe_budget_count",
        "probe_budget_floor_reserved_count",
        "probe_budget_fill_count",
        "truncated_by_max_candidates_count",
        "normal_pool_variants_per_anchor_max",
        "unique_anchors_after_dedupe_count",
        "unique_anchors_after_truncate_count",
        "anchor_preserved_by_truncation_count",
        "anchor_dropped_by_truncation_count",
    ):
        assert key in summary, f"missing summary field: {key!r}"
        assert isinstance(summary[key], int)
    assert "unique_anchors_after_dedupe_before_truncate_count" not in summary
    assert isinstance(summary["gate_c_branch_hint"], str)
    assert summary["gate_c_branch_hint"] in (
        "c1_probe_domain",
        "c2_rim_topology",
        "c3_dedupe_truncation",
        "unknown",
    )


def test_solver_summary_includes_selection_throughput_stop_fields() -> None:
    loaded = _pipeline_loaded_snapshot()
    result = run_solver_runtime_pipeline(
        loaded=loaded,
        gene_templates=_minimal_gene_templates(),
        run_key="sel_tp_stop",
    )
    summary = result.solver_summary
    assert "selection_stopped_by_throughput_budget" in summary
    assert "selected_throughput_at_stop" in summary
    assert isinstance(summary["selection_stopped_by_throughput_budget"], int)
    assert isinstance(summary["selected_throughput_at_stop"], int)
    assert "commit_equipment_transport_overlap_count" in summary


def test_solver_summary_includes_anchor_diversity_fields() -> None:
    loaded = _pipeline_loaded_snapshot()
    result = run_solver_runtime_pipeline(
        loaded=loaded,
        gene_templates=_minimal_gene_templates(),
        run_key="anchor_div",
    )
    summary = result.solver_summary
    for key in (
        "unique_anchors_in_normal_pool_count",
        "unique_anchors_selected_count",
        "variants_per_anchor_max",
        "selected_duplicate_anchor_count",
        "selection_skipped_duplicate_anchor_count",
        "max_selected_variants_per_extractor",
    ):
        assert key in summary, f"missing summary field: {key!r}"
        assert isinstance(summary[key], int)
    assert summary["selected_duplicate_anchor_count"] == 0
    assert summary["variants_per_anchor_max"] <= summary["max_selected_variants_per_extractor"]
    assert (
        summary["unique_anchors_selected_count"] <= summary["unique_anchors_in_normal_pool_count"]
    )


def test_solver_summary_includes_capacity_diagnostic_fields() -> None:
    """New throughput-chain fields are present and typed as int."""
    loaded = _pipeline_loaded_snapshot()
    result = run_solver_runtime_pipeline(
        loaded=loaded,
        gene_templates=_minimal_gene_templates(),
        run_key="diag",
    )
    summary = result.solver_summary
    for key in (
        "target_throughput",
        "normal_pool_throughput",
        "selected_throughput",
        "confirmed_throughput",
        "unique_gene_ids_used_count",
    ):
        assert key in summary, f"missing summary field: {key!r}"
        assert isinstance(
            summary[key], int
        ), f"summary[{key!r}] expected int, got {type(summary[key])}"


def test_validation_warns_under_target_throughput_without_failing() -> None:
    """UNDER_TARGET_THROUGHPUT is a warning; validation.passed stays True.

    Calls validate_final_layout directly so target > 0 is guaranteed regardless
    of whether the minimal fixture produces any route goals.
    """
    inp = greenfield_optimization_input(bbox=BBox(0, 10, 0, 0))

    targets = BundleSelectionTargets(
        route_out_count=1,
        miners_per_shape_route=12,
        pumps_per_fluid_route=72,
        target_miner_bundle_count=12,
        shape_route_out_count=1,
        fluid_route_out_count=0,
    )

    empty_commit = IncrementalCommitResult(
        confirmed=(),
        skipped_candidates=(),
        goal_assigned_platforms={},
    )

    empty_layout = MaterializedLayoutCells(cells=(), equipment_cells=())

    result = validate_final_layout(
        empty_commit,
        empty_layout,
        inp=inp,
        candidates_by_id={},
        targets=targets,
    )

    assert result.passed is True  # only WARNING issued; no ERROR

    matching = [
        i for i in result.issues if i.issue_code == ValidationIssueCode.UNDER_TARGET_THROUGHPUT
    ]
    assert len(matching) == 1, f"expected 1 UNDER_TARGET_THROUGHPUT issue, got {len(matching)}"
    assert matching[0].severity == ValidationSeverity.WARNING
    assert "confirmed throughput is below selection target" in matching[0].message


def _minimal_pool_metrics() -> dict[str, int]:
    return {
        "projected_candidate_count_before_probe": 0,
        "normal_candidate_count_after_probe": 0,
        "rejected_candidate_count": 0,
        "deduped_candidate_count": 0,
    }


def test_build_solver_summary_capacity_fields_when_under_target() -> None:
    targets = BundleSelectionTargets(
        route_out_count=7,
        miners_per_shape_route=12,
        pumps_per_fluid_route=1,
        target_miner_bundle_count=84,
        shape_route_out_count=7,
        fluid_route_out_count=0,
    )
    summary = _build_solver_summary(
        validation_passed=True,
        commit_count=6,
        skipped_records=(),
        materialization=RouteMaterializationResult(layout=None, failure_reason=None),
        issues=(),
        timing=SolverRuntimeTimingMetrics(),
        targets=targets,
        raw_pattern_count=0,
        pool_metrics=_minimal_pool_metrics(),
        plan=SelectedCandidatePlan(ordered_candidate_ids=()),
        commit_attempt_count=6,
        throughput_metrics={
            "target_throughput": 84,
            "normal_pool_throughput": 6,
            "selected_throughput": 6,
            "confirmed_throughput": 6,
            "unique_gene_ids_used_count": 1,
        },
        anchor_metrics={},
        generation_metrics={},
    )
    assert summary["validation_passed"] is True
    assert summary["placement_capacity_satisfied"] is False
    assert summary["throughput_budget_satisfied"] is False
    assert summary["capacity_satisfied"] is False
    assert summary["capacity_deficit_count"] == 78
    assert summary["throughput_deficit_count"] == 78
    assert summary["run_success"] is False


def test_build_solver_summary_run64_mirror() -> None:
    """Run #64: 6 placements, throughput 96/84 — placement fails, throughput OK."""

    targets = BundleSelectionTargets(
        route_out_count=7,
        miners_per_shape_route=12,
        pumps_per_fluid_route=1,
        target_miner_bundle_count=84,
        shape_route_out_count=7,
        fluid_route_out_count=0,
    )
    summary = _build_solver_summary(
        validation_passed=True,
        commit_count=6,
        skipped_records=(),
        materialization=RouteMaterializationResult(layout=None, failure_reason=None),
        issues=(),
        timing=SolverRuntimeTimingMetrics(),
        targets=targets,
        raw_pattern_count=102,
        pool_metrics=_minimal_pool_metrics(),
        plan=SelectedCandidatePlan(ordered_candidate_ids=("a", "b", "c", "d", "e", "f")),
        commit_attempt_count=6,
        throughput_metrics={
            "target_throughput": 84,
            "normal_pool_throughput": 1024,
            "selected_throughput": 96,
            "confirmed_throughput": 96,
            "unique_gene_ids_used_count": 4,
        },
        anchor_metrics={},
        generation_metrics={},
    )
    assert summary["confirmed_count"] == 6
    assert summary["target_miner_bundle_count"] == 84
    assert summary["target_placement_count"] == 84
    assert summary["target_throughput"] == 84
    assert summary["confirmed_throughput"] == 96
    assert summary["placement_capacity_satisfied"] is False
    assert summary["throughput_budget_satisfied"] is True
    assert summary["capacity_satisfied"] is False
    assert summary["run_success"] is False
    assert summary["capacity_deficit_count"] == 78
    assert summary["throughput_deficit_count"] == 0


def test_build_solver_summary_run_success_when_capacity_met() -> None:
    targets = BundleSelectionTargets(
        route_out_count=1,
        miners_per_shape_route=12,
        pumps_per_fluid_route=1,
        target_miner_bundle_count=12,
        shape_route_out_count=1,
        fluid_route_out_count=0,
    )
    summary = _build_solver_summary(
        validation_passed=True,
        commit_count=12,
        skipped_records=(),
        materialization=RouteMaterializationResult(layout=None, failure_reason=None),
        issues=(),
        timing=SolverRuntimeTimingMetrics(),
        targets=targets,
        raw_pattern_count=0,
        pool_metrics=_minimal_pool_metrics(),
        plan=SelectedCandidatePlan(ordered_candidate_ids=()),
        commit_attempt_count=12,
        throughput_metrics={
            "target_throughput": 12,
            "normal_pool_throughput": 12,
            "selected_throughput": 12,
            "confirmed_throughput": 12,
            "unique_gene_ids_used_count": 1,
        },
        anchor_metrics={},
        generation_metrics={},
    )
    assert summary["placement_capacity_satisfied"] is True
    assert summary["throughput_budget_satisfied"] is True
    assert summary["capacity_satisfied"] is True
    assert summary["capacity_deficit_count"] == 0
    assert summary["throughput_deficit_count"] == 0
    assert summary["run_success"] is True


def test_pipeline_solver_summary_is_deterministic() -> None:
    loaded = _pipeline_loaded_snapshot()
    templates = _minimal_gene_templates()

    r1 = run_solver_runtime_pipeline(loaded=loaded, gene_templates=templates)
    r2 = run_solver_runtime_pipeline(loaded=loaded, gene_templates=templates)

    def _summary_without_timing(summary: dict) -> dict:
        out = dict(summary)
        out.pop("timing", None)
        return out

    assert _summary_without_timing(r1.solver_summary) == _summary_without_timing(r2.solver_summary)
    assert r1.commit == r2.commit
