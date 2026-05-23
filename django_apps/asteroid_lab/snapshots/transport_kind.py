"""Transport kind enum for lab adapters (not solver runtime)."""

from __future__ import annotations

from enum import StrEnum


class TransportKind(StrEnum):
    NONE = "none"
    SHAPE_BELT = "shape_belt"
    FLUID_PIPE = "fluid_pipe"


__all__ = ["TransportKind"]
