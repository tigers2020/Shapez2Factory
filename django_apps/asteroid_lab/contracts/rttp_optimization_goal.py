"""RTTP optimization goal issue codes and run status (output-only; never solver input)."""

from __future__ import annotations

from enum import StrEnum

MINING_EQUIPMENT_GOAL_SHORTFALL_ISSUE_CODE = "mining_equipment_goal_shortfall"


class RttpRunStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAIL = "fail"


__all__ = [
    "MINING_EQUIPMENT_GOAL_SHORTFALL_ISSUE_CODE",
    "RttpRunStatus",
]
