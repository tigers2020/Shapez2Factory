# Factory Throughput Layer Plan


> **Plans (misc):** Project planning memo; not Asteroid Lab coordinate canon. See [`documents/Algorithm/`](../Algorithm/) and [`docs/superpowers/specs/`](../docs/superpowers/specs/) for active specs.

## Summary

- Layer 2 adds factory-oriented quantity planning on top of the existing single-target recipe solver.
- The first implementation slice is limited to the document gate plus Phase 1 base-demand domain logic and unit tests.
- `target_count` means final target quantity only. `output_lanes` stays out of scope until a later graph-focused phase.

## MVP Policy

- Phase 1 lives in `django_apps/shapez_solver/domain/factory_demand.py`.
- Phase 1 must not change `PlannerService`, `SolverService`, `GraphBuilder`, `OperationEngine`, graph DTOs, or current API behavior.
- Supported targets are single-layer only.
- Targets containing pin or crystal materials are rejected.
- Colored targets are accepted, but base-demand counting is computed from the uncolored skeleton only.
- Paint demand is explicitly out of scope for this phase.

## Domain Interface

```python
@dataclass(frozen=True, slots=True)
class BaseDemand:
    base_shape_code: str
    quadrants_per_target: int
    total_quadrants: int
    full_source_count: int


class UnsupportedFactoryDemandError(Exception):
    ...


def compute_base_demands(target: Shape, target_count: int) -> tuple[BaseDemand, ...]:
    ...
```

- `target_count` must be greater than or equal to `1`.
- Base demands are grouped by shape kind on the single target layer.
- `base_shape_code` is the uncolored full-source code for that kind, repeated across all four quadrants.
- Return values are sorted by `base_shape_code` for stable tests and serialization.

## Phase Boundaries

### Phase 1

- Add `BaseDemand`, `UnsupportedFactoryDemandError`, and `compute_base_demands`.
- Add focused unit tests in `tests/unit/shapez_solver/test_factory_demand.py`.

### Phase 2

- Add a dedicated Layer 2 planner/service that composes `compute_base_demands(...)` with `PlannerService.solve_shape(...)`.
- Return a result object that pairs `base_demands` with the existing `SolvedRecipe`.

### Phase 3

- Add optional request field `target_count` with default `1`.
- Serialize `base_demands` as a top-level response field.
- Keep `output_lanes` out of the request and response.

### Phase 4

- Revisit graph deduplication with lane-aware or recipe-output-aware node identity.
- Add regression coverage for repeated same-shape source cases before changing graph behavior.

### Phase 5

- Revisit flow operations only after splitter and belt semantics are separately specified.

## Out Of Scope

- Paint consumption or paint source demand.
- Lane-aware graph nodes and throughput graph rendering.
- Flow-operation support in `OperationEngine`.
- Changes to the single-target planner contract.

## References

- `../research/research_shapez2_game_systems_2026-05-01.md`
- `protocols/README.md`
- `AGENTS.md`
