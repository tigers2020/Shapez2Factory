"""Track D+ — catalog placement contract tests."""

from __future__ import annotations

from django_apps.asteroid_lab.contracts.catalog_placement import (
    CardinalDirection,
    CatalogPlacementIssueCode,
)


def test_cardinal_direction_values() -> None:
    assert CardinalDirection.E.value == "E"
    assert CardinalDirection.N.value == "N"


def test_catalog_placement_issue_code_is_str_enum() -> None:
    assert CatalogPlacementIssueCode.CATALOG_FOOTPRINT_MISMATCH.value == (
        "catalog_footprint_mismatch"
    )
