"""A1 — RTTP core recovery stage diagnosis from evidence rows (read-only)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from django_apps.asteroid_lab.contracts.rttp_recovery_stage_diagnosis import (
    FLAG_CANDIDATE_POOL_EMPTY,
    FLAG_EXTERIOR_ROUTE_MISSING,
    FLAG_MISSING_EXTENSIONS,
    FLAG_NO_COMMITTED_EXTRACTORS,
    FLAG_OUTPUT_TRANSPORT_MISSING,
    FLAG_PLACEMENT_GOAL_SHORTFALL,
    FLAG_RECONSTRUCTION_ENVELOPE_VACUOUS,
    FLAG_ROUTE_MATERIALIZATION_MISSING,
    FLAG_VALIDATION_FAILED,
    FLAG_VALIDATION_FALSE_POSITIVE,
    STAGE_ORDER,
    STAGE_S1_RECONSTRUCTION,
    STAGE_S2_EXTENSION_GEOMETRY,
    STAGE_S3_ROUTE_MATERIALIZATION,
    STAGE_S4_PLACEMENT_GOAL,
    STAGE_S5_SELECTION,
    STAGE_S6_COMMIT_VALIDATION_GAP,
    STAGE_S8_VALIDATION,
    SYMPTOM_NO_COMMITS,
    SYMPTOM_NONE,
    SYMPTOM_ROUTE_ZERO_VALIDATION_PASSED,
)


@dataclass(frozen=True, slots=True)
class RecoveryStageDiagnosis:
    first_failing_stage: str
    blocking_stages: tuple[str, ...]
    diagnostic_flags: tuple[str, ...]
    primary_symptom: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "first_failing_stage": self.first_failing_stage,
            "blocking_stages": list(self.blocking_stages),
            "diagnostic_flags": list(self.diagnostic_flags),
            "primary_symptom": self.primary_symptom,
        }


def _int_field(row: Mapping[str, Any], key: str, default: int = 0) -> int:
    raw = row.get(key)
    if raw is None:
        return default
    return int(raw)


def _earliest_stage(blocking: set[str]) -> str:
    for stage in STAGE_ORDER:
        if stage in blocking:
            return stage
    return SYMPTOM_NONE


def _derive_primary_symptom(
    *,
    flags: frozenset[str],
    validation_passed: bool,
    route_count: int,
    exterior_count: int,
) -> str:
    if FLAG_NO_COMMITTED_EXTRACTORS in flags:
        return SYMPTOM_NO_COMMITS
    if (
        FLAG_VALIDATION_FALSE_POSITIVE in flags
        or (
            validation_passed
            and route_count <= 0
            and FLAG_ROUTE_MATERIALIZATION_MISSING in flags
        )
    ):
        return SYMPTOM_ROUTE_ZERO_VALIDATION_PASSED
    return SYMPTOM_NONE


def diagnose_recovery_evidence_row(row: Mapping[str, Any]) -> RecoveryStageDiagnosis:
    """Classify recovery pipeline stage failures from an A0 evidence row."""

    extractors = _int_field(row, "committed_extractor_count")
    extensions = _int_field(row, "visible_extension_cell_count")
    route_count = _int_field(row, "committed_route_cell_count")
    exterior_count = _int_field(row, "exterior_connected_route_count")
    fot_count = _int_field(row, "committed_output_transport_cells")
    validation_passed = bool(row.get("validation_passed"))
    shape_field_count = row.get("installable_shape_field_cell_count")
    normal_count = row.get("normal_candidate_count")
    placement_goal = row.get("placement_goal_count")
    confirmed = _int_field(row, "confirmed_count")

    flags: set[str] = set()
    blocking: set[str] = set()

    if extractors <= 0:
        flags.add(FLAG_NO_COMMITTED_EXTRACTORS)
        blocking.add(STAGE_S6_COMMIT_VALIDATION_GAP)

    if shape_field_count is not None and int(shape_field_count) <= 0:
        flags.add(FLAG_RECONSTRUCTION_ENVELOPE_VACUOUS)
        blocking.add(STAGE_S1_RECONSTRUCTION)

    if normal_count is not None and int(normal_count) <= 0:
        flags.add(FLAG_CANDIDATE_POOL_EMPTY)
        blocking.add(STAGE_S5_SELECTION)

    if extractors > 0 and extensions <= 0:
        flags.add(FLAG_MISSING_EXTENSIONS)
        blocking.add(STAGE_S2_EXTENSION_GEOMETRY)

    if extractors > 0 and route_count <= 0:
        flags.add(FLAG_ROUTE_MATERIALIZATION_MISSING)
        blocking.add(STAGE_S3_ROUTE_MATERIALIZATION)

    if extractors > 0 and fot_count <= 0:
        flags.add(FLAG_OUTPUT_TRANSPORT_MISSING)
        blocking.add(STAGE_S3_ROUTE_MATERIALIZATION)

    if extractors > 0 and route_count > 0 and exterior_count <= 0:
        flags.add(FLAG_EXTERIOR_ROUTE_MISSING)
        blocking.add(STAGE_S3_ROUTE_MATERIALIZATION)

    if (
        placement_goal is not None
        and confirmed > 0
        and int(placement_goal) > confirmed
        and extractors == confirmed
    ):
        flags.add(FLAG_PLACEMENT_GOAL_SHORTFALL)
        blocking.add(STAGE_S4_PLACEMENT_GOAL)

    if validation_passed and extractors > 0 and (route_count <= 0 or exterior_count <= 0):
        flags.add(FLAG_VALIDATION_FALSE_POSITIVE)
        blocking.add(STAGE_S6_COMMIT_VALIDATION_GAP)

    if not validation_passed:
        flags.add(FLAG_VALIDATION_FAILED)
        blocking.add(STAGE_S8_VALIDATION)

    flag_tuple = tuple(sorted(flags))
    blocking_tuple = tuple(stage for stage in STAGE_ORDER if stage in blocking)
    first = _earliest_stage(blocking) if blocking else SYMPTOM_NONE
    primary = _derive_primary_symptom(
        flags=frozenset(flags),
        validation_passed=validation_passed,
        route_count=route_count,
        exterior_count=exterior_count,
    )

    return RecoveryStageDiagnosis(
        first_failing_stage=first,
        blocking_stages=blocking_tuple,
        diagnostic_flags=flag_tuple,
        primary_symptom=primary,
    )


__all__ = [
    "RecoveryStageDiagnosis",
    "diagnose_recovery_evidence_row",
]
