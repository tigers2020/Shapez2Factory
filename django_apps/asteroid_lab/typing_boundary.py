"""Shared typing aliases for Asteroid Lab wire boundaries."""

from __future__ import annotations

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]

# typing_contracts: validated generic JSON object tree (post json.loads narrow)
type RawJsonObject = JsonObject

__all__ = ["JsonObject", "JsonScalar", "JsonValue", "RawJsonObject"]
