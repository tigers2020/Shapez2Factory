from dataclasses import dataclass

from django_apps.shapez_core.domain.shape_pattern import NormalizedShapePattern


@dataclass(frozen=True, slots=True)
class PlannerRequest:
    target_pattern: NormalizedShapePattern
    target_rate_per_min: float


@dataclass(frozen=True, slots=True)
class PlannerResult:
    required_inputs: tuple[str, ...] = ()


class PlannerService:
    def plan(self, request: PlannerRequest) -> PlannerResult:
        return PlannerResult(required_inputs=(request.target_pattern.normalized_code,))
