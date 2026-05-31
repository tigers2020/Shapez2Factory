"""Mining extraction rule row for terrain upper-bound capacity (L1 / CLI envelope)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class MiningExtractionRow:
    resource_kind: str
    mini_unit_output_per_min: Decimal
    output_unit: str
    max_extension_count: int
    source_kind: str = "CANON_MANUAL"


__all__ = ["MiningExtractionRow"]
