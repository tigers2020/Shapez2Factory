"""RTTP genome selection mode (PR-GA-2)."""

from __future__ import annotations

from enum import StrEnum


class SelectionMode(StrEnum):
    GREEDY_REGRET = "greedy_regret"
    GREEDY_REGRET_OVERLAP_PACK = "greedy_regret_overlap_pack"
    EVOLUTION = "evolution"


__all__ = ["SelectionMode"]
