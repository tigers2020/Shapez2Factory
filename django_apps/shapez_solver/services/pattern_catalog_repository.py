"""Pattern Lab macro candidate lookup (DB catalog removed)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PatternMacroStepCandidate:
    """Pattern Lab에 표시할 macro recipe step 메타데이터."""

    step_index: int
    operation: str
    input_slots: tuple[str, ...]
    output_slots: tuple[str, ...]
    note: str


@dataclass(frozen=True, slots=True)
class PatternMacroCandidate:
    """Pattern Lab macro strategy 후보 메타데이터."""

    macro_code: str
    strategy_code: str
    family_code: str
    estimated_operation_cost: int
    estimated_stage_cost: int
    estimated_waste_cost: int
    priority: int
    steps: tuple[PatternMacroStepCandidate, ...] = ()
    lab_step_source: str = "database"


class PatternCatalogRepository:
    """Pattern Lab용 macro 후보 조회 — 영구 저장소 없음."""

    def find_macro_candidates(self, *, signature: str) -> tuple[PatternMacroCandidate, ...]:
        del signature
        return ()
