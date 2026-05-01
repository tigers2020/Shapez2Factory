from dataclasses import dataclass

from shapez2_solver.domain.shape import ShapeCode


@dataclass(frozen=True, slots=True)
class PlannerRequest:
    target_shape: ShapeCode
    target_rate_per_min: float


@dataclass(frozen=True, slots=True)
class PlannerResult:
    required_inputs: tuple[str, ...] = ()


class PlannerService:
    def plan(self, request: PlannerRequest) -> PlannerResult:
        return PlannerResult(required_inputs=(request.target_shape.normalized(),))
