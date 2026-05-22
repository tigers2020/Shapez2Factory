"""Coverage disposition enum (A1 manifest)."""

from __future__ import annotations

from enum import StrEnum


class Disposition(StrEnum):
    PROMOTED = "promoted"
    CROSS_REF = "cross_ref"
    IGNORE_AUDIT = "ignore_audit"
