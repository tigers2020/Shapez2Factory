"""Pass3 eligibility must use explicit ``step4_committed`` (no trunk_load default-True inference)."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_permission import (
    pass3_permission_snapshot,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation_contracts import (
    FinalValidationReport,
)


def _ok_report() -> FinalValidationReport:
    return FinalValidationReport(
        geometry_valid=True,
        connectivity_valid=True,
        disconnected_stub_count=0,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=0,
        overlap_violation_count=0,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
    )


def test_pass3_permission_false_when_step4_not_committed() -> None:
    snap = pass3_permission_snapshot(
        pass12_skipped=False,
        step4_committed=False,
        unfinalized_placement_count=0,
        report_step4=_ok_report(),
    )
    assert snap["eligible"] is False
    assert snap["step4_committed"] is False
    assert snap["skip_reason"] == "step4_not_committed"


def test_pass3_permission_true_when_step4_committed() -> None:
    snap = pass3_permission_snapshot(
        pass12_skipped=False,
        step4_committed=True,
        unfinalized_placement_count=0,
        report_step4=_ok_report(),
    )
    assert snap["eligible"] is True
    assert snap["skip_reason"] is None
