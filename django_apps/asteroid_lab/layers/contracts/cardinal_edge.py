"""Cardinal edge buckets for exterior connector placement."""

from enum import StrEnum


class CardinalEdge(StrEnum):
    NORTH = "north"
    EAST = "east"
    SOUTH = "south"
    WEST = "west"


__all__ = ["CardinalEdge"]
