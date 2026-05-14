"""STEP 0 decoded blueprint handle — pure domain; no I/O, Django, serialization, runtime."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True, slots=True)
class DecodedBlueprintDocument:
    """Immutable handle to STEP 0 decoded JSON (shallow read-only view via ``MappingProxyType``)."""

    _root: dict[str, Any]

    @property
    def document(self) -> Mapping[str, Any]:
        return MappingProxyType(self._root)

    def as_mutable_dict(self) -> dict[str, Any]:
        """Shallow copy for callers that need a mutable ``dict``."""

        return dict(self._root)


__all__ = ["DecodedBlueprintDocument"]
