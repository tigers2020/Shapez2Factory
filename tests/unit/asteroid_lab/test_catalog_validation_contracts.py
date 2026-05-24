from django_apps.asteroid_lab.contracts.catalog_placement import CatalogPlacementIssueCode
from django_apps.asteroid_lab.contracts.catalog_validation import (
    CatalogValidationIssue,
    CatalogValidationResult,
    ValidationSeverity,
)


def test_validation_severity_values() -> None:
    assert ValidationSeverity.ERROR.value == "error"
    assert ValidationSeverity.WARNING.value == "warning"


def test_catalog_validation_issue_uses_catalog_issue_code_enum() -> None:
    issue = CatalogValidationIssue(
        issue_code=CatalogPlacementIssueCode.CATALOG_FOOTPRINT_MISMATCH,
        severity=ValidationSeverity.ERROR,
        candidate_id="c1",
        message="footprint mismatch",
    )
    assert issue.issue_code is CatalogPlacementIssueCode.CATALOG_FOOTPRINT_MISMATCH


def test_catalog_validation_result_passed_false_when_errors() -> None:
    issue = CatalogValidationIssue(
        issue_code=CatalogPlacementIssueCode.CATALOG_FOOTPRINT_MISMATCH,
        severity=ValidationSeverity.ERROR,
        candidate_id="c1",
        message="mismatch",
    )
    result = CatalogValidationResult(passed=False, issues=(issue,))
    assert result.passed is False
    assert len(result.issues) == 1
