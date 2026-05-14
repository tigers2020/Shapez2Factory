"""STEP 9 validation DTOs (§15) — pure domain; no I/O, Django, preview."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FinalValidationReport:
    """STEP 9 assertion summary (§15); geometry + quarantine boundary."""

    geometry_ok: bool
    connectivity_ok: bool
    quarantined_count: int
