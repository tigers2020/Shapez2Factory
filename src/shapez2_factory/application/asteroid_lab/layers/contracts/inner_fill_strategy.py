"""L4/L5 inner pattern fill strategy selector."""

from __future__ import annotations

from enum import StrEnum


class InnerFillStrategy(StrEnum):
    GREEDY = "greedy"
    TRUNK_FIRST_WEIGHTED_RIPUP = "trunk_first_weighted_ripup"


def parse_inner_fill_strategy(value: str | InnerFillStrategy | None) -> InnerFillStrategy:
    if value is None:
        return InnerFillStrategy.GREEDY
    if isinstance(value, InnerFillStrategy):
        return value
    normalized = value.strip().lower()
    return InnerFillStrategy(normalized)


__all__ = ["InnerFillStrategy", "parse_inner_fill_strategy"]
