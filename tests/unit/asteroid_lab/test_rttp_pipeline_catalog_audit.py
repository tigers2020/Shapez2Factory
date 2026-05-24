"""Track D+ PR-1/PR-2 — pipeline catalog placement audit and AND semantics."""

from __future__ import annotations

from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    SLICE_VERSION,
    BuildingCatalogSlice,
)
from django_apps.asteroid_lab.contracts.catalog_placement import CatalogPlacementIssueCode
from django_apps.asteroid_lab.contracts.catalog_validation import (
    CatalogValidationIssue,
    CatalogValidationResult,
    ValidationSeverity,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot import TransportRegistryEntry
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import ExtractorPlacementPolicy
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpPipelineConfig,
)
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.rttp_solver_summary import (
    RttpAlgorithmStepId,
    build_rttp_solver_summary,
)
from django_apps.asteroid_lab.optimization.validation.catalog_layout_validation import (
    catalog_error_issue_codes_for_summary,
    catalog_error_issue_codes_from_algorithm_steps,
)


def test_pipeline_includes_observe_only_catalog_placement_validation_step(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    result = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(catalog_placement_validation_mode="observe_only"),
    )
    audit_rows = [
        row
        for row in result.algorithm_steps
        if row["step_id"] == RttpAlgorithmStepId.RTTP_CATALOG_PLACEMENT_VALIDATION.value
    ]
    assert len(audit_rows) == 1
    audit_row = audit_rows[0]
    assert audit_row["passed"] is True
    assert audit_row["metrics"]["catalog_validation_mode"] == "observe_only"
    commit_rows = [
        row
        for row in result.algorithm_steps
        if row["step_id"] == RttpAlgorithmStepId.RTTP_COMMIT.value
    ]
    assert len(commit_rows) == 1
    assert commit_rows[0]["metrics"]["validation_passed"] == result.validation_passed


def _greenfield_with_catalog_slice(base: OptimizationInput) -> OptimizationInput:
    catalog_slice = BuildingCatalogSlice(
        slice_version=SLICE_VERSION,
        transport_registry=(TransportRegistryEntry("space_belt", "belt", "bv:stub"),),
        variants=(),
        variant_geometries=(),
    )
    return OptimizationInput(
        mineable_cells=base.mineable_cells,
        rim_cells=base.rim_cells,
        inner_cells=base.inner_cells,
        external_void_cells=base.external_void_cells,
        protected_corridor_cells=base.protected_corridor_cells,
        existing_trunk_cells=base.existing_trunk_cells,
        transport_kind=base.transport_kind,
        route_goals=base.route_goals,
        existing_transport_cells=base.existing_transport_cells,
        blocked_incompatible_transport_cells=base.blocked_incompatible_transport_cells,
        coord_frame=base.coord_frame,
        catalog_slice=catalog_slice,
    )


def test_synthetic_unmapped_audit_observe_only_does_not_force_validation_failure(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    """Synthetic candidates without catalog_placement_ref are unmapped but non-failing."""

    inp = _greenfield_with_catalog_slice(greenfield_optimization_input)
    result = run_rttp_pipeline(
        inp,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(catalog_placement_validation_mode="observe_only"),
    )
    assert len(result.commit_result.committed_ids) > 0
    audit_row = next(
        row
        for row in result.algorithm_steps
        if row["step_id"] == RttpAlgorithmStepId.RTTP_CATALOG_PLACEMENT_VALIDATION.value
    )
    assert audit_row["passed"] is True
    metrics = audit_row["metrics"]
    assert metrics["catalog_validation_mode"] == "observe_only"
    assert metrics["checked_candidate_count"] == len(result.commit_result.committed_ids)
    assert metrics["unmapped_candidate_count"] == metrics["checked_candidate_count"]
    assert metrics.get("catalog_slice_version") == SLICE_VERSION
    commit_row = next(
        row
        for row in result.algorithm_steps
        if row["step_id"] == RttpAlgorithmStepId.RTTP_COMMIT.value
    )
    assert commit_row["metrics"]["validation_passed"] == result.validation_passed
    assert result.validation_passed == commit_row["passed"]


def test_pipeline_validation_passed_false_when_catalog_validation_fails(
    greenfield_optimization_input: OptimizationInput,
    monkeypatch,
) -> None:
    def _fail_catalog_validation(*_args, **_kwargs):
        return CatalogValidationResult(
            passed=False,
            issues=(
                CatalogValidationIssue(
                    issue_code=CatalogPlacementIssueCode.CATALOG_FOOTPRINT_MISMATCH,
                    severity=ValidationSeverity.ERROR,
                    candidate_id="injected-c1",
                    message="injected for pipeline AND test",
                ),
            ),
        )

    monkeypatch.setattr(
        "django_apps.asteroid_lab.optimization.validation.catalog_layout_validation.validate_catalog_placements",
        _fail_catalog_validation,
    )
    result = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(catalog_placement_validation_mode="mapped_fail_closed"),
    )
    assert result.validation_passed is False
    audit_row = next(
        row
        for row in result.algorithm_steps
        if row["step_id"] == RttpAlgorithmStepId.RTTP_CATALOG_PLACEMENT_VALIDATION.value
    )
    assert audit_row["passed"] is False
    assert audit_row["metrics"]["catalog_validation_mode"] == "mapped_fail_closed"
    assert (
        CatalogPlacementIssueCode.CATALOG_FOOTPRINT_MISMATCH.value
        in audit_row["metrics"]["catalog_error_issue_codes"]
    )
    summary = build_rttp_solver_summary(
        pipeline_ok=result.validation_passed,
        committed_count=len(result.commit_result.committed_ids),
        normal_count=result.normal_count,
        commit_order=result.genome.commit_order,
        algorithm_steps=result.algorithm_steps,
        catalog_error_issue_codes=catalog_error_issue_codes_from_algorithm_steps(
            result.algorithm_steps
        ),
    )
    assert summary["issue_codes"] == [CatalogPlacementIssueCode.CATALOG_FOOTPRINT_MISMATCH.value]


def test_pipeline_warning_only_catalog_does_not_fail_validation_or_top_level_issue_codes(
    greenfield_optimization_input: OptimizationInput,
    monkeypatch,
) -> None:
    def _warn_only_catalog_validation(*_args, **_kwargs):
        return CatalogValidationResult(
            passed=True,
            issues=(
                CatalogValidationIssue(
                    issue_code=CatalogPlacementIssueCode.CATALOG_VARIANT_MAPPING_MISSING,
                    severity=ValidationSeverity.WARNING,
                    candidate_id="c-warn",
                    message="unmapped synthetic warning",
                ),
            ),
        )

    monkeypatch.setattr(
        "django_apps.asteroid_lab.optimization.validation.catalog_layout_validation.validate_catalog_placements",
        _warn_only_catalog_validation,
    )
    result = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(catalog_placement_validation_mode="mapped_fail_closed"),
    )
    assert result.validation_passed is True
    audit_row = next(
        row
        for row in result.algorithm_steps
        if row["step_id"] == RttpAlgorithmStepId.RTTP_CATALOG_PLACEMENT_VALIDATION.value
    )
    assert audit_row["passed"] is True
    assert (
        CatalogPlacementIssueCode.CATALOG_VARIANT_MAPPING_MISSING.value
        in audit_row["metrics"]["catalog_warning_codes"]
    )
    assert audit_row["metrics"]["catalog_error_issue_codes"] == []
    summary = build_rttp_solver_summary(
        pipeline_ok=result.validation_passed,
        committed_count=len(result.commit_result.committed_ids),
        normal_count=result.normal_count,
        commit_order=result.genome.commit_order,
        algorithm_steps=result.algorithm_steps,
        catalog_error_issue_codes=catalog_error_issue_codes_from_algorithm_steps(
            result.algorithm_steps
        ),
    )
    assert summary["issue_codes"] == []
    assert (
        catalog_error_issue_codes_for_summary(
            CatalogValidationResult(
                passed=True,
                issues=(
                    CatalogValidationIssue(
                        issue_code=CatalogPlacementIssueCode.CATALOG_VARIANT_MAPPING_MISSING,
                        severity=ValidationSeverity.WARNING,
                        candidate_id="c-warn",
                        message="warn",
                    ),
                ),
            )
        )
        == ()
    )


def test_pipeline_observe_only_mode_unchanged_when_catalog_validation_would_fail(
    greenfield_optimization_input: OptimizationInput,
    monkeypatch,
) -> None:
    def _fail_catalog_validation(*_args, **_kwargs):
        return CatalogValidationResult(
            passed=False,
            issues=(
                CatalogValidationIssue(
                    issue_code=CatalogPlacementIssueCode.CATALOG_FOOTPRINT_MISMATCH,
                    severity=ValidationSeverity.ERROR,
                    candidate_id="injected-c1",
                    message="injected",
                ),
            ),
        )

    monkeypatch.setattr(
        "django_apps.asteroid_lab.optimization.validation.catalog_layout_validation.validate_catalog_placements",
        _fail_catalog_validation,
    )
    result = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(catalog_placement_validation_mode="observe_only"),
    )
    audit_row = next(
        row
        for row in result.algorithm_steps
        if row["step_id"] == RttpAlgorithmStepId.RTTP_CATALOG_PLACEMENT_VALIDATION.value
    )
    assert audit_row["metrics"]["catalog_validation_mode"] == "observe_only"
    assert audit_row["passed"] is True
    assert result.validation_passed is True
