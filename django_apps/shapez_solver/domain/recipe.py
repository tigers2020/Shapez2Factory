from __future__ import annotations

from dataclasses import dataclass, field

from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_solver.domain.operations import OperationType


@dataclass(frozen=True, slots=True)
class RecipeCost:
    operations: int
    sources: int
    depth: int
    reused_nodes: int
    unsupported_penalty: int = 0

    def as_sort_key(self) -> tuple[int, int, int, int, int]:
        return (
            self.operations,
            self.sources,
            self.depth,
            -self.reused_nodes,
            self.unsupported_penalty,
        )


@dataclass(frozen=True, slots=True)
class SourceRecipe:
    id: str
    shape: Shape
    label: str = "Source"


@dataclass(frozen=True, slots=True)
class RecipeRef:
    recipe_id: str
    output_index: int
    shape: Shape


@dataclass(frozen=True, slots=True)
class OperationRecipe:
    id: str
    operation_type: OperationType
    inputs: tuple[RecipeRef, ...]
    outputs: tuple[Shape, ...]
    label: str
    description: str
    color: str | None = None


@dataclass(frozen=True, slots=True)
class SolvedRecipe:
    ref: RecipeRef
    recipes: tuple[SourceRecipe | OperationRecipe, ...]
    cost: RecipeCost


@dataclass(slots=True)
class SolveContext:
    memo: dict[str, SolvedRecipe] = field(default_factory=dict)
    visiting: set[str] = field(default_factory=set)
    next_id: int = 1

    def allocate_id(self, prefix: str) -> str:
        value = f"{prefix}-{self.next_id:04d}"
        self.next_id += 1
        return value
