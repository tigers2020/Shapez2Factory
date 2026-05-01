from dataclasses import dataclass

from shapez2_solver.domain.shape import ShapeCode


@dataclass(frozen=True, slots=True)
class SolverRequest:
    target_shape: ShapeCode
    max_depth: int = 12


@dataclass(frozen=True, slots=True)
class SolverResult:
    found: bool
    steps: tuple[str, ...] = ()


class SolverService:
    def solve(self, request: SolverRequest) -> SolverResult:
        return SolverResult(found=False, steps=(f"target:{request.target_shape.normalized()}",))
