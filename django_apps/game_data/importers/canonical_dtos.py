"""Lightweight DTOs for importer validation (expanded as handlers grow)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShapeRecipeDTO:
    operation_uid: int
    shape_hash: str
    layer_count: int
