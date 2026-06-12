"""Transport kind enum for lab adapters (not solver runtime)."""

from __future__ import annotations

from enum import StrEnum


class TransportKind(StrEnum):
    NONE = "none"
    SPACE_BELT = "space_belt"
    SPACE_PIPE = "space_pipe"


__all__ = ["TransportKind"]
