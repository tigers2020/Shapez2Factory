"""Track D+ PR-1 — pipeline catalog placement audit (observe-only)."""

from __future__ import annotations

from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    SLICE_VERSION,
    BuildingCatalogSlice,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot import TransportRegistryEntry
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import ExtractorPlacementPolicy
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.rttp_solver_summary import RttpAlgorithmStepId


def test_pipeline_includes_observe_only_catalog_placement_validation_step(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    result = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
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
