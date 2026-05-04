from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InventoryState:
    """Batch search에서 사용하는 hashable inventory 상태."""

    counts: tuple[tuple[str, int], ...]

    @classmethod
    def from_counts(cls, counts: Mapping[str, int]) -> InventoryState:
        normalized_counts = tuple(
            sorted((shape_code, count) for shape_code, count in counts.items() if count > 0)
        )
        return cls(counts=normalized_counts)

    def to_dict(self) -> dict[str, int]:
        return dict(self.counts)

    def count(self, shape_code: str) -> int:
        return self.to_dict().get(shape_code, 0)

    def can_consume(self, shape_codes: tuple[str, ...]) -> bool:
        available_counts = self.to_dict()
        for shape_code in shape_codes:
            next_count = available_counts.get(shape_code, 0) - 1
            if next_count < 0:
                return False
            available_counts[shape_code] = next_count
        return True

    def consume_and_produce(
        self,
        inputs: tuple[str, ...],
        outputs: tuple[str, ...],
    ) -> InventoryState:
        next_counts = self.to_dict()
        for shape_code in inputs:
            next_counts[shape_code] = next_counts.get(shape_code, 0) - 1
        for shape_code in outputs:
            next_counts[shape_code] = next_counts.get(shape_code, 0) + 1
        return InventoryState.from_counts(next_counts)
