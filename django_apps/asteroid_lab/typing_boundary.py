"""Shared typing aliases for Asteroid Lab wire boundaries."""

from __future__ import annotations

from typing import Any

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]

# typing_contracts: raw JSON before normalization only
type RawJsonObject = dict[str, Any]

__all__ = ["JsonScalar", "JsonValue", "RawJsonObject"]
