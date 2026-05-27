"""Gate A frozen bounds for P1-ELCP-RF-D0 (investigation test assertions only).

Update only when rttp-core-recovery-test-map Gate A overlap-pack stale universe changes.
Source: docs/superpowers/reports/2026-05-27-rttp-elcp-rf-c0-post-b1-commit-regate-report.md
"""

from __future__ import annotations

# Post-F1 reservation policy (2026-05-27): see rttp_e0_gate_a_frozen_bounds.py
EXPECTED_OVERLAP_STALE_ROW_COUNT = 33
D0_ATTRIBUTION_COVERAGE_MIN = 0.95
D0_UNATTRIBUTED_RATIO_MAX = 0.10
D0_VERDICT_DOMINANCE_THRESHOLD = 0.50

__all__ = [
    "D0_ATTRIBUTION_COVERAGE_MIN",
    "D0_UNATTRIBUTED_RATIO_MAX",
    "D0_VERDICT_DOMINANCE_THRESHOLD",
    "EXPECTED_OVERLAP_STALE_ROW_COUNT",
]
