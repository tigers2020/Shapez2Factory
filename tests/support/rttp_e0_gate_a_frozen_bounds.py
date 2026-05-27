"""Gate A frozen bounds for P1-ELCP-RF-E0 (investigation test assertions only).

Update only when rttp-core-recovery-test-map Gate A overlap-pack stale universe changes.
Source: docs/superpowers/reports/2026-05-27-rttp-elcp-rf-d0-stale-candidate-reachable-report.md
"""

from __future__ import annotations

# Post-F1 reservation policy (2026-05-27 SHA): one fewer stale row vs E0 baseline.
EXPECTED_OVERLAP_STALE_ROW_COUNT = 33
EXPECTED_ROUTE_CELL_CONFLICT_COUNT = 20
EXPECTED_INLET_ON_SHARED_TRANSPORT_COUNT = 13

E0_MECHANISM_COVERAGE_MIN = 0.95
E0_UNATTRIBUTED_RATIO_MAX = 0.10
E0_VERDICT_DOMINANCE_THRESHOLD = 0.50
E0_SPLIT_FAMILY_MIN_RATIO = 0.35
E0_MECHANISM_CLASS_DOMINANCE_FOR_NOMINATION = 0.50

__all__ = [
    "E0_MECHANISM_CLASS_DOMINANCE_FOR_NOMINATION",
    "E0_MECHANISM_COVERAGE_MIN",
    "E0_SPLIT_FAMILY_MIN_RATIO",
    "E0_UNATTRIBUTED_RATIO_MAX",
    "E0_VERDICT_DOMINANCE_THRESHOLD",
    "EXPECTED_INLET_ON_SHARED_TRANSPORT_COUNT",
    "EXPECTED_OVERLAP_STALE_ROW_COUNT",
    "EXPECTED_ROUTE_CELL_CONFLICT_COUNT",
]
