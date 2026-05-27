"""Gate A G1 bounds for P1-ELCP-RF-F1 (investigation assertions only)."""

from __future__ import annotations

E0_PRIVATE_ROUTE_OVERLAP_MECHANISM_BASELINE = 23
F1_G1_MAX_PRIVATE_ROUTE_OVERLAP_ROWS = 11  # floor(23 * 0.5) — ≥50% reduction

__all__ = [
    "E0_PRIVATE_ROUTE_OVERLAP_MECHANISM_BASELINE",
    "F1_G1_MAX_PRIVATE_ROUTE_OVERLAP_ROWS",
]
