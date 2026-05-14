"""JSON-safe projection for HTTP / behavior artifacts (serialization layer only).

Domain DTOs and placement code must not depend on this module as algorithm input.
Call sites: views, copy-preview sidecars, behavior artifact builders.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any


def to_jsonable(obj: Any) -> Any:
    """Recursively convert dataclasses, enums, ``Coord``/``BBox``, sets to JSON-friendly data."""

    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, frozenset):
        return [to_jsonable(x) for x in sorted(obj, key=lambda x: _sort_key(x))]
    if isinstance(obj, tuple):
        return [to_jsonable(x) for x in obj]
    if isinstance(obj, list):
        return [to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if is_dataclass(obj):
        return {f.name: to_jsonable(getattr(obj, f.name)) for f in fields(obj)}
    msg = f"unsupported type for JSON view: {type(obj)!r}"
    raise TypeError(msg)


def _sort_key(x: Any) -> tuple[int, int, str]:
    if hasattr(x, "x") and hasattr(x, "y"):
        return (int(x.x), int(x.y), "")  # Coord
    if isinstance(x, tuple) and len(x) == 2 and all(isinstance(i, int) for i in x):
        return (int(x[0]), int(x[1]), "")
    return (0, 0, str(x))


def existing_layout_analysis_to_json(analysis: Any) -> dict[str, Any]:
    """Serialize ``ExistingLayoutAnalysis`` for HTTP JSON.

    Top-level keys are prefixed with ``existing_layout_`` so payloads never collide with
    STEP 9 ``FinalValidationReport`` field names (``geometry_ok``, etc.).
    """

    out = to_jsonable(analysis)
    if not isinstance(out, dict):
        msg = "expected dict root from analysis serialization"
        raise TypeError(msg)
    return {f"existing_layout_{k}": v for k, v in out.items()}


__all__ = ["existing_layout_analysis_to_json", "to_jsonable"]
