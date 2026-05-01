from typing import Protocol

from django_apps.shapez_core.domain.shape import ShapeCode


class Operation(Protocol):
    name: str
    input_count: int
    output_count: int

    def apply(self, inputs: tuple[ShapeCode, ...]) -> tuple[ShapeCode, ...]:
        """Apply this operation to one or more input shapes."""
