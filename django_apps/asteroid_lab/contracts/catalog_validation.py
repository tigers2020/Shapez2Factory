"""Catalog placement validation result DTOs (Track D+ PR-2)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from django_apps.asteroid_lab.contracts.catalog_placement import CatalogPlacementIssueCode


class ValidationSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class CatalogValidationIssue:
    issue_code: CatalogPlacementIssueCode
    severity: ValidationSeverity
    candidate_id: str | None
    message: str


@dataclass(frozen=True, slots=True)
class CatalogValidationResult:
    passed: bool
    issues: tuple[CatalogValidationIssue, ...]


__all__ = [
    "CatalogValidationIssue",
    "CatalogValidationResult",
    "ValidationSeverity",
]
