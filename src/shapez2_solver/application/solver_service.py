from dataclasses import dataclass

from shapez2_solver.domain.shape_pattern import NormalizedShapePattern


@dataclass(frozen=True, slots=True)
class SolverRequest:
    target_pattern: NormalizedShapePattern
    max_depth: int = 12


@dataclass(frozen=True, slots=True)
class SolverResult:
    found: bool
    steps: tuple[str, ...] = ()


class SolverService:
    def solve(self, request: SolverRequest) -> SolverResult:
        return SolverResult(
            found=False,
            steps=(f"target:{request.target_pattern.normalized_code}",),
        )
