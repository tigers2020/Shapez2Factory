from __future__ import annotations

from dataclasses import dataclass


class SolverValidationError(Exception):
    """(레거시) 레시피 재생 검증 실패 — 인벤토리 전용 경로에서는 사용되지 않는다."""

    code = "SOLVER_VALIDATION_ERROR"

    def __init__(self, expected: str, actual: str) -> None:
        super().__init__(f"expected {expected}, got {actual}")
        self.expected = expected
        self.actual = actual


@dataclass(frozen=True, slots=True)
class SolveStep:
    id: str
    operation_type: str
    title: str
    description: str
    input_shape_codes: tuple[str, ...]
    output_shape_codes: tuple[str, ...]


__all__ = ["SolveStep", "SolverValidationError"]
