"""Gate A frozen bounds for P1-ELCP-RF-F1.1 (investigation test assertions only).

Update only when post-F1 Gate A private_route_overlap slice count changes.
"""

from __future__ import annotations

F11_EXPECTED_PRIVATE_OVERLAP_ROW_COUNT = 20
F11_UNCLEAR_MAX_ROWS = 2
F11_ROOT_CAUSE_DOMINANCE_MIN_COUNT = 10  # 50% of 20

__all__ = [
    "F11_EXPECTED_PRIVATE_OVERLAP_ROW_COUNT",
    "F11_ROOT_CAUSE_DOMINANCE_MIN_COUNT",
    "F11_UNCLEAR_MAX_ROWS",
]
