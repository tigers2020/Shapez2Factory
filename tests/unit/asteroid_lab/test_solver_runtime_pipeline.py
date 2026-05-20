"""Solver Runtime A→M pipeline unit tests (PR7)."""

from __future__ import annotations

from pathlib import Path

from django_apps.asteroid_lab.optimization.bundle_selection_targets import (
    BundleSelectionTargets,
)
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
from django_apps.asteroid_lab.optimization.materialization_dtos import MaterializedLayoutCells
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_loaded_snapshot,
)
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.services.solver_runtime_pipeline import run_solver_runtime_pipeline

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
        assert isinstance(summary[key], int), (
            f"summary[{key!r}] expected int, got {type(summary[key])}"
        )


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
        skipped_candidate_ids=(),
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
        i
        for i in result.issues
        if i.issue_code == ValidationIssueCode.UNDER_TARGET_THROUGHPUT
    ]
    assert len(matching) == 1, f"expected 1 UNDER_TARGET_THROUGHPUT issue, got {len(matching)}"
    assert matching[0].severity == ValidationSeverity.WARNING
    assert "confirmed throughput is below selection target" in matching[0].message


def test_pipeline_solver_summary_is_deterministic() -> None:
    loaded = _pipeline_loaded_snapshot()
    templates = _minimal_gene_templates()

    r1 = run_solver_runtime_pipeline(loaded=loaded, gene_templates=templates)
    r2 = run_solver_runtime_pipeline(loaded=loaded, gene_templates=templates)

    def _summary_without_timing(summary: dict) -> dict:
        out = dict(summary)
        out.pop("timing", None)
        return out

    assert _summary_without_timing(r1.solver_summary) == _summary_without_timing(
        r2.solver_summary
    )
    assert r1.commit == r2.commit
